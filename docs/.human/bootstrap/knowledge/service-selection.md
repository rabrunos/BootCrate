# External services and hosting discovery

Decide capabilities before vendors. This is a research/decision guide, not authorization to buy, provision, change DNS/firewalls or deploy.

## Owner questions

Ask only relevant questions in plain language. Existing intake free text plus the discovery conversation can supply these until the questionnaire is redesigned.

- What must be online: sync, login, scores, files, email, scheduled automation or payments?
- Is the priority lower cash cost, less maintenance, more control, portability, or a balance?
- What infrastructure/skills already exist? Who will patch, monitor, restore and respond to incidents?
- What is an acceptable monthly budget and spending ceiling? What is the expected starting workload and plausible growth?
- How much downtime/data loss is tolerable? Are geography, personal-data or licensing restrictions material?
- Is managed, self-hosted or hybrid operation acceptable? How important is export/migration away from a provider?

Do not ask a novice to choose database brands, TLS algorithms or queue products without explaining the actual need.

## Capability-first comparison

Candidate capabilities include compute, persistence, authentication, storage, realtime, queues/jobs, automation, email, observability, payments, backups and content delivery. Do not create every category. Start with the smallest architecture that meets the requirements; one suitable database often beats several unnecessary systems.

Compare no external service, managed, self-hosted and hybrid options as applicable. Research current primary documentation for price/quota, egress, licensing/SaaS use, region, backups, security responsibility, portability and failure behavior. Never hard-code a provider or promise free/unlimited usage. Self-hosted software still costs operation, recovery, security work and finite capacity.

Record the selected capability/provider, rationale, operator, security obligations, cost ceiling and exit strategy in stable project context. Work/status remains in Issues. Materialize only necessary clients/config/scripts; do not add MCP or a vendor framework solely to make the catalog complete.

## Release boundary

Before real deployment: verify data/service access controls, non-public management interfaces, secret provisioning, restore/rollback, monitoring, quotas and the owner's explicit approval. A managed provider does not eliminate these obligations.

## Example: online leaderboard

Resolve identity, authorized score submission, ranking queries, abuse limits, capacity, recovery and privacy first. Only then compare a lightweight API/database against a managed backend. A client write key is not a trustworthy score-validation mechanism.
