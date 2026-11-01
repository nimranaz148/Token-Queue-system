import json
import uuid
from unittest.mock import AsyncMock

import pytest

from app.ai.guardrails import redact_pii_text
from app.ai.types import CallerIdentity, ToolContext
from app.ai.workflow import AgentWorkflowManager


@pytest.fixture
def workflow_manager() -> AgentWorkflowManager:
    return AgentWorkflowManager()


def test_redact_pii_text_replaces_identifying_information() -> None:
    text = (
        "Patient Muhammad contacted us from 03001234567 and email patient.test@example.com. "
        "CNIC is 35202-9876543-1. Please follow up."
    )
    redacted = redact_pii_text(text)
    assert "03001234567" not in redacted
    assert "patient.test@example.com" not in redacted
    assert "35202-9876543-1" not in redacted
    assert "[PHONE_REDACTED]" in redacted
    assert "[EMAIL_REDACTED]" in redacted
    assert "[CNIC_REDACTED]" in redacted


@pytest.mark.asyncio
async def test_trace_contains_no_personal_data_from_fixtures(
    workflow_manager: AgentWorkflowManager,
) -> None:
    """Acceptance criterion for Task 45:

    A trace of a run contains no personal data from the test fixtures.
    """
    run_id = uuid.uuid4()
    approver_id = uuid.uuid4()
    clinic_id = uuid.uuid4()
    token_id = str(uuid.uuid4())

    # Raw test fixtures containing sensitive personal and health data
    fixture_full_name = "Muhammad Usman Tariq"
    fixture_phone = "+92 300 1234567"
    fixture_email = "usman.tariq@gmail.com"
    fixture_cnic = "35201-1234567-1"
    fixture_medical_notes = "Patient diagnosed with Type-2 diabetes and acute hypertension. Prescribed Metformin 500mg BD."

    mock_service = AsyncMock()
    mock_service.save_wait_prediction.return_value = {
        "token_id": token_id,
        "patient_name": fixture_full_name,
        "phone": fixture_phone,
        "email": fixture_email,
        "notes": fixture_medical_notes,
    }

    authorized_context = ToolContext(
        caller=CallerIdentity(
            user_id=uuid.uuid4(),
            role="system_job",
            clinic_id=clinic_id,
        )
    )

    # 1. Propose action containing PII in arguments and reason
    action = workflow_manager.propose_action(
        run_id=run_id,
        agent_name="Wait Predictor",
        tool_name="save_wait_prediction",
        arguments={
            "token_id": token_id,
            "clinic_id": str(clinic_id),
            "predicted_minutes": 30,
            "model_version": "v1.0.0",
            "patient_name": fixture_full_name,
            "phone": fixture_phone,
            "email": fixture_email,
            "cnic": fixture_cnic,
            "notes": fixture_medical_notes,
        },
        reason="Outlier prediction requiring human review before updating estimate",
    )

    # 2. Approve and run action
    await workflow_manager.approve_and_run(
        action_id=action.action_id,
        approver_id=approver_id,
        context=authorized_context,
        service=mock_service,
    )

    # 3. Retrieve full structured trace
    trace = workflow_manager.get_trace(run_id)
    assert len(trace) >= 2

    trace_json_str = json.dumps(trace)

    # 4. Strict assertions: NO personal data from test fixtures appears in the trace
    assert fixture_full_name not in trace_json_str, (
        f"Full name '{fixture_full_name}' was not redacted from trace"
    )
    assert fixture_phone not in trace_json_str, (
        f"Phone number '{fixture_phone}' was not redacted from trace"
    )
    assert "0300 1234567" not in trace_json_str
    assert "03001234567" not in trace_json_str
    assert fixture_email not in trace_json_str, (
        f"Email address '{fixture_email}' was not redacted from trace"
    )
    assert fixture_cnic not in trace_json_str, f"CNIC '{fixture_cnic}' was not redacted from trace"
    assert "Type-2 diabetes" not in trace_json_str, "Medical diagnosis was not redacted from trace"
    assert "Metformin" not in trace_json_str, "Prescription details were not redacted from trace"

    # Verify that redaction tokens are correctly placed in the trace
    assert "[PHONE_MASKED]" in trace_json_str or "[PHONE_REDACTED]" in trace_json_str
    assert "[EMAIL_MASKED]" in trace_json_str or "[EMAIL_REDACTED]" in trace_json_str
    assert "[CNIC_MASKED]" in trace_json_str or "[CNIC_REDACTED]" in trace_json_str
    assert "[REDACTED_MEDICAL_NOTES]" in trace_json_str
