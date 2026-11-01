import uuid
from decimal import Decimal

from app.ai.guardrails import (
    KillSwitchManager,
    RunCapTracker,
    SpendCapManager,
)


def test_token_run_cap_exceeded_stops_run_with_clear_message() -> None:
    """Acceptance criterion 1a: Exceeding a run cap stops the run with a clear message."""
    tracker = RunCapTracker(token_daily_cap=20)

    # Under cap (e.g. 19 runs)
    allowed, msg = tracker.check_run_cap(current_runs_today=19)
    assert allowed is True
    assert msg is None

    # Reaching or exceeding cap (20 runs)
    blocked, error_message = tracker.check_run_cap(current_runs_today=20)
    assert blocked is False
    assert error_message is not None
    assert "AI_RUN_CAP_EXCEEDED" in error_message
    assert "Daily limit of 20 AI interactions reached for today" in error_message
    assert "Barah-e-karam kal dobara rabta karein" in error_message


def test_clinic_spend_cap_exceeded_stops_run_with_clear_message() -> None:
    """Acceptance criterion 1b: Exceeding a clinic spend cap stops the run with a clear message."""
    manager = SpendCapManager(default_clinic_cap=Decimal("2.00"), global_cap=Decimal("50.00"))
    clinic_id = uuid.uuid4()

    # Under cap: $1.85 spent
    allowed, msg = manager.check_spend(
        clinic_id=clinic_id,
        clinic_month_spend_usd=Decimal("1.85"),
        global_month_spend_usd=Decimal("10.00"),
    )
    assert allowed is True
    assert msg is None

    # Exceeding default cap: $2.05 spent
    blocked, error_message = manager.check_spend(
        clinic_id=clinic_id,
        clinic_month_spend_usd=Decimal("2.05"),
        global_month_spend_usd=Decimal("10.00"),
    )
    assert blocked is False
    assert error_message is not None
    assert "AI_SPEND_CAP_REACHED" in error_message
    assert "Monthly AI spend cap of $2.00 reached for this clinic" in error_message
    assert "AI service is currently unavailable" in error_message

    # Custom clinic cap override (e.g. $5.00)
    manager.set_clinic_cap(clinic_id, Decimal("5.00"))
    allowed_override, _ = manager.check_spend(
        clinic_id=clinic_id,
        clinic_month_spend_usd=Decimal("2.05"),
        global_month_spend_usd=Decimal("10.00"),
    )
    assert allowed_override is True


def test_global_spend_cap_exceeded_stops_run_with_clear_message() -> None:
    """Acceptance criterion 1c: Exceeding the global spend cap stops all runs with a clear message."""
    manager = SpendCapManager(default_clinic_cap=Decimal("2.00"), global_cap=Decimal("50.00"))
    clinic_id = uuid.uuid4()

    blocked, error_message = manager.check_spend(
        clinic_id=clinic_id,
        clinic_month_spend_usd=Decimal("0.50"),
        global_month_spend_usd=Decimal("50.00"),
    )
    assert blocked is False
    assert error_message is not None
    assert "AI_SPEND_CAP_REACHED" in error_message
    assert "Global platform AI monthly budget of $50.00 reached" in error_message


def test_kill_switch_works_without_deploy() -> None:
    """Acceptance criterion 2: The kill switch works without a deploy.

    Proves global, feature-level, and clinic-level kill switches can be toggled
    dynamically at runtime without restarting or redeploying code.
    """
    ks = KillSwitchManager()
    clinic_a = uuid.uuid4()
    clinic_b = uuid.uuid4()

    # Initial state: fully operational
    ok, _ = ks.check_is_operational(feature="patient_chat", clinic_id=clinic_a)
    assert ok is True

    # 1. Activate global kill switch
    ks.activate_global(reason="Emergency maintenance on AI provider keys.")
    blocked_global, reason_global = ks.check_is_operational(
        feature="patient_chat", clinic_id=clinic_a
    )
    assert blocked_global is False
    assert reason_global == "AI_SERVICE_DISABLED: Emergency maintenance on AI provider keys."

    # Deactivate global kill switch
    ks.deactivate_global()
    ok_restored, _ = ks.check_is_operational(feature="patient_chat", clinic_id=clinic_a)
    assert ok_restored is True

    # 2. Feature-specific kill switch without affecting other features
    ks.disable_feature(feature="patient_chat", reason="Spam anomaly detected in chat.")

    # patient_chat is disabled
    chat_blocked, chat_reason = ks.check_is_operational(feature="patient_chat", clinic_id=clinic_a)
    assert chat_blocked is False
    assert chat_reason == "AI_FEATURE_DISABLED: Spam anomaly detected in chat."

    # visit_summarizer continues operating normally
    summarizer_ok, _ = ks.check_is_operational(feature="visit_summarizer", clinic_id=clinic_a)
    assert summarizer_ok is True

    # Re-enable feature
    ks.enable_feature("patient_chat")
    chat_ok, _ = ks.check_is_operational(feature="patient_chat", clinic_id=clinic_a)
    assert chat_ok is True

    # 3. Clinic-specific kill switch without affecting other clinics
    ks.disable_clinic(clinic_id=clinic_a, reason="Clinic suspended due to billing.")

    # Clinic A is disabled
    clinic_a_blocked, clinic_a_reason = ks.check_is_operational(
        feature="daily_brief", clinic_id=clinic_a
    )
    assert clinic_a_blocked is False
    assert clinic_a_reason == "AI_CLINIC_DISABLED: Clinic suspended due to billing."

    # Clinic B is unaffected
    clinic_b_ok, _ = ks.check_is_operational(feature="daily_brief", clinic_id=clinic_b)
    assert clinic_b_ok is True

    # Re-enable Clinic A
    ks.enable_clinic(clinic_id=clinic_a)
    clinic_a_restored, _ = ks.check_is_operational(feature="daily_brief", clinic_id=clinic_a)
    assert clinic_a_restored is True
