import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.ai.tools.executor import execute_tool
from app.ai.types import ToolContext, ToolResult


class ActionApprovalStatus(StrEnum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


@dataclass
class AgentTraceStep:
    timestamp: datetime
    step_type: str  # "PROPOSAL" | "DECISION" | "EXECUTION" | "ABORTED"
    action_id: uuid.UUID
    run_id: uuid.UUID
    details: dict[str, Any]


@dataclass
class ProposedAction:
    action_id: uuid.UUID
    run_id: uuid.UUID
    agent_name: str
    tool_name: str
    arguments: dict[str, Any]
    reason: str
    status: ActionApprovalStatus = ActionApprovalStatus.PENDING_APPROVAL
    decision_by: uuid.UUID | None = None
    decision_reason: str | None = None
    decision_at: datetime | None = None
    execution_result: Any | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AgentWorkflowManager:
    """Manages agent side-effect proposals with human-in-the-loop approval (PRD §36.6 L3 Autonomy).

    Guarantees:
    1. An action marked with side effects cannot run without explicit human approval.
    2. An approved action runs via the tool executor.
    3. A rejected action is strictly aborted without executing tool side effects.
    4. The trace audit log captures every proposal, human decision, and execution event.
    """

    def __init__(self) -> None:
        self._actions: dict[uuid.UUID, ProposedAction] = {}
        self._traces: dict[uuid.UUID, list[AgentTraceStep]] = {}

    def propose_action(
        self,
        run_id: uuid.UUID,
        agent_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        reason: str,
    ) -> ProposedAction:
        """Agent generates an action proposal requiring human approval before side-effect execution."""
        action_id = uuid.uuid4()
        action = ProposedAction(
            action_id=action_id,
            run_id=run_id,
            agent_name=agent_name,
            tool_name=tool_name,
            arguments=arguments,
            reason=reason,
            status=ActionApprovalStatus.PENDING_APPROVAL,
        )
        self._actions[action_id] = action

        # Append proposal event to trace
        if run_id not in self._traces:
            self._traces[run_id] = []

        self._traces[run_id].append(
            AgentTraceStep(
                timestamp=datetime.now(UTC),
                step_type="PROPOSAL",
                action_id=action_id,
                run_id=run_id,
                details={
                    "agent": agent_name,
                    "tool": tool_name,
                    "arguments": arguments,
                    "reason": reason,
                    "status": ActionApprovalStatus.PENDING_APPROVAL.value,
                },
            )
        )
        return action

    async def approve_and_run(
        self,
        action_id: uuid.UUID,
        approver_id: uuid.UUID,
        context: ToolContext,
        service: Any,
    ) -> tuple[ProposedAction, ToolResult]:
        """Human approves the proposed action; tool execution runs immediately and records trace."""
        action = self._actions.get(action_id)
        if not action:
            raise ValueError(f"Action '{action_id}' not found")
        if action.status != ActionApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f"Action '{action_id}' cannot be approved; status is {action.status}")

        now = datetime.now(UTC)
        action.status = ActionApprovalStatus.APPROVED
        action.decision_by = approver_id
        action.decision_at = now

        # Trace approval decision
        self._traces[action.run_id].append(
            AgentTraceStep(
                timestamp=now,
                step_type="DECISION",
                action_id=action_id,
                run_id=action.run_id,
                details={
                    "decision": "APPROVED",
                    "approver_id": str(approver_id),
                },
            )
        )

        # Execute side-effect tool
        tool_result = await execute_tool(
            tool_name=action.tool_name,
            raw_args=action.arguments,
            context=context,
            service=service,
        )

        if tool_result.success:
            action.status = ActionApprovalStatus.EXECUTED
            action.execution_result = tool_result.data
        else:
            action.status = ActionApprovalStatus.FAILED
            action.execution_result = tool_result.error

        # Trace execution outcome
        self._traces[action.run_id].append(
            AgentTraceStep(
                timestamp=datetime.now(UTC),
                step_type="EXECUTION",
                action_id=action_id,
                run_id=action.run_id,
                details={
                    "execution_status": action.status.value,
                    "tool_success": tool_result.success,
                    "error": tool_result.error,
                    "data": tool_result.data,
                },
            )
        )

        return action, tool_result

    def reject_action(
        self,
        action_id: uuid.UUID,
        rejector_id: uuid.UUID,
        reason: str,
    ) -> ProposedAction:
        """Human rejects the proposed action; execution is strictly aborted and recorded in trace."""
        action = self._actions.get(action_id)
        if not action:
            raise ValueError(f"Action '{action_id}' not found")
        if action.status != ActionApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f"Action '{action_id}' cannot be rejected; status is {action.status}")

        now = datetime.now(UTC)
        action.status = ActionApprovalStatus.REJECTED
        action.decision_by = rejector_id
        action.decision_reason = reason
        action.decision_at = now

        # Trace rejection decision
        self._traces[action.run_id].append(
            AgentTraceStep(
                timestamp=now,
                step_type="DECISION",
                action_id=action_id,
                run_id=action.run_id,
                details={
                    "decision": "REJECTED",
                    "rejector_id": str(rejector_id),
                    "reason": reason,
                },
            )
        )

        # Trace aborted execution (proves side-effect did not run)
        self._traces[action.run_id].append(
            AgentTraceStep(
                timestamp=now,
                step_type="ABORTED",
                action_id=action_id,
                run_id=action.run_id,
                details={
                    "execution_status": ActionApprovalStatus.ABORTED.value,
                    "note": "Side-effect tool execution prevented by human rejection",
                },
            )
        )

        return action

    def get_trace(self, run_id: uuid.UUID) -> list[dict[str, Any]]:
        """Retrieve full structured trace for an agent run."""
        steps = self._traces.get(run_id, [])
        return [
            {
                "timestamp": s.timestamp.isoformat(),
                "step_type": s.step_type,
                "action_id": str(s.action_id),
                "run_id": str(s.run_id),
                "details": s.details,
            }
            for s in steps
        ]
