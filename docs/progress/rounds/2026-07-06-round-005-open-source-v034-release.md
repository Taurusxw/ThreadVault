# 2026-07-06 Round 005 - Open Source v0.34.0 Release

## 本轮目标

调用开源发布与规则治理工作流，整理 ThreadVault 当前 `0.34.0` 版本，使其适合公开 GitHub release。

## 背景原因

用户要求发布当前版本。仓库已经是 public，当前重点从“切换可见性”变为：确认许可证、补齐社区/安全文件、排除本地私有产物、记录 release 验收，并验证当前工作树。

## 修改范围

- 发布准备文档与社区文件。
- `.gitignore` 本地产物 guardrails。
- `v0.34.0` release 记录。
- 当前发布树移除旧 DOCX 二进制规划文件。

## 实施步骤

1. 读取 `seer-prepare-open-source-release` 和 `seer-codex-rules` skill。
2. 检查 Git 状态、远端、GitHub 仓库可见性和 licenseInfo。
3. 测量项目规则文档体量，确认无需规则重构。
4. 扫描密钥、私有路径、本地输出目录和 tracked 风险产物。
5. 添加开源社区/安全文件与 ignore guardrails。
6. 建立 `docs/progress/releases/v0.34.0/` release 记录。
7. 运行发布验证并记录结果。

## 关键决策

- 仓库已经是 public，本轮不执行 visibility 切换。
- 保持 MIT License。
- 不添加 CodeQL、issue templates、PR templates、branch protection 或 REUSE headers；这些作为后续 hardening。
- 不重写 Git 历史；旧二进制和历史路径若已存在于历史中，作为残留风险记录。
- 本地输出目录只 ignore，不删除用户本地文件。

## 修改清单

- `.gitignore`
- `.env.example`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `docs/progress/releases/v0.34.0/RELEASE_NOTES.md`
- `docs/progress/releases/v0.34.0/ACCEPTANCE.md`
- `docs/progress/releases/v0.34.0/artifacts/README.md`
- `docs/progress/rounds/2026-07-06-round-005-open-source-v034-release.md`

## 测试与验证

实际验证：

```powershell
threadvault mcp manifest --json
py -3.12 -m ruff check .
py -3.12 -m pytest
git diff --check
```

结果：

- `threadvault mcp manifest --json` 通过，输出 `threadvault_mcp_manifest.v1`，版本为 `0.34.0`。
- `py -3.12 -m ruff check .` 通过。
- `py -3.12 -m pytest` 通过：`421 passed in 76.39s`。
- `git diff --check` 通过；仅出现 Windows 行尾提示。
- `git check-ignore` 确认 `threadvault-ui-output/`、`threadvault-ui-backups/`、`data/`、`exports/`、`backups/`、`.env` 和 `.env.*` 会被忽略。
- 密钥扫描命中项均归类为测试假值、扫描器源码或安全说明文案，没有发现真实凭证。

## 文档更新

- 新增 release notes 和 acceptance。
- 新增开源贡献与安全说明。
- 验证结果已同步到 release acceptance。

## 风险与遗留问题

- 历史 Git commits 可能仍包含旧 DOCX 规划文件；当前发布树移除不等于历史清除。
- 历史 archive 记录中可能保留本机路径作为迁移证据。
- 本地 `threadvault-ui-output/` 和 `threadvault-ui-backups/` 目录保留在用户机器上，但会被 ignore。

## 下一步计划

- 提交并推送当前 release 准备。
- 创建 `v0.34.0` Git tag / GitHub release。

## 状态

completed
