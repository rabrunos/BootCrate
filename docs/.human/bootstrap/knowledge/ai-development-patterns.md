# AI development patterns

ChatGPT remains the abundant discovery/research/planning layer. Executors spend their capacity on local truth, implementation and validation. Small tasks still pass through ChatGPT; contracts get smaller, not less rigorous.

Main is one role with Medium / High / XHigh effort. Apply `docs/.ai/TASK_POLICY.md`: High is the default, Medium requires all quality gates, and XHigh handles deep ambiguity. Effort labels depend on the current model/client. A line in a prompt does not switch a runtime setting.

Use Worker for bounded mechanical execution and Scout for narrow read/search interpretation. Return compact evidence, not raw logs. No recursive agent fan-out or permanent reviewer. Review consequential security changes independently when appropriate.

Spend effort on correct controls and executable negative tests before adding agents, documents or infrastructure. More reasoning cannot authorize deployment, supply missing evidence or guarantee security. Use the same acceptance standard at every effort level.
