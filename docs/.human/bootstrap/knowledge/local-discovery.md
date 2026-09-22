# Local Discovery Heuristics

Local discovery fills the gap between remote planning and executable reality.

It is part of materialization when local facts can change the correct technical baseline. It is not a license for broad exploration on every project.

## Discovery levels

### none

Use when the repository, owner decisions, and remote evidence already determine the implementation path. The executor still performs the local truth gate.

### targeted

Use when a known stack/integration needs local confirmation:

- installed SDK/runtime/compiler/package manager;
- real project/manifest version;
- filesystem paths;
- build/test/run commands;
- browser/engine/IDE tooling;
- external service/client availability;
- exact package/API versions;
- target launch/install/log locations.

### deep

Use only when the implementation depends on evidence that cannot be responsibly inferred remotely:

- unfamiliar native/runtime behavior;
- modding against a locally installed target;
- reverse engineering/decompilation explicitly allowed by the owner;
- engine/resource/package inspection;
- ambiguous binary/assembly/API boundaries;
- difficult local-only failures;
- undocumented or Early Access behavior.

Deep discovery normally maps to E3/Main XHigh, with Worker/Scout used to reduce raw exploration.

## Procedure

1. Inspect branch/HEAD/status/diff and preserve unrelated local work.
2. Identify the smallest local questions that block correct materialization.
3. Prefer official/supported APIs and metadata first.
4. Inspect local manifests, SDKs, binaries, assemblies, resources, logs, or runtime output only as needed.
5. When reverse engineering is authorized, choose a current proven tool appropriate to the target representation. Verify the tool and target format instead of assuming an engine implies one decompiler.
6. Keep bulky/raw evidence under ignored `.local/`.
7. Build deterministic indexes/summaries when raw evidence is large.
8. Separate observation from inference.
9. Promote only stable reusable conclusions into tracked project maps/scripts.
10. If local evidence contradicts an owner-approved assumption or makes the approved path unsafe/impossible, report the conflict instead of silently redesigning the product.

## Domain examples

**Godot/external game:** determine whether relevant behavior lives in GDScript resources, C#/.NET assemblies, GDExtension/native code, an official mod API, or a community loader before choosing extraction/decompilation tooling. Inspect only the needed symbols/resources and keep bulk recovered output local.

**Unity/.NET target:** inspect managed assemblies/metadata and supported extension points before patching. Use current .NET-aware inspection/decompilation tooling when authorized.

**Browser extension:** confirm manifest version, browser targets, dev-load workflow, build pipeline, permissions, and available browser automation before generating scripts.

**Windows/Desktop:** confirm SDK/runtime/toolchain, packaging/installer requirements, platform APIs, signing boundary, and run/debug/diagnostic commands.

**Web/backend:** confirm installed/runtime versions, package manager/lockfile, database/service dependencies, migration commands, and browser/E2E availability.

## Machine-local resource setup

When discovery finds a resource whose location varies by machine, do not promote the discovered absolute path into tracked project files.

Instead, materialize the portable resolver:

1. define what makes a candidate valid (expected executable/manifest/version/signature);
2. decide whether an explicit environment/CLI override is useful;
3. define the ignored persisted local key/path;
4. implement safe platform-specific auto-detection when practical;
5. automatically persist one unambiguous valid candidate when appropriate;
6. require user selection or explicit path for ambiguous/missing candidates;
7. keep interactive setup separate from non-interactive/CI behavior;
8. validate stale configuration and fresh-machine scenarios.

For an installed game, detection may inspect launcher/library metadata (for example Steam library locations) and known platform paths, but should verify the actual target rather than assuming the first matching directory is valid.

## Outputs

Local discovery may justify generating:

- a source/runtime/external-target map;
- a command cookbook;
- target locator/doctor script;
- build/test/run/install/diagnostics helpers;
- compact symbol/resource/API indexes;
- validation smoke scripts;
- environment requirements.

Do not generate any of these merely because they exist in this list.
