# 2026-07-14 Round 001: Hot/Cold Storage And Minimal Backups

Status: completed

## 本轮目标

降低持续增长的 SQLite 热库体积，保留可检索对话核心，减少重复正文，建立冷热归档、垃圾回收和分层备份。

## 背景原因

真实库达到 5,683,245,056 bytes。主要体积来自 compacted replacement history、工具输出、token/status 事件、补丁/MCP 结果、内嵌图片和重复 assistant 正文；单纯 VACUUM 无可回收 freelist。

## 修改范围

- 数据库 schema v8 与导入写入策略。
- 内容寻址冷 blob、透明回读、复制重建、验证与 GC。
- Core/Evidence/Forensic 备份及验证。
- CLI、JSON Schema、文档和测试。
- 真实数据库备份、迁移、切换和增量补入。

## 实施步骤

1. 审计真实库体积分布并确定 Core/Evidence/Forensic 边界。
2. 实现 `storage_policy.py`、`cold_store.py`、`archive_lifecycle.py` 深模块。
3. 接入 import、export、privacy scan、CLI、capabilities 和 schemas。
4. 添加精确重复正文去重、冷引用 GC 和分层备份测试。
5. 创建 schema 7 预迁移快照，复制重建 schema 8，完成验收后原子切换。
6. 增量导入迁移期间变化的会话，创建并验证生产 Core/Evidence 备份。

## 关键决策

- 人类对话核心永远保持热存储；只对精确重复正文去重。
- 大型可逆证据冷存储；低价值遥测只保留哈希存根。
- 迁移不原地修改，验收依赖会话摘要而非文件大小。
- 日常备份默认 Core，完整恢复使用 Evidence，原始 JSONL 完整性使用 Forensic。

## 修改清单

- 新增 schema v8、`cold_blobs` 与事件存储字段。
- 新增 storage audit/rebuild/verify/event/prune/backup/verify-backup。
- 新增 2.2.0 文档、ADR、schemas 和六项存储生命周期测试。

## 测试与验证

- 全量 pytest：286 passed（文档前代码基线）。
- 新增存储测试：6 passed。
- Ruff：changed Python surfaces passed。
- 预迁移：328 sessions / 808,698 events / 8 warnings，integrity ok。
- 重建：计数一致、canonical conversation digest 一致、doctor ok、cold ok。
- 热库：5,683,245,056 -> 1,204,150,272 bytes（增量补入前）。
- 去重：32,683 条重复 agent-message 正文。
- 深度冷校验：增量补入后 85,686 blobs，missing 0，invalid 0。
- 增量导入：340 discovered，19 imported，321 skipped，0 failed。
- 生产 Core/Evidence 备份：数据库、manifest、FTS、SHA-256 和冷 blob 深度验证均通过。

## 文档更新

README、AGENTS、DEVELOPMENT、RULES、ARCHITECTURE、API、DATABASE、KNOWLEDGE_GRAPH、CHANGELOG、TODO、DOC_INDEX、PROGRESS、使用手册、ADR 和本 round。

## 风险与遗留问题

- Core 备份不含大型冷证据；需要完整工具/图片恢复时必须使用 Evidence。
- Forensic 生产副本未额外生成，以避免重复占用数 GB；功能由夹具自动测试覆盖，原始 Codex JSONL 仍保留在用户目录。
- 预迁移 schema 7 快照暂留用于短期回滚，确认稳定后可按保留策略删除。

## 下一步计划

按使用频率定期执行 Core 备份；重要阶段执行 Evidence；偶尔运行 `storage prune` dry-run 与 `storage verify`。
