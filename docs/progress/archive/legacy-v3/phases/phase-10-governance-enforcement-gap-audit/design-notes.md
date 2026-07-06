# v3 Phase 10 Design Notes: Governance Enforcement Gap Audit

## Audit Before Enforcement

This phase produces a gap audit before wiring enforcement into existing commands. That keeps the local-first CLI stable
while giving future enforcement work an explicit checklist.

## Static Inventory

The first inventory is static and hand-curated from the current CLI command surface. This is deliberate: the governance
meaning of a command is a product decision, not merely a function name scan.

## No Behavior Change

All gap records should report current enforcement as disabled. The output is planning evidence, not an enforcement
mechanism.

## Future Use

Later phases can use this inventory to choose which commands get permission preflight and audit append calls first.
Export, restore, delete/retention, and raw transcript access should be highest priority.
