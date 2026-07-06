# 2026-07-06 Round 019 - Native UI Major Release Gate

## 本轮目标

Record the user's release requirement: after the native local UI is fully complete and can replace the browser Web UI, ThreadVault should move to a major package version.

## 背景原因

The native desktop app has become the recommended daily entrypoint, but the full replacement goal is not yet complete. The user explicitly requested a major version update after the local UI is completely done.

## 修改范围

- Added the major-version release gate to README versioning guidance.
- Added the gate to PROGRESS next steps.
- Added a high-priority TODO item.
- Updated changelog and document index.

## 实施步骤

1. Kept the current package version unchanged.
2. Documented that the major version bump happens after native desktop UI completion, not before.
3. Added this round record for traceability.

## 关键决策

- Do not bump to a major version while replacement is still incomplete.
- Treat the major bump as a release gate tied to completed native UI parity and validation.

## 修改清单

- `README.md`
- `docs/PROGRESS.md`
- `docs/TODO.md`
- `docs/CHANGELOG.md`
- `docs/DOC_INDEX.md`

## 测试与验证

Not runtime-affecting. Validation is documentation consistency:

```powershell
rg -n "major version|0.x|round-019-native-ui-major-release-gate" README.md docs
```

## 文档更新

- README versioning guidance
- PROGRESS next steps
- TODO high-priority item
- CHANGELOG note
- DOC_INDEX round entry

## 风险与遗留问题

- The major version bump is intentionally deferred until the native desktop UI is complete.
- Remaining completion criteria still include final parity review, unresolved governance/audit write decisions, and any final desktop QA.

## 下一步计划

- Continue completing native desktop UI parity.
- Prepare a major version release only after completion evidence is strong.

## 状态

completed
