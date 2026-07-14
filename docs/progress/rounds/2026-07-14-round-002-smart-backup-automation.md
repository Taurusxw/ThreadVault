# 2026-07-14 Round 002: Smart Backup Automation

Status: completed

## 本轮目标

把 Core/Evidence/Forensic 的人工选择收口为一个傻瓜式入口，并接入本机每天自动执行，使普通使用者只关心成功、跳过或阻塞结果。

## 背景原因

2.2.0 已具备分层备份和冷热归档，但仍要求用户理解档位、周期、验证和保留策略。该操作容易忘记，也容易因长期累积造成磁盘压力。

## 修改范围

- 新增智能备份决策与自动保留深模块。
- 接入 ArchiveStore、CLI、capabilities、robot guide 和 JSON Schema。
- 更新版本、架构、接口、数据库、规则、使用手册和进度文档。
- 运行专项、全量和真实数据库 dry-run/apply 验收，并安装本地周期任务。

## 实施步骤

1. 以现有分层备份和验证接口为唯一底层实现。
2. 建立逻辑变化指纹、周期优先级、空间预检、互斥锁、创建后验证和自动目录保留。
3. 增加 `threadvault storage auto [--apply] --json` 单一入口。
4. 覆盖首次、每日、每周、每月、无变化、空间不足、保留和 JSON 合同测试。
5. 对真实库执行 dry-run/apply，并注册每天一次的本地 Codex 自动任务。

## 关键决策

- 首次建立 Evidence 基线；之后只执行最高到期且数据有变化的一档。
- 周期为每日 Core、每周 Evidence、累计历史满 30 天后每月 Forensic。
- 新备份验证成功后才能执行保留；保留 Core 3、Evidence 2、Forensic 1。
- 自动删除范围仅限 `storage-backups/auto`，手工备份和实时归档不在范围内。
- 空间预检保留 5 GiB 安全余量；不足时阻止，不静默降级。

## 修改清单

- `src/threadvault/smart_backup.py`
- `src/threadvault/archive_lifecycle.py`
- `src/threadvault/store.py`、`cli.py`、`schemas.py`
- `tests/test_v230_smart_backup.py`
- 2.3.0 相关长期文档、schema 和本 round。

## 测试与验证

- 智能备份 + 存储生命周期专项：11 passed。
- Ruff 专项：passed。
- 全量回归：291 passed。
- Ruff 全项目：passed；`pip check`：No broken requirements found。
- 桌面 smoke：ok；MCP manifest：2.3.0、6 个只读工具；doctor：schema v8、FTS 835,177/835,177。
- 真实库 dry-run/apply：`action=skip`、`reason=fresh_or_unchanged`，正确复用当天已有 Evidence，未重复复制大文件，并写入 `data/storage-backups/auto/last-run.json`。
- Codex 本地自动任务 `ThreadVault 每日智能备份` 已创建并复核，任务 ID `threadvault`，每天 03:15 执行。

## 文档更新

README、DEVELOPMENT、RULES、ARCHITECTURE、API、DATABASE、KNOWLEDGE_GRAPH、CHANGELOG、TODO、DOC_INDEX、PROGRESS、使用手册、ADR 和本 round。

## 风险与遗留问题

- 周期任务依赖本机 Codex 自动任务执行环境可用；错过一次不会破坏状态，下次执行会重新按到期策略判断。
- Forensic 会复制原始 JSONL；空间预检通过后仍可能受到并发磁盘占用影响，失败会明确报告并保留已验证的旧备份。

## 下一步计划

日常只查看自动任务通知或 `data/storage-backups/auto/last-run.json`；仅在 blocked/failed 时人工处理磁盘或路径问题。
