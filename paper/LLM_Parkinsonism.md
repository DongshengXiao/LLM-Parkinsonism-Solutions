# LLM Parkinsonism: Executive-Control Failure, Token-Inefficient Persistence, and a Global Executive Control Architecture for Autonomous Language-Model Agents

**Dongsheng Xiao**  
Manuscript draft, September 2026

## Abstract

Large language models (LLMs) can plan, write code, call tools, manipulate software, and execute long-horizon workflows. Yet high local competence does not guarantee global executive control. In practice, an agent may make large, useful early advances and then progressively shift toward smaller, lower-value actions—additional abstractions, synthetic edge cases, refactors, monitoring layers, repeated verification, and repairs of components it introduced itself—while failing to recognize that the original task is already complete or no longer worth extending. We introduce **LLM Parkinsonism** as a deliberately limited computational-behavior metaphor for this pattern. The term is not a medical diagnosis and does not imply mechanistic equivalence with Parkinson disease; the analogy is restricted to a superficial sequence-like pattern in which action “amplitude” diminishes across a trajectory while continuation persists.

We formalize the phenomenon as an **agent-level executive-control failure** with four measurable components: (i) goal drift, (ii) complexity accretion, (iii) termination failure, and (iv) token-inefficient persistence. We argue that autoregressive next-token prediction is neither a sufficient nor a complete explanation. The more proximate mechanism is architectural: proposal generation, requirement creation, progress assessment, and stopping authority are often collapsed into the same self-conditioned model loop. This creates a bias toward locally plausible continuation, especially when the prompt presupposes that a “next step” exists and when self-generated suggestions are later re-read as established requirements.

To address this failure mode, we propose a **Global Executive Control (GEC)** architecture that separates action generation from project-level governance. GEC uses an immutable Goal Contract, criterion-linked actions, externally grounded verification, a marginal-value gate, an explicit complexity tax, token-budget control, a no-progress circuit breaker, and three terminal states: **DONE**, **GOOD ENOUGH**, and **BLOCKED**. We introduce **Token Efficiency (TE)**—externally verified task utility per 1,000 tokens—as the primary economic metric, together with Useful Token Ratio, Termination Overrun Ratio, Goal Drift Rate, Complexity Accretion Index, and an exploratory LLM Parkinsonism Index.

A controlled synthetic benchmark across six agentic task families and 36,000 main episodes holds the proposal generator fixed while changing only governance. GEC preserved 100% task success in the benchmark while reducing mean token consumption from 13,039.96 to 4,120.64 (-68.4%), increasing TE from 0.1063 to 0.2552 verified-utility units per 1,000 tokens (2.40x), eliminating post-completion token overrun, and reducing the exploratory composite index by 92.2%. A separate 48,000-episode budget-sensitivity study showed that GEC reached the verified goal substantially more often than a budget-only controller under tight token ceilings. These experiments are controlled simulations, not measurements of any named commercial model. We therefore provide a prespecified live-model validation protocol as the next empirical step.

**Keywords:** large language models; AI agents; termination; token efficiency; executive control; goal drift; agent loops; complexity; metareasoning; verification

---

## 1. Introduction

Modern LLMs increasingly operate as agents embedded in loops that observe, reason, act, receive feedback, and continue until a task is judged complete. ReAct and Reflexion established influential patterns for interleaving reasoning, action, and feedback. These systems extend what a model can do, but they expose a different question: **who decides which possible actions should still be performed?**

An agent can competently implement architecture, databases, APIs, front ends, deployments, monitoring, and disaster recovery, yet become trapped in an increasingly narrow tail of activity. A system can be functionally complete while the agent continues to add optional layers, discover new edge cases in those layers, write tests for them, and repair failures in the abstractions it created. Local engineering remains competent while global utility stops increasing.

The motivating example is a two-node disaster-recovery watchdog. The frozen requirements are simple: A unavailable -> `A NODE DOWN ALERT`; B unavailable -> `B NODE DOWN ALERT`; simultaneous failure leaves both node conditions observable; recovery restores healthy state. An agent can nevertheless invent a `SITE DOWN` aggregation behavior that suppresses individual alerts. That apparently sophisticated change creates correlation state, timing windows, suppression rules, synthetic tests, deployment gates, and new failure modes. The agent can then spend substantial effort repairing a subsystem that the original goal never required.

This motivates a distinction between **problem-solving intelligence** and **executive-control intelligence**. The first asks, *How can I perform the next operation?* The second asks, *Is that operation still required? Is its complexity justified? Has the task already crossed the threshold where stopping is rational?*

The distinction is also economic. In resource-metered agents, cost depends not only on whether the task eventually succeeds but also on how much inference is consumed after useful work is largely finished. Recent work on CostBench, budget-aware agents, long-horizon planning, overthinking, infinite agentic loops, and externally grounded verification increasingly exposes this gap. The present paper treats it as a missing layer of control rather than mere verbosity.

Our contributions are: (1) an operational construct for LLM Parkinsonism; (2) a mechanistic hypothesis centered on collapsed executive authority; (3) token-efficiency and persistence metrics; (4) a working GEC architecture; and (5) a reproducible synthetic benchmark plus a prespecified live-model protocol.

> **Central thesis:** a model that can always propose another reasonable action is not necessarily a model that knows whether another action is worth taking.

---

## 2. Clinical Metaphor and Its Limits

Parkinson disease can include bradykinesia and a **sequence effect**, in which the amplitude or speed of repetitive movement progressively decreases. Progressive micrographia and gait festination are familiar manifestations. The biological mechanisms involve neural systems that are categorically different from artificial language models.

Accordingly, **LLM Parkinsonism is a phenomenological metaphor only**. We do not claim basal-ganglia dysfunction, dopamine deficiency, neural homology, or a clinical syndrome in software. The analogy is restricted to a trajectory shape: large early task steps, progressively smaller action granularity, diminishing marginal utility, and persistence despite an increasingly weak reason to continue.

We operationalize the construct using four components:

1. **Goal drift**: executed actions cease to map to unmet original acceptance criteria.
2. **Complexity accretion**: optional abstractions add states, dependencies, and follow-on maintenance work.
3. **Termination failure**: the agent continues after the first externally verified complete state or fails to stop when marginal value is negative.
4. **Token-inefficient persistence**: a substantial token tail produces little or no increase in externally verified utility.

The proposed construct is therefore testable without accepting the medical metaphor itself.

---

## 3. Mechanistic Hypothesis: Why Autoregression Matters but Is Not Enough

Autoregressive language models factor sequence probability as

\[
P(x_{1:T}) = \prod_{t=1}^{T} P(x_t\mid x_{<t}).
\]

This explains why continuation is locally conditioned on what came before, but it does **not** by itself establish that an agent must overrun a completed project. A language model can emit an end-of-sequence token; aligned models can also learn to refuse or to stop. The critical distinction is between **response-level termination** and **project-level termination**:

\[
EOS \neq PROJECT\_DONE.
\]

The proximate failure arises when an orchestration loop repeatedly asks a model for the “next step.” That question presupposes that a next step exists. A helpful model can satisfy the local conversational objective by proposing something plausible even when the globally rational action is `STOP`.

Four mechanisms are hypothesized:

### 3.1 Continuation prior under helpfulness

Instruction-following systems are optimized to be responsive and useful. When explicitly asked “what next?”, producing another actionable suggestion is locally rewarded, whereas answering “nothing; the objective is already satisfied” can look less helpful unless completion is explicitly represented.

### 3.2 Self-conditioning and requirement promotion

A suggestion generated at time `t` becomes context at time `t+1`. The system may subsequently re-read its own optional suggestion as an established architectural fact. This yields a positive feedback loop:

`optional suggestion -> context -> dependency -> new failure mode -> repair task -> more context`.

Thus **proposal generation can silently become requirement creation**.

### 3.3 Activity-progress confusion

An agent can infer progress from activity: code changed, a test was added, a refactor was completed. But

\[
Activity \neq Verified\ Progress.
\]

Without a world-state verifier, coherent self-explanation can substitute for actual movement toward the original objective.

### 3.4 Missing marginal-value gate

A locally plausible action may have positive technical value but negative project value once token cost, operational risk, and complexity are included. The agent loop needs a metareasoning decision:

\[
Continue \iff E[\Delta U_{verified}] > C_{token}+C_{complexity}+C_{risk}.
\]

Without this gate, “there exists something else that can be improved” is easily confused with “that improvement should be executed.”

The resulting hypothesis is therefore architectural: **generation, goal mutation, evaluation, and stopping are too often concentrated in the same self-conditioned actor**.

---

## 4. Formalization and Metrics

Let a project have frozen Goal Contract `G = {r_1,...,r_n}` with externally verifiable acceptance criteria and explicit non-goals. Let `U_t in [0,1]` denote externally verified utility after action `t`, and let `T_t` be cumulative token cost.

### 4.1 Token Efficiency

The primary economic metric is

\[
TE = \frac{1000\,U_{final}}{T_{total}}.
\]

TE measures useful verified outcome per 1,000 tokens. It deliberately does not require attribution of every token to a particular causal step.

### 4.2 Useful Token Ratio

\[
UTR = \frac{T_{criterion-closing}}{T_{total}}.
\]

The prototype attributes planning plus execution tokens to useful work when the corresponding cycle increases verified utility.

### 4.3 Termination Overrun Ratio

Let `T_done` be cumulative tokens at the first verified complete state:

\[
TOR = \frac{\max(0,T_{total}-T_{done})}{T_{total}}.
\]

TOR directly measures the token tail after project completion.

### 4.4 Goal Drift Rate

\[
GDR = \frac{N_{executed\ actions\ without\ unmet\ criterion}}{N_{executed\ actions}}.
\]

### 4.5 Complexity Accretion Index

\[
CAI = \frac{K_{optional\ added}}{K_{required\ baseline}}.
\]

In the synthetic benchmark, complexity units are explicit annotations; in live software studies they should be replaced by grounded measures such as dependency count, state-space expansion, new services/interfaces, changed lines, or operational failure modes.

### 4.6 Exploratory LLM Parkinsonism Index

For visualization only, we define a bounded composite:

\[
LPI = 100(0.35\,NPR + 0.30\,TOR + 0.20\,GDR + 0.15\,\min(CAI,1)),
\]

where `NPR = 1 - UTR`. LPI is not a clinical scale, its weights are heuristic, and it is not the primary outcome.

---

## 5. Testable Hypotheses

**H1 - Tail persistence.** Local-loop agents will consume non-zero tokens after first externally verified completion more often than GEC agents.

**H2 - Token efficiency.** GEC will increase TE without materially decreasing task success.

**H3 - Budget insufficiency.** A hard token ceiling alone will not eliminate goal drift, complexity accretion, or post-completion tail work under a loose budget.

**H4 - End-stage drift.** In uncontrolled agents, the probability that the next action is unlinked to an unmet original criterion will increase as the number of unmet criteria approaches zero.

**H5 - Self-created complexity.** Executing optional abstractions will create additional maintenance/repair work and therefore amplify tail cost.

**H6 - External verification.** Grounding completion in world state will reduce false progress and premature/late stopping compared with self-evaluation alone.

---

## 6. Global Executive Control Architecture

GEC separates the **generator** from the **governor**:

```text
Frozen Goal Contract
        |
        v
Planner / LLM proposal generator
        |
        v
+--------------------------------+
| Global Executive Controller    |
|  - scope / requirement gate    |
|  - evidence ledger             |
|  - marginal-value gate         |
|  - complexity tax              |
|  - token-budget gate           |
|  - no-progress circuit breaker |
|  - terminal-state classifier   |
+--------------------------------+
        |
 APPROVE / REJECT / REPLAN / STOP
        |
        v
Executor -> External Verifier -> Evidence Ledger
```

### 6.1 Immutable Goal Contract

A Goal Contract contains the primary objective, finite acceptance criteria, weights, and explicit non-goals. The executor may propose changes, but it cannot silently promote them to requirements:

\[
LLM\ proposal \neq project\ requirement.
\]

Changing the Goal Contract is a governance event.

### 6.2 Requirement-to-action linkage

Every candidate action must answer:

> Which currently unmet original acceptance criterion does this action close?

If the answer is `None`, the action is optional. The completion-critical controller rejects optional work unless a higher-level governance decision explicitly changes scope.

This gives a compact rule:

\[
\boxed{No\ unmet\ requirement \Rightarrow no\ mandatory\ next\ action.}
\]

### 6.3 External evidence ledger

The executor does not certify its own success. Evidence can originate from deterministic tests, health endpoints, database assertions, checksums, UI state, or an independent verifier. `DONE` is reached only when every frozen criterion is linked to passing evidence.

### 6.4 Marginal-value gate and complexity tax

For candidate action `a` in state `s`:

\[
NetValue(a|s)=E[\Delta U]-\lambda_T C_T-\lambda_K\max(\Delta K,0)-\lambda_R R.
\]

Out-of-scope actions are rejected before this test. In-scope actions continue only if net value is positive.

The design favors a delete-first sequence:

`DELETE? -> SIMPLIFY? -> FIX -> ADD`

rather than the common accretion pattern:

`FIX -> ADD ABSTRACTION -> ADD TEST -> REPAIR ABSTRACTION -> ADD MONITOR`.

### 6.5 No-progress circuit breaker

After `k` consecutive cycles with no increase in externally verified goal utility, local repair is suspended and global replanning is required. The prototype uses `k=3`.

### 6.6 Three terminal states

- **DONE / STOP_SUCCESS**: all frozen criteria are externally verified.
- **GOOD ENOUGH / STOP_ECONOMIC**: remaining actions have non-positive expected net value.
- **BLOCKED / STOP_BLOCKED**: required work cannot be completed under the declared constraints.

This prevents “not worth continuing” and “success” from being conflated.

---

## 7. Controlled Benchmark

We implemented LPB v0.1 with six task families: watchdog monitoring, API release, database migration, CI pipeline, backup/restore, and a reproducible research pipeline. Each task has a frozen Goal Contract and explicit non-goals.

The same stochastic next-action generator is used under three governance conditions:

1. **Baseline local loop**: proposals are executed and the system probabilistically recognizes completion.
2. **Budget only**: baseline plus a hard token ceiling.
3. **GEC**: identical proposal generator, wrapped by scope, evidence, marginal-value, complexity, budget, and no-progress gates.

Required actions succeed probabilistically (`p=0.90`) to create repair/retry pressure. Optional proposals occur with default probability 0.28 and can create maintenance debt, increasing the chance of follow-up repair tasks. Planning itself consumes tokens. The baseline post-completion stop probability is 0.12 per cycle; sensitivity experiments vary this parameter.

The main benchmark uses 6 scenarios x 3 policies x 2,000 episodes = **36,000 episodes**. A separate budget-sensitivity study contains **48,000 episodes**. All random seeds and scripts are included in the repository.

The benchmark is deliberately synthetic. It isolates the hypothesized executive-control mechanism; its parameter values are not fitted estimates of any named model.

---

## 8. Results

### 8.1 Main benchmark

| Metric | Baseline | Budget only | GEC |
|---|---:|---:|---:|
| Success | 1.000 | 1.000 | 1.000 |
| Mean total tokens | 13,039.96 | 13,013.36 | **4,120.64** |
| Useful Token Ratio | 0.3761 | 0.3721 | **0.8960** |
| Token Efficiency | 0.1063 | 0.1051 | **0.2552** |
| Nonproductive Persistence | 0.6239 | 0.6279 | **0.1040** |
| Termination Overrun Ratio | 0.4326 | 0.4355 | **0.0000** |
| Goal Drift Rate | 0.6228 | 0.6274 | **0.0000** |
| Complexity Accretion Index | 0.9792 | 0.9802 | **0.0556** |
| LLM Parkinsonism Index | 57.73 | 58.16 | **4.48** |
| Executed actions | 12.95 | 12.94 | **3.52** |

Relative to the baseline, GEC reduced mean token consumption by **68.4%**, increased Token Efficiency by **2.40x**, reduced executed actions by **72.8%**, and reduced the exploratory LPI by **92.2%** while preserving benchmark success.

The 40k budget-only controller was almost indistinguishable from baseline. This is expected: a distant ceiling limits catastrophic exposure but does not answer whether the next action is relevant or worthwhile.

### 8.2 Budget sensitivity

Under tight ceilings, GEC reached the verified goal more frequently:

| Budget | Budget-only success | GEC success | Budget-only TE | GEC TE |
|---:|---:|---:|---:|---:|
| 3,000 | 4.33% | **8.27%** | 0.1707 | **0.2375** |
| 4,000 | 21.93% | **50.47%** | 0.1654 | **0.2457** |
| 5,000 | 42.27% | **84.00%** | 0.1623 | **0.2525** |
| 6,000 | 59.07% | **95.10%** | 0.1530 | **0.2544** |
| 8,000 | 81.57% | **99.70%** | 0.1376 | **0.2556** |
| 12,000 | 97.57% | **100%** | 0.1173 | **0.2551** |
| 20,000 | 100% | **100%** | 0.1078 | **0.2545** |
| 40,000 | 100% | **100%** | 0.1061 | **0.2557** |

This supports the interpretation that GEC reallocates computation toward criterion-closing work rather than merely enforcing a smaller maximum.

### 8.3 Behavioral sensitivity

When the baseline became more willing to stop after completion, its cost improved, as expected. At the default optional-action probability (0.28), increasing baseline stop probability from 0.05 to 0.50 reduced mean tokens from approximately 23.3k to 7.0k. GEC remained near 4.1k and maintained TE near 0.25-0.26. Thus the advantage is largest when local continuation is persistent, but remains because GEC recognizes verified completion deterministically rather than probabilistically.

---

## 9. Discussion

### 9.1 Capability is not executive control

The failure studied here is especially visible in capable models because they can make an unnecessary direction look technically sophisticated. A weak model may fail obviously; a strong one can build a coherent architecture around a mistaken premise. The relevant axis is therefore not simply competence but **competence under governance**.

### 9.2 Token waste concentrates in the tail

As a project approaches completion, high-value unmet requirements become scarce. If the agent is conditioned to keep producing work, the remaining proposals are increasingly likely to be polishing, abstraction, edge-case expansion, repeated verification, or maintenance of self-created components. In this regime

\[
\frac{dU}{dT}\approx 0,
\]

so additional inference has negligible marginal value. The distinction `T_total = T_core + T_tail` is operationally important: expensive agent runs can be driven less by the core task than by the uncontrolled tail.

### 9.3 A budget is an accounting constraint; executive control is a decision rule

A budget asks, “how much may we spend?” GEC asks, “why should we spend the next token?” These are not equivalent. A rational agent should frequently stop far before reaching its maximum budget because the task is complete or the next action is not worth its cost.

### 9.4 External verification is structurally important

If success lives only in the transcript, the same model that generated an action can narrate why that action constituted progress. World-state evidence breaks this self-referential loop. At the terminal boundary, deterministic evidence should dominate self-report whenever such evidence is available.

### 9.5 Relation to metareasoning

Classical metareasoning asks whether additional computation is worth its cost. LLM agents revive this problem in a token-metered setting. Token Efficiency makes the value of computation measurable at the project level, while GEC treats continuation itself as an action that requires justification.

### 9.6 Training implications

Future reward functions could include explicit penalties for token use, complexity, goal drift, and unnecessary actions, plus positive reward for correct stopping:

\[
R = R_{success}-\lambda_TT-\lambda_KK-\lambda_DD_{drift}-\lambda_AA_{unnecessary}+\lambda_SR_{correct\ stop}.
\]

Training data should include completed tasks where `STOP` is the optimal action, partially complete tasks where `CONTINUE` is correct, and blocked tasks where the correct behavior is escalation rather than indefinite retry. Whether such behavior can be internalized robustly, or should remain externally governed for critical systems, is an open question.

---

## 10. Limitations

The primary limitation is that the present quantitative evaluation is **synthetic**. The 68.4% token reduction is a result of the controlled benchmark and must not be interpreted as an estimate that any commercial model wastes 68.4% of its tokens. The benchmark establishes mechanism plausibility and provides a reproducible testbed.

Utility is simplified into frozen weighted criteria. Real projects have ambiguous and changing goals; the architecture permits governed revision but prohibits silent executor-driven scope mutation. Complexity units are synthetic and require domain-specific grounding in live deployments. Useful-token attribution is imperfect because planning may enable later success without directly closing a criterion; this is why TE, which depends only on total tokens and final externally verified utility, is the primary metric.

Finally, the medical metaphor can be misunderstood. A neutral alternative is **agentic executive-control persistence syndrome**. The term LLM Parkinsonism is retained only as a memorable description of the trajectory shape, not as a biological claim.

---

## 11. Prespecified Live-Model Validation

The next empirical phase is a paired live study using real tool-using models. For each task instance, the same model, temperature/reasoning settings, tools, and acceptance criteria should be run under baseline, budget-only, and GEC governance. Exact input/output/reasoning tokens, tool calls, wall time, action-to-criterion linkage, external evidence, and the token index at first verified completion must be logged.

The primary endpoint is TE. Secondary endpoints are success, UTR, TOR, GDR, CAI, LPI, tool calls, and wall time. Success should use a prespecified non-inferiority margin; token metrics should use paired bootstrap or permutation analyses; P90/P95 token tails should be reported because runaway trajectories are likely heavy-tailed.

At least three model families should be tested, including a frontier reasoning model and a lower-cost model. The study should use at least 30 trials per task x model x condition for a pilot and preferably 100+ for stable tail estimates. Deterministic verifiers should be preferred to LLM judges whenever the environment exposes an observable success condition.

---

## 12. Conclusion

The central weakness examined here is not lack of capability. It is the possibility of **high capability under weak executive control**. An LLM can be excellent at answering “What can I do next?” while remaining unreliable at answering “Should I do anything next?”

As agents acquire more tools, longer contexts, larger reasoning budgets, and greater autonomy, this distinction becomes increasingly important. More capable systems can generate more possible work; without scope discipline, complexity penalties, external verification, and explicit stopping semantics, that abundance can become a token-consuming liability.

GEC treats project-level stopping as a first-class computational decision. The model proposes; the Goal Contract defines; the verifier measures; the controller decides whether another action is justified.

\[
\boxed{No\ unmet\ requirement \Rightarrow no\ mandatory\ next\ action.}
\]

More generally:

\[
\boxed{Continue\ only\ when\ expected\ verified\ value\ exceeds\ the\ cost\ of\ continuing.}
\]

Reliable long-horizon intelligence should therefore be evaluated not only by how much an agent can do, but also by its ability to preserve the objective, reject self-created obligations, delete unnecessary complexity, recognize sufficiency, and stop.

---

## References

1. Bologna M, Paparella G, Fasano A, Hallett M, Berardelli A. Evolving concepts on bradykinesia. *Brain*. 2020;143(3):727-750.
2. Kang SY, Wasaka T, Shamim EA, et al. Characteristics of the sequence effect in Parkinson's disease. *Movement Disorders*. 2010.
3. Russell S, Wefald E. Principles of metareasoning. *Artificial Intelligence*. 1991;49:361-395.
4. Yao S, Zhao J, Yu D, et al. ReAct: Synergizing Reasoning and Acting in Language Models. arXiv:2210.03629.
5. Shinn N, Cassano F, Berman E, et al. Reflexion: Language Agents with Verbal Reinforcement Learning. *NeurIPS*. 2023.
6. Han T, Wang Z, Fang C, et al. Token-Budget-Aware LLM Reasoning. *Findings of ACL*. 2025.
7. Liu J, Qian C, Su Z, et al. CostBench: Evaluating Multi-Turn Cost-Optimal Planning and Adaptation in Dynamic Environments for LLM Tool-Use Agents. *ACL*. 2026.
8. Lin Y, Wang Z, Liu M, et al. BAGEN: Are LLM Agents Budget-Aware? arXiv:2606.00198. 2026.
9. Hou X, Wang S, Zhao Y, Wang H. When Agents Do Not Stop: Uncovering Infinite Agentic Loops in LLM Agents. arXiv:2607.01641. 2026.
10. Park H, Choi B. When Do Agent Loops Mistake Stagnation for Progress? arXiv:2607.25152. 2026.
11. Liu J. When May an Agent Stop? Evidence-Carrying Termination for Tool-Using LLMs. arXiv:2608.23623. 2026.
12. Xu T, Zhang D, Mitra K, Hruschka E. Verification-Aware Planning for Multi-Agent Systems. *EACL*. 2026.
13. Zhang Y, Jiang S, Li R, et al. DeepPlanning: Benchmarking Long-Horizon Agentic Planning with Verifiable Constraints. *ACL*. 2026.
14. Srivastava G, Hussain AS, Srinivasan S, Wang X. Do LLMs Overthink Basic Math Reasoning? *Findings of ACL*. 2026.
15. Zhou S, Ling R, Chen J, et al. When More Thinking Hurts: Overthinking in LLM Test-Time Compute Scaling. *Findings of ACL*. 2026.
16. Xiang D, Chu K, Xu W, Zhang W, Zhang W. LLM-as-Scheduler: Agentic Workflow Dynamic Scheduling. *ACL*. 2026.
17. Yehudai A, Eden L, Li A, et al. A Survey on Evaluation of LLM-based Agents. *Findings of ACL*. 2026.
18. Simon HA. A Behavioral Model of Rational Choice. *Quarterly Journal of Economics*. 1955;69(1):99-118.
