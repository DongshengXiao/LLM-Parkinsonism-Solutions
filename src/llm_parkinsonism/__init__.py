"""LLM Parkinsonism: executive-control and token-efficiency research prototype."""

from .controller import ControllerConfig, GlobalExecutiveController
from .metrics import EpisodeMetrics, compute_metrics
from .models import AcceptanceCriterion, ActionProposal, GoalContract, TaskState

__all__ = [
    "AcceptanceCriterion",
    "ActionProposal",
    "ControllerConfig",
    "EpisodeMetrics",
    "GlobalExecutiveController",
    "GoalContract",
    "TaskState",
    "compute_metrics",
]

__version__ = "0.1.0"
