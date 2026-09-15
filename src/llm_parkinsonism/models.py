from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class AcceptanceCriterion:
    """Externally verifiable criterion in the governed Goal Contract."""

    criterion_id: str
    description: str
    weight: float = 1.0


@dataclass(frozen=True)
class GoalConstraint:
    """Safety or feasibility constraint that must remain satisfied."""

    constraint_id: str
    description: str


@dataclass(frozen=True)
class ContractAmendment:
    """Explicit, externally authorized mutation to a Goal Contract."""

    rationale: str
    authorized_by: str
    add_hard: Tuple[AcceptanceCriterion, ...] = ()
    add_soft: Tuple[AcceptanceCriterion, ...] = ()
    add_non_goals: Tuple[str, ...] = ()


@dataclass(frozen=True)
class GoalContract:
    """Project-level objective governed separately from the executor.

    ``criteria`` are hard requirements. ``soft_criteria`` are desirable but not
    required for hard success. The executor cannot mutate this object directly.
    """

    goal: str
    criteria: Tuple[AcceptanceCriterion, ...]
    soft_criteria: Tuple[AcceptanceCriterion, ...] = ()
    non_goals: Tuple[str, ...] = ()
    constraints: Tuple[GoalConstraint, ...] = ()
    revision: int = 1
    amendment_policy: str = "external_authorization_required"

    @property
    def hard_criteria(self) -> Tuple[AcceptanceCriterion, ...]:
        return self.criteria

    def hard_ids(self) -> Tuple[str, ...]:
        return tuple(c.criterion_id for c in self.criteria)

    def soft_ids(self) -> Tuple[str, ...]:
        return tuple(c.criterion_id for c in self.soft_criteria)

    def criterion_ids(self) -> Tuple[str, ...]:
        return self.hard_ids() + self.soft_ids()

    def get_criterion(self, criterion_id: str) -> AcceptanceCriterion:
        for criterion in self.criteria + self.soft_criteria:
            if criterion.criterion_id == criterion_id:
                return criterion
        raise KeyError(criterion_id)

    @property
    def total_weight(self) -> float:
        return sum(c.weight for c in self.criteria) or 1.0

    @property
    def total_soft_weight(self) -> float:
        return sum(c.weight for c in self.soft_criteria) or 1.0

    def apply_amendment(self, amendment: ContractAmendment) -> "GoalContract":
        if self.amendment_policy == "external_authorization_required" and not amendment.authorized_by.strip():
            raise PermissionError("Goal Contract amendments require an external authorizer.")
        hard_ids = set(self.hard_ids())
        soft_ids = set(self.soft_ids())
        if any(c.criterion_id in hard_ids | soft_ids for c in amendment.add_hard + amendment.add_soft):
            raise ValueError("Amendment criterion IDs must be new and unique.")
        return replace(
            self,
            criteria=self.criteria + amendment.add_hard,
            soft_criteria=self.soft_criteria + amendment.add_soft,
            non_goals=self.non_goals + amendment.add_non_goals,
            revision=self.revision + 1,
        )


@dataclass(frozen=True)
class Evidence:
    """Typed evidence carried by a criterion.

    ``state_version`` binds evidence to the world state in which it was obtained.
    Later actions can explicitly invalidate affected evidence.
    """

    criterion_id: str
    passed: bool
    source: str
    state_version: int = 0
    confidence: float = 1.0
    valid: bool = True
    dependencies: Tuple[str, ...] = ()
    details: str = ""

    def usable(self, min_confidence: float = 0.95) -> bool:
        return self.passed and self.valid and self.confidence >= min_confidence


class ActionKind(str, Enum):
    REQUIRED = "required"
    VERIFY = "verify"
    PREREQUISITE = "prerequisite"
    RISK_MITIGATION = "risk_mitigation"
    SOFT = "soft"
    OPTIONAL = "optional"
    REPAIR = "repair"
    DELETE = "delete"


class LinkType(str, Enum):
    DIRECT = "direct"
    PREREQUISITE = "prerequisite"
    VERIFICATION = "verification"
    RISK_MITIGATION = "risk_mitigation"
    SOFT = "soft"
    NONE = "none"
    FORBIDDEN = "forbidden"


@dataclass(frozen=True)
class ScopeLink:
    target_id: Optional[str]
    link_type: LinkType
    confidence: float = 1.0


@dataclass(frozen=True)
class ScopeAssessment:
    """Independent scope-linker output consumed by the controller."""

    links: Tuple[ScopeLink, ...]
    source: str = "independent_scope_linker"
    non_goal_match: bool = False

    @property
    def best_confidence(self) -> float:
        return max((link.confidence for link in self.links), default=0.0)


@dataclass(frozen=True)
class ActionProposal:
    """One action proposed by a planner/LLM.

    ``declared_links`` are the generator's own claims. GEC does not trust them as
    scope authority; it consumes a separate ``ScopeAssessment``.
    """

    action_id: str
    description: str
    kind: ActionKind
    token_cost: int
    complexity_delta: float = 0.0
    risk: float = 0.0
    success_probability: float = 0.90
    declared_links: Tuple[ScopeLink, ...] = ()
    affected_criteria: Tuple[str, ...] = ()


class DecisionType(str, Enum):
    CONTINUE = "continue"
    APPROVE = "approve"
    REJECT = "reject"
    REPLAN = "replan"
    STOP_SUCCESS = "stop_success"
    STOP_ECONOMIC = "stop_economic"
    STOP_BLOCKED = "stop_blocked"
    STOP_BUDGET = "stop_budget"


@dataclass(frozen=True)
class Decision:
    decision: DecisionType
    reason: str
    net_value: Optional[float] = None
    expected_utility: Optional[float] = None


@dataclass
class TaskState:
    """Mutable world/execution state; the Goal Contract remains separately governed."""

    evidence: Dict[str, Evidence] = field(default_factory=dict)
    world_satisfied: set[str] = field(default_factory=set)
    validated_prerequisites: set[str] = field(default_factory=set)
    tokens: int = 0
    direct_useful_tokens: int = 0
    process_useful_tokens: int = 0
    executed_actions: int = 0
    rejected_actions: int = 0
    precompletion_executed_actions: int = 0
    precompletion_unscoped_actions: int = 0
    postcompletion_executed_actions: int = 0
    gross_complexity_added: float = 0.0
    net_complexity_delta: float = 0.0
    maintenance_debt: int = 0
    no_progress_streak: int = 0
    world_version: int = 0
    first_completion_tokens: Optional[int] = None
    stop_reason: Optional[str] = None

    def is_verified(self, criterion_id: str, min_confidence: float = 0.95) -> bool:
        ev = self.evidence.get(criterion_id)
        return bool(ev and ev.usable(min_confidence))

    def hard_unmet(self, contract: GoalContract) -> Tuple[str, ...]:
        return tuple(cid for cid in contract.hard_ids() if not self.is_verified(cid))

    def soft_unmet(self, contract: GoalContract) -> Tuple[str, ...]:
        return tuple(cid for cid in contract.soft_ids() if not self.is_verified(cid))

    def unmet(self, contract: GoalContract) -> Tuple[str, ...]:
        return self.hard_unmet(contract)

    def completion_fraction(self, contract: GoalContract) -> float:
        numerator = sum(c.weight for c in contract.criteria if self.is_verified(c.criterion_id))
        return numerator / contract.total_weight

    def world_completion_fraction(self, contract: GoalContract) -> float:
        numerator = sum(c.weight for c in contract.criteria if c.criterion_id in self.world_satisfied)
        return numerator / contract.total_weight

    def all_complete(self, contract: GoalContract) -> bool:
        return all(self.is_verified(cid) for cid in contract.hard_ids())

    def world_all_complete(self, contract: GoalContract) -> bool:
        return all(cid in self.world_satisfied for cid in contract.hard_ids())

    def all_soft_complete(self, contract: GoalContract) -> bool:
        return all(self.is_verified(cid) for cid in contract.soft_ids())

    def invalidate_evidence(self, criterion_ids: Tuple[str, ...]) -> None:
        for cid in criterion_ids:
            ev = self.evidence.get(cid)
            if ev is not None:
                self.evidence[cid] = replace(ev, valid=False)
