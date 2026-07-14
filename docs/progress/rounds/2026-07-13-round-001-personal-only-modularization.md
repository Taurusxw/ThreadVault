# 2026-07-13 Round 001: Personal-Only Modularization

## 本轮目标

删除不需要的团队/共享治理运行时，减轻核心模块，修复治理契约冲突和 `compacted` 解析债务，隔离 Python 环境，并完善只读 MCP 接口。

## 背景原因

项目用于个人本地归档。此前治理状态与共享服务器实现存在冲突，核心文件职责过重；真实数据库有 91 条解析告警，其中 89 条是已知 `compacted` 类型；全局 Python 还混有与项目无关的 Selenium/Trio 依赖问题。

## 修改范围

- 删除 governance/shared server 源码、CLI、配置、桌面面板、Schema 和专属测试。
- 缩减 store/client/desktop/CLI/schema 连接面，拆分 MCP runtime/validation。
- 增加 `compacted` 解析和数据库 v6 兼容迁移。
- 更新版本、项目规则、架构/API/数据库/术语/使用手册和进度文档。
- 清理陈旧 `~hreadvault-*` 元数据并建立 `.venv`。

## 实施步骤

1. 审计活动源码、测试、Schema、文档和真实数据库。
2. 删除团队/治理/共享服务器活动路径，保留个人安全门。
3. 拆分并强化 MCP 的 transport、validation 和 read-only runtime。
4. 支持 `compacted`，以幂等迁移修复既有数据。
5. 重生成 Schema、更新长期文档并运行完整验证。

## 关键决策

- 采用 `docs/adr/0001-personal-only-runtime.md` 的个人专用 2.x 边界。
- 历史 v3/v4 记录保留，不作为活动能力声明。
- MCP 不复用会初始化数据库的写连接，改用只读 URI 与 `query_only`。
- 89 条旧告警仅在事件负载可确认包含字符串 `message` 时迁移和删除；其余告警保留。
- 全局 Selenium/Trio 环境不做扩张性修复，项目验证改用独立 `.venv`。

## 修改清单

- 包版本：`1.0.1` -> `2.0.0`。
- 数据库 Schema：`5` -> `6`。
- 新增：`mcp_runtime.py`、`mcp_validation.py`、个人专用架构测试、v6 迁移测试、ADR。
- 删除：`governance.py`、`shared_server.py`、27 个治理 Schema、27 个治理/团队测试文件。
- 核心体量：`store.py` 约 2,477 -> 1,266 行；`cli.py` 约 3,213 -> 1,927 行；`schemas.py` 约 5,105 -> 1,803 行。

## 测试与验证

- 定向回归：51 passed。
- v6 迁移/解析：4 passed。
- 完整 pytest：`272 passed in 31.06s`。
- 全仓 ruff：通过。
- `.venv pip check`：`No broken requirements found`。
- Desktop smoke：`ok=true`，无需 browser/server/frontend pipeline。
- MCP manifest：6 个工具均声明只读 annotations，协议版本 `2025-06-18`，包版本 `2.0.0`。
- MCP 缺库 smoke：`db_created=false`、错误不泄露目标路径。
- Capabilities：contract `2.0`、Schema v6、major release target `2.0.0`，无 governance 命令或 feature flag。
- 生成 Schema 已重写；活动 `docs/schemas/` 不含 governance artifact。
- 真实数据库：56,680 个 events 与 FTS 行数一致；warnings 91 -> 2，剩余均为 `duplicate_session_meta`。
- 迁移后备份：`.tmp/threadvault-v2-postmigration-backup.db`，`integrity_check=ok`，Schema v6。

## 文档更新

更新 `README.md`、`AGENTS.md`、`CONTEXT.md`、`docs/ARCHITECTURE.md`、`docs/API.md`、`docs/DATABASE.md`、`docs/MCP_INTEGRATION.md`、`docs/KNOWLEDGE_GRAPH.md`、`docs/RULES.md`、`docs/DEVELOPMENT.md`、`docs/CHANGELOG.md`、`docs/TODO.md`、`docs/PROGRESS.md`、`docs/DOC_INDEX.md` 和中文使用手册。

## 风险与遗留问题

- 正常 CLI `doctor` 会先初始化/迁移数据库；本轮首次真实库迁移因此早于备份命令。迁移后备份已校验，但没有迁移前副本。
- 全局 Python 的 Selenium/Trio/WSProto 仍报告 8 个缺失传递依赖，必须使用项目 `.venv` 验证；陈旧 `~hreadvault-*` 目录已为 0。
- 官方 MCP Inspector 外部客户端 smoke 仍是低优先级发布增强，不影响当前只读协议测试。

## 下一步计划

- 只在明确的新产品决策下重新评估团队/共享能力。
- 未来发布门可增加官方 MCP Inspector smoke。

## 状态

completed
