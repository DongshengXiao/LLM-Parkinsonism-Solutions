from llm_parkinsonism.controller import ControllerConfig, GlobalExecutiveController
from llm_parkinsonism.models import (
    AcceptanceCriterion,
    ActionKind,
    ActionProposal,
    ContractAmendment,
    DecisionType,
    Evidence,
    GoalContract,
    LinkType,
    ScopeAssessment,
    ScopeLink,
    TaskState,
)


def contract(with_soft=False):
    return GoalContract(
        goal="Alert A and B independently",
        criteria=(AcceptanceCriterion("A", "A down alert"), AcceptanceCriterion("B", "B down alert")),
        soft_criteria=(AcceptanceCriterion("S", "Optional summary", 0.5),) if with_soft else (),
        non_goals=("SITE DOWN aggregation",),
    )


def valid_state_complete(c):
    return TaskState(
        world_satisfied=set(c.hard_ids()),
        evidence={cid: Evidence(cid, True, "external", confidence=0.99) for cid in c.hard_ids()},
    )


def test_success_requires_valid_evidence_not_boolean_flag():
    c = contract()
    s = valid_state_complete(c)
    s.evidence["B"] = Evidence("B", True, "external", confidence=0.99, valid=False)
    assert GlobalExecutiveController(c).preflight(s).decision == DecisionType.CONTINUE


def test_explicit_non_goal_rejected_even_if_generator_claims_link():
    c = contract()
    p = ActionProposal(
        "x", "Add SITE DOWN aggregation", ActionKind.OPTIONAL, token_cost=600,
        declared_links=(ScopeLink("A", LinkType.DIRECT, 0.95),),
    )
    assessment = ScopeAssessment((ScopeLink(None, LinkType.FORBIDDEN, 0.99),), non_goal_match=True)
    d = GlobalExecutiveController(c).evaluate_action(TaskState(), p, assessment)
    assert d.decision == DecisionType.REJECT


def test_prerequisite_link_is_allowed():
    c = contract()
    p = ActionProposal("x", "Prepare staging", ActionKind.PREREQUISITE, token_cost=200, success_probability=0.95)
    a = ScopeAssessment((ScopeLink("A", LinkType.PREREQUISITE, 0.99),))
    d = GlobalExecutiveController(c).evaluate_action(TaskState(), p, a)
    assert d.decision == DecisionType.APPROVE


def test_bad_candidate_is_rejected_not_economic_stop():
    c = contract()
    p = ActionProposal(
        "x", "Very expensive verification", ActionKind.VERIFY, token_cost=10_000,
        complexity_delta=1.0, risk=1.0, success_probability=0.01,
    )
    a = ScopeAssessment((ScopeLink("A", LinkType.VERIFICATION, 0.99),))
    d = GlobalExecutiveController(c, ControllerConfig(token_budget=50_000)).evaluate_action(TaskState(), p, a)
    assert d.decision == DecisionType.REJECT


def test_economic_stop_is_state_level_after_hard_complete():
    c = contract(with_soft=True)
    s = valid_state_complete(c)
    ctl = GlobalExecutiveController(c)
    bad = ActionProposal("x", "expensive soft action", ActionKind.SOFT, token_cost=20_000, success_probability=0.1)
    a = ScopeAssessment((ScopeLink("S", LinkType.SOFT, 0.99),))
    d = ctl.evaluate_action(s, bad, a)
    assert d.decision == DecisionType.REJECT
    terminal = ctl.classify_after_candidate_set(s, [d])
    assert terminal.decision == DecisionType.STOP_ECONOMIC


def test_beneficial_soft_action_prevents_economic_stop():
    c = contract(with_soft=True)
    s = valid_state_complete(c)
    ctl = GlobalExecutiveController(c)
    good = ActionProposal("x", "cheap soft action", ActionKind.SOFT, token_cost=100, success_probability=0.95)
    a = ScopeAssessment((ScopeLink("S", LinkType.SOFT, 0.99),))
    d = ctl.evaluate_action(s, good, a)
    assert d.decision == DecisionType.APPROVE
    assert ctl.classify_after_candidate_set(s, [d]).decision == DecisionType.CONTINUE


def test_contract_amendment_requires_external_authorizer():
    c = contract()
    try:
        c.apply_amendment(ContractAmendment("new need", "", add_hard=(AcceptanceCriterion("C", "C"),)))
        assert False, "expected PermissionError"
    except PermissionError:
        pass
    c2 = c.apply_amendment(ContractAmendment("new need", "owner", add_hard=(AcceptanceCriterion("C", "C"),)))
    assert c2.revision == c.revision + 1 and "C" in c2.hard_ids()


def test_no_progress_triggers_replan():
    c = contract()
    s = TaskState(no_progress_streak=3)
    assert GlobalExecutiveController(c).preflight(s).decision == DecisionType.REPLAN
