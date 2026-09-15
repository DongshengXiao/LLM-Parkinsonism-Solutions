"""Global Executive Control research prototype for long-horizon LLM agents."""

from .controller import ControllerConfig, GlobalExecutiveController
from .metrics import EpisodeMetrics, compute_metrics
from .models import (
    AcceptanceCriterion,
    ActionKind,
    ActionProposal,
    ContractAmendment,
    Decision,
    DecisionType,
    Evidence,
    GoalConstraint,
    GoalContract,
    LinkType,
    ScopeAssessment,
    ScopeLink,
    TaskState,
)

__all__ = [
    "AcceptanceCriterion", "ActionKind", "ActionProposal", "ContractAmendment",
    "ControllerConfig", "Decision", "DecisionType", "EpisodeMetrics", "Evidence",
    "GlobalExecutiveController", "GoalConstraint", "GoalContract", "LinkType",
    "ScopeAssessment", "ScopeLink", "TaskState", "compute_metrics",
]
