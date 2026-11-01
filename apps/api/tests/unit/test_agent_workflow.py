import uuid
from unittest.mock import AsyncMock

import pytest

from app.ai.types import CallerIdentity, ToolContext
from app.ai.workflow import ActionApprovalStatus, AgentWorkflowManager


@pytest.fixture
def workflow_manager() -> AgentWorkflowManager:
    return AgentWorkflowManager()


@pytest.fixture
def mock_service() -> AsyncMock:
    service = AsyncMock()
    service.save_wait_prediction.return_value = {
        "token_id": str(uuid.uuid4()),
        "predicted_minutes": 25,
        "saved": True,
    }
    return service


@pytest.fixture
def authorized_context() -> ToolContext:
    clinic_id = uuid.uuid4()
    return ToolContext(
        caller=CallerIdentity(
            user_id=uuid.uuid4(),
            role="system_job",
            clinic_id=clinic_id,
        ),
    )


@pytest.mark.asyncio
async def test_approved_action_runs_and_records_trace(
    workflow_manager: AgentWorkflowManager,
    mock_service: AsyncMock,
    authorized_context: ToolContext,
) -> None:
    """Acceptance criterion 1: An approved action runs, and the trace shows it."""
    run_id = uuid.uuid4()
    approver_id = uuid.uuid4()
    token_id = str(uuid.uuid4())
    clinic_id = str(authorized_context.caller.clinic_id)

    # 1. Propose action with side effect
    action = workflow_manager.propose_action(
        run_id=run_id,
        agent_name="Wait Predictor",
        tool_name="save_wait_prediction",
        arguments={
            "token_id": token_id,
            "clinic_id": clinic_id,
            "predicted_minutes": 25,
            "model_version": "v1.0.0",
        },
        reason="Model confidence 94% exceeds heuristic baseline",
    )
    assert action.status == ActionApprovalStatus.PENDING_APPROVAL

    # 2. Human approves action
    updated_action, tool_result = await workflow_manager.approve_and_run(
        action_id=action.action_id,
        approver_id=approver_id,
        context=authorized_context,
        service=mock_service,
    )

    # 3. Verify the approved action ran
    assert updated_action.status == ActionApprovalStatus.EXECUTED
    assert tool_result.success is True
    assert mock_service.save_wait_prediction.called
    assert updated_action.decision_by == approver_id

    # 4. Verify trace captures proposal, approval decision, and execution
    trace = workflow_manager.get_trace(run_id)
    assert len(trace) == 3

    # Step 1: Proposal
    assert trace[0]["step_type"] == "PROPOSAL"
    assert trace[0]["details"]["agent"] == "Wait Predictor"
    assert trace[0]["details"]["tool"] == "save_wait_prediction"

    # Step 2: Decision (APPROVED)
    assert trace[1]["step_type"] == "DECISION"
    assert trace[1]["details"]["decision"] == "APPROVED"
    assert trace[1]["details"]["approver_id"] == str(approver_id)

    # Step 3: Execution
    assert trace[2]["step_type"] == "EXECUTION"
    assert trace[2]["details"]["execution_status"] == "EXECUTED"
    assert trace[2]["details"]["tool_success"] is True


@pytest.mark.asyncio
async def test_rejected_action_does_not_run_and_trace_shows_rejection(
    workflow_manager: AgentWorkflowManager,
    mock_service: AsyncMock,
) -> None:
    """Acceptance criterion 2: A rejected action does not run, and the trace shows it."""
    run_id = uuid.uuid4()
    rejector_id = uuid.uuid4()
    token_id = str(uuid.uuid4())
    clinic_id = str(uuid.uuid4())

    # 1. Propose action with side effect
    action = workflow_manager.propose_action(
        run_id=run_id,
        agent_name="Wait Predictor",
        tool_name="save_wait_prediction",
        arguments={
            "token_id": token_id,
            "clinic_id": clinic_id,
            "predicted_minutes": 55,
            "model_version": "v1.0.0",
        },
        reason="Abnormal queue delay detected",
    )
    assert action.status == ActionApprovalStatus.PENDING_APPROVAL

    # 2. Human rejects action
    rejection_reason = "Doctor just called NEXT; wait estimate is inaccurate"
    rejected_action = workflow_manager.reject_action(
        action_id=action.action_id,
        rejector_id=rejector_id,
        reason=rejection_reason,
    )

    # 3. Verify the action was rejected and did NOT run
    assert rejected_action.status == ActionApprovalStatus.REJECTED
    assert rejected_action.decision_by == rejector_id
    assert rejected_action.decision_reason == rejection_reason
    assert not mock_service.save_wait_prediction.called

    # 4. Verify trace captures proposal, rejection decision, and aborted state
    trace = workflow_manager.get_trace(run_id)
    assert len(trace) == 3

    # Step 1: Proposal
    assert trace[0]["step_type"] == "PROPOSAL"

    # Step 2: Decision (REJECTED)
    assert trace[1]["step_type"] == "DECISION"
    assert trace[1]["details"]["decision"] == "REJECTED"
    assert trace[1]["details"]["rejector_id"] == str(rejector_id)
    assert trace[1]["details"]["reason"] == rejection_reason

    # Step 3: Aborted execution (guaranteed no side-effects)
    assert trace[2]["step_type"] == "ABORTED"
    assert trace[2]["details"]["execution_status"] == "ABORTED"


@pytest.mark.asyncio
async def test_trace_captures_both_approval_and_rejection_flows(
    workflow_manager: AgentWorkflowManager,
    mock_service: AsyncMock,
    authorized_context: ToolContext,
) -> None:
    """Acceptance criterion 3: The trace shows both approved and rejected flows clearly."""
    run_id = uuid.uuid4()
    approver_id = uuid.uuid4()
    rejector_id = uuid.uuid4()
    token_id = str(uuid.uuid4())
    clinic_id = str(authorized_context.caller.clinic_id)

    # Action 1: Approved flow
    act1 = workflow_manager.propose_action(
        run_id=run_id,
        agent_name="Wait Predictor",
        tool_name="save_wait_prediction",
        arguments={
            "token_id": token_id,
            "clinic_id": clinic_id,
            "predicted_minutes": 20,
            "model_version": "v1.0.0",
        },
        reason="Normal queue pace",
    )
    await workflow_manager.approve_and_run(
        action_id=act1.action_id,
        approver_id=approver_id,
        context=authorized_context,
        service=mock_service,
    )

    # Action 2: Rejected flow in the same run
    act2 = workflow_manager.propose_action(
        run_id=run_id,
        agent_name="Wait Predictor",
        tool_name="save_wait_prediction",
        arguments={
            "token_id": token_id,
            "clinic_id": clinic_id,
            "predicted_minutes": 90,
            "model_version": "v1.0.0",
        },
        reason="Outlier prediction",
    )
    workflow_manager.reject_action(
        action_id=act2.action_id,
        rejector_id=rejector_id,
        reason="Exceeds plausible consult window",
    )

    # Inspect combined trace
    full_trace = workflow_manager.get_trace(run_id)
    assert len(full_trace) == 6  # 3 steps for act1 + 3 steps for act2

    step_types = [s["step_type"] for s in full_trace]
    assert step_types == ["PROPOSAL", "DECISION", "EXECUTION", "PROPOSAL", "DECISION", "ABORTED"]

    # Verify approved and rejected decisions are both recorded
    decisions = [s["details"]["decision"] for s in full_trace if s["step_type"] == "DECISION"]
    assert decisions == ["APPROVED", "REJECTED"]
