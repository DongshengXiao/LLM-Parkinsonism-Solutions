from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class AcceptanceCriterion:
    """A frozen, externally verifiable requirement in the original goal contract."""

    criterion_id: str
    description: str
    weight: float = 1.0


@dataclass(frozen=True)
class GoalContract:
    """Immutable project-level objective used by the executive controller."""

    goal: str
    criteria: Tuple[AcceptanceCriterion, ...]
    non_goals: Tuple[str, ...] = ()

    def criterion_ids(self) -> Tuple[str, ...]:
        return tuple(c.criterion_id for c in self.criteria)

    @property
    def total_weight(self) -> float:
        return sum(c.weight for c in self.criteria) or 1.0


@dataclass(frozen=True)
class Evidence:
    """Externally grounded evidence associated with one acceptance criterion."""

    criterion_id: str
    passed: bool
    source: str
    details: str = ""


class ActionKind(str, Enum):
    REQUIRED = "required"
    VERIFY = "verify"
    OPTIONAL = "optional"
    REPAIR = "repair"
    DELETE = "delete"


@dataclass(frozen=True)
class ActionProposal:
    """One candidate action emitted by a planner/executor."""

    action_id: str
    description: str
    kind: ActionKind
    target_criterion: Optional[str]
    expected_utility: float
    token_cost: int
    complexity_delta: float = 0.0
    risk: float = 0.0


class DecisionType(str, Enum):
    CONTINUE = "continue"
    APPROVE = "approve"
    REJECT = "reject"
    REPLAN = "replan"
    STOP_SUCCESS = "stop_success"
    STOP_ECONOMIC = "stop_economic"
    STOP_BLOCKED = "stop_blocked"


@dataclass(frozen=True)
class Decision:
    decision: DecisionType
    reason: str
    net_value: Optional[float] = None


@dataclass
class TaskState:
    """Mutable execution state; the goal contract itself remains frozen."""

    verified: Dict[str, bool] = field(default_factory=dict)
    evidence: Dict[str, Evidence] = field(default_factory=dict)
    tokens: int = 0
    useful_tokens: int = 0
    executed_actions: int = 0
    rejected_actions: int = 0
    unscoped_executed_actions: int = 0
    complexity_added: float = 0.0
    maintenance_debt: int = 0
    no_progress_streak: int = 0
    first_completion_tokens: Optional[int] = None
    stop_reason: Optional[str] = None

    def is_verified(self, criterion_id: str) -> bool:
        return bool(self.verified.get(criterion_id, False))

    def unmet(self, contract: GoalContract) -> Tuple[str, ...]:
        return tuple(cid for cid in contract.criterion_ids() if not self.is_verified(cid))

    def completion_fraction(self, contract: GoalContract) -> float:
        numerator = sum(
            criterion.weight
            for criterion in contract.criteria
            if self.is_verified(criterion.criterion_id)
        )
        return numerator / contract.total_weight

    def all_complete(self, contract: GoalContract) -> bool:
        return all(self.is_verified(cid) for cid in contract.criterion_ids())
