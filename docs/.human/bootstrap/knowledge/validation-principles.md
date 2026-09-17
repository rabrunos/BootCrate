# Validation Principles

Prefer, in order when applicable:
1. deterministic static/schema checks;
2. compile/typecheck/build;
3. focused automated tests;
4. broader integration checks;
5. controlled runtime smoke;
6. graphical/manual owner smoke when automation cannot prove behavior.

Never claim an unexecuted/unobserved check passed.
A failing required check blocks completion until fixed or explicitly re-scoped.
External publishing is not validation.
