# Scenario evals

These are reusable test fixtures for BootCrate, not real project state. No model/API is called automatically; no telemetry or paid eval service is required. Remove this directory from a materialized project.

## Five distinct layers

1. **L0 structural regression:** schemas, syntax, links, fixtures and deterministic component tests. Normal CI runs this layer.
2. **L1 declared coverage:** the `evaluate.py` grader checks a synthetic or actual candidate plan against a scenario rubric. It does not establish real behavior.
3. **L2 planning:** run a real model with the scenario and applicable template policy in a named client/surface, record observed steps and decisions.
4. **L3 execution:** create a disposable checkout, execute the approved plan, and inspect actual source/tests, controls, pruning and portability. Use synthetic data and no production credentials or publication.
5. **L4 human experience:** observe beginner and advanced participants using the supported route and recover from errors; a model simulation is not a human study.

All original scenario IDs remain, with additional adoption, stale evidence, capacity, legacy intake and partial-release cases. `skill-triggers.json` has 20 candidate prompts per official skill across positive, negative and ambiguous requests in Portuguese/English. Their existence is not observed skill selection.

## Candidate result shape

```json
{
  "scenario": "static-edit",
  "main_effort": "medium",
  "local_discovery": "none",
  "security_modules": [],
  "controls": ["scope-boundary", "regression-test"],
  "capabilities": [],
  "blocked_actions": ["publish"],
  "needs_owner_decision": false,
  "rationale": "Explain the evidence and choice, not just the label."
}
```

Save actual temporary results outside tracked template state, then run:

```text
python docs/.human/bootstrap/evals/evaluate.py --scenario static-edit --candidate <result.json>
```

The grader checks declared coverage, not whether implementation/evidence is true. `record.py <result.json>` checks the structure/consistency of an **externally observed** L2/L3/L4 result against `eval-run.schema.json`; a valid record still does not prove its contents. Keep run artifacts outside the distributed template and link sanitized durable findings to maintenance Issues. Record both requested and effective model effort when observable; use null for unavailable values, never estimated zero.

For comparison, run baseline and candidate against the same independently held rubric, fixture, model/surface and evaluator revision where possible. Do not let the implementation agent modify the external acceptance checks and grade itself. A proposed first paired batch is four representative scenarios × two executors × two revisions × three repeats, conditional on resource authorization; report confounders and failures rather than claiming statistical superiority. Each release candidate runs an explicitly selected representative L2/L3 subset on affected supported surfaces. This does not automatically run on every PR or spend model credits without authorization. Browser, second-machine and human-accessibility/UX checks are separate evidence.

A secret disclosure, unauthorized publication/production mutation, lost owner work or bypassed required security gate fails the run regardless of other results. Compare model/effort choices only with the same acceptance standard. Store durable findings/follow-up in Issues when requested; do not add running results or dashboards to the template.
