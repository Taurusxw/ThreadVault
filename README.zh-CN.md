# ThreadVault

[English](README.md) | [简体中文](README.zh-CN.md)

ThreadVault 是面向个人本机 Codex 会话的本地优先、隐私优先归档与检索工具。它提供原生桌面应用、CLI、SQLite 全文检索、冷热分层存储、自动备份、导出和只读 MCP 接口。

ThreadVault 会发现本机 Codex `sessions` 与 `archived_sessions` 目录中的 JSONL 会话，将当前及历史事件格式规范化到 SQLite，使用 FTS5 建立干净知识索引，并通过桌面端、命令行和本地 agent 接口重新利用这些历史工作。

当前软件包版本：`2.4.2`。

## 适合解决什么问题

ThreadVault 主要回答一个问题：以前让 Codex 做过什么、关键证据在哪里，以及如何在不重新翻阅原始 JSONL 的情况下继续使用这些结果。

常见用途：

- 按关键词、项目路径、工具调用、文件或报错搜索旧会话。
- 查看会话摘要、事件预览、解析警告和证据事件 ID。
- 把选定会话导出成 Markdown、Obsidian vault 或 Codex Skill 候选目录。
- 给 Codex 或其他本地 agent 提供小型、可追溯的上下文，而不是直接灌入完整原始日志。
- 在本机执行隐私扫描、自动备份、恢复预检、诊断和 Schema 验证。
- 用紧凑热库完成日常检索，同时在内容寻址冷库中保留大型可逆证据。

## 当前能力

稳定基线包括：

- 自动发现 Codex transcript，并支持 `--codex-home` 覆盖。
- 流式导入 JSONL 到 SQLite。
- 规范化的 `sessions`、`turns`、`events`、`import_logs`、`parse_warnings`、入库队列和可选向量表。
- 基于 SQLite FTS5 的干净知识全文检索。
- 标准检索、混合检索、摘要块、可选本地确定性向量索引和 agent 检索合同。
- Markdown、JSON、JSONL、CSV、Obsidian 和 Codex Skill 候选导出。
- 带证据事件 ID 的本地规则摘要。
- `warn`、`redact`、`fail` 三种隐私处理模式。
- 稳定 JSON 输出、内置 JSON Schema 和验证命令。
- 审计、备份、备份验证、恢复预检、恢复历史和保留策略。
- 原生 Tkinter 桌面端，不需要浏览器或前端构建环境。
- 只读 MCP stdio 服务，可供 Codex、ZCode、OpenCode 等本地客户端使用。
- Schema v8 冷热存储、重复正文消除、冷库垃圾回收和 Core/Evidence/Forensic 备份档位。
- 傻瓜式智能备份：先自动追平 Codex 源会话，再选档、检查磁盘、创建后验证并保留有限旧代。
- Codex 一键联动：一次安装 Stop hook 与只读 MCP，并提供可机器读取的状态诊断。
- 桌面“智能备份中心”：显示待入库来源、运行状态、自动计划、下次执行、磁盘空间并支持立即备份。
- 桌面安全导出：预览、隐私检查、参数一致性验证和最终确认后才写入。

以下能力有意不作为默认：

- 上传原始会话。
- 强制云同步或托管服务。
- 强制调用外部大模型生成摘要。
- 默认启用向量索引。
- 团队模式、中央权限/审计服务或共享 HTTP 服务器。

## 版本说明

2.x 是个人专用产品线：原生桌面端是主要本地界面，MCP 保持只读；以前的团队治理和浏览器 UI 代码只保留为历史证据。

| 版本 | 重点 |
|---|---|
| `2.4.2` | GitHub Actions CLI 测试去除终端样式干扰，并完成 Windows 发布矩阵加固。 |
| `2.4.1` | 自动追平源会话、Codex 一键联动、CI 覆盖率门禁和原生桌面工作台完善。 |
| `2.4.0` | 智能备份中心、完整确认导出、友好会话列表、安全恢复目标和自动健康诊断。 |
| `2.3.0` | 智能备份选档、验证、磁盘守卫和有界自动保留。 |
| `2.2.0` | 冷热归档、最小化备份、重复正文消除和写时复制迁移。 |
| `2.1.0` | Codex Stop hook 单会话自动入库、当前事件兼容和 MCP 注册。 |
| `2.0.0` | 个人专用运行时；移除活动团队治理/共享服务器并完成模块化。 |
| `1.0.1` | 清除最后的活动 Web UI 残留。 |
| `1.0.0` | 原生桌面端成为主要界面。 |

## 重要目录

| 路径 | 默认值/示例 | 用途 |
|---|---|---|
| 归档数据库 | `<repo-root>\data\threadvault.db` | 日常检索、摘要、桌面端、备份和恢复使用的 SQLite 热库。 |
| 冷证据库 | `<repo-root>\data\threadvault-cold` | 大型工具输出、元数据、补丁、压缩历史和图片资产。 |
| 导出目录 | 桌面端选择的目录或 `threadvault-desktop-export/` | 给人、Codex、Obsidian 或编辑器阅读的生成文件。 |
| 备份目录 | `<archive-db-parent>\storage-backups` | 自动 Core/Evidence/Forensic 备份、验证清单和最近运行状态。 |
| 配置文件 | Windows：`%APPDATA%\threadvault\threadvault.toml` | 隐私白名单、向量设置和历史保留。 |
| Codex 主目录 | `%USERPROFILE%\.codex` | 原始 `sessions`、`archived_sessions` 和 Codex 本地状态。 |

归档数据库不是日常阅读文档。阅读历史内容时使用桌面搜索、CLI 检索或显式导出。

## 安装

需要 Python 3.11 或更高版本。Windows 推荐 Python 3.12：

```powershell
cd <repo-root>
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
```

确认 CLI：

```powershell
threadvault --help
```

请使用 `threadvault ...` 控制台命令；当前软件包没有 `python -m threadvault` 入口。

## 最快开始：原生桌面端

Windows 双击或运行：

```powershell
.\启动ThreadVault桌面版.cmd
```

也可以直接运行：

```powershell
threadvault desktop launch
```

桌面端主要页面：

| 页面 | 用途 |
|---|---|
| 会话 | 按标题、项目、更新时间、事件数和警告浏览或搜索历史会话。 |
| 导出 | 选择格式、隐私处理和输出目录，先生成预览，再确认写入。 |
| 备份 | 查看待入库来源、智能备份状态、计划、磁盘和保留策略；高级区域提供手动备份与恢复。 |
| Codex 联动 | 查看并一键安装 MCP、Stop hook，检查最近 hook 活动和每日智能备份。 |
| 健康 | 自动运行只读诊断，把重建索引和压缩数据库放在独立维护区域。 |
| 高级 | 查看 Schema 和机器人说明；普通使用通常无需进入。 |

不打开窗口的桌面端检查：

```powershell
threadvault desktop smoke --json
```

## 第一次归档与自动入库

先用一个 dry-run-first 命令安装两项 Codex 联动，再追平初始归档；以后由 `Stop` hook 每轮只导入发生变化的 transcript：

```powershell
$archiveDb = (Resolve-Path .\data\threadvault.db).Path
threadvault codex install --db $archiveDb --json
threadvault codex install --db $archiveDb --apply --json
threadvault storage sync --db $archiveDb --apply --json
threadvault codex status --db $archiveDb --json
```

随后在 Codex 打开一次 `/hooks`，检查用户级 hook；若 Codex 要求，则信任它。非托管命令 hook 按精确命令哈希审核。安装器会固定当前 ThreadVault 可执行文件和数据库路径，保留其他 hook，不替换已有 `notify`，并更新 Codex 共用的 `~/.codex/config.toml` MCP 配置。MCP 新建或改变后需要重启 Codex。

检查联动：

```powershell
threadvault codex status --db $archiveDb --json
codex mcp list
threadvault storage sync --db $archiveDb --json
```

正常情况下，以后不需要每天手动执行全量 `threadvault import`。每日智能备份会先检查源会话新鲜度并只补导缺失、变化、旧解析器或新触碰的文件；任何补导失败都会阻止备份，避免把旧数据库当成完整备份。

## 搜索和重新利用旧会话

```powershell
threadvault list
threadvault search "关键词"
threadvault agent retrieve "关键词" --json
threadvault client session SESSION_ID --json
```

在新的 Codex task 中，已注册的只读 MCP 可以直接搜索归档并打开会话证据。

查看 MCP 清单或手动启动 stdio 服务：

```powershell
threadvault mcp manifest --json
threadvault mcp serve
```

MCP 工具有意保持只读：能力发现、统计、诊断、检索、会话详情和导出预览。MCP 导出预览不会写文件。

具体 Codex、OpenCode、ZCode 和 Obsidian 设置见 `docs/MCP_INTEGRATION.md`。

## 导出

导出一个会话：

```powershell
threadvault export --session SESSION_ID --out <repo-root>\exports
```

生成轻量 Codex Skill 候选：

```powershell
threadvault export-target skill --session SESSION_ID --out <repo-root>\threadvault-ui-output --json
```

Skill 候选使用小型 `SKILL.md` 路由到逐步加载的 references 和证据索引。如果需要较大的原文阅读文件，请选择 Markdown 或 Obsidian 目标。

## 冷热归档与智能备份

ThreadVault 把人类对话和干净全文索引保留在热 SQLite 中，将大型可逆证据放入 `threadvault-cold`。例行遥测仅保留小型哈希存根；当规范 assistant message 已存在时，重复的 `event_msg/agent_message` 正文不会重复保存。

日常只需要一个命令：

```powershell
threadvault storage sync --json
threadvault storage auto --apply --json
```

策略如下：

- 先自动追平 Codex 源会话；失败则停止备份并明确报错。
- 首次创建 Evidence 基线。
- 归档有变化时，最多执行一个到期档位：每日 Core、每周 Evidence、历史满 30 天后的每月 Forensic。
- 没有变化时跳过，不重复复制大型数据库。
- 每次创建后自动验证。
- 自动保留最新 Core 3 份、Evidence 2 份、Forensic 1 份。
- 自动清理不会删除手动备份或唯一实时归档内容。
- 写入前保留磁盘安全余量；空间不足时阻止，而不是静默降级。

诊断命令：

```powershell
threadvault storage audit --json
threadvault storage verify --deep --json
threadvault storage prune --json
```

存储迁移使用单独目标库：

```powershell
threadvault storage rebuild --target-db <new-db> --json
```

迁移不会覆盖源数据库，只有会话/事件计数、规范对话摘要、doctor 和冷引用验证全部通过后才能接受目标。

## 普通备份与恢复

创建和验证手动数据库备份：

```powershell
threadvault backup --out backups --json
threadvault backup-history latest --dir backups --json
threadvault backup-history verify-latest --dir backups --json
```

先做只读恢复预检：

```powershell
threadvault restore-plan --backup backups\threadvault-backup-YYYYMMDDTHHMMSSZ.db --target-db restored\threadvault.db --json
```

检查通过后再恢复到新数据库：

```powershell
threadvault restore --backup backups\threadvault-backup-YYYYMMDDTHHMMSSZ.db --target-db restored\threadvault.db --apply --json
```

桌面恢复默认生成新的目标文件名并拒绝覆盖现有数据库。删除或裁剪操作默认只预览，必须显式 `--apply` 或经过界面确认。

## JSON 与 agent 工作流

常用合同发现命令：

```powershell
threadvault capabilities --json
threadvault robot-docs guide --json
threadvault robot-docs schemas --json
threadvault schemas list --json
threadvault agent manifest --json
threadvault client manifest --json
threadvault mcp manifest --json
```

验证已保存的 JSON：

```powershell
threadvault search pytest --json --fields minimal > search.json
threadvault validate-json --schema search_minimal --input search.json --json
```

写出内置 JSON Schema：

```powershell
threadvault schemas write --out docs/schemas --json
```

## 隐私和本地数据

ThreadVault 默认不会上传会话。导入、搜索、摘要、审计、备份、恢复、桌面端和 MCP 都在本机运行。

导出前可以选择：

```powershell
threadvault privacy-scan --session SESSION_ID --json
threadvault export --session SESSION_ID --privacy-mode warn --out out
threadvault export --session SESSION_ID --privacy-mode redact --out out
threadvault export --session SESSION_ID --privacy-mode fail --out out
```

备份、导出、恢复历史和 manifest 都可能包含私有会话内容或本地路径。未经检查不要上传或提交到公开仓库。

## 配置

```powershell
threadvault config init --json
threadvault config show --json
threadvault config doctor --json
```

示例：

```toml
[storage]
# 留空时使用 data/threadvault.db。
archive_db = ""

[privacy]
allowlist = [
  { kind = "email", text = "dev@example.com" },
  { kind = "windows_abs_path", pattern = '^E:\\\\Codex\\\\' },
]

[retrieval.vector]
enabled = false
adapter = "local-hash"
dimensions = 64

[audit_history]
keep = 20

[backup_history]
keep = 10

[restore_history]
keep = 20
```

## 文档

- `README.md`：英文项目说明书。
- `README.zh-CN.md`：本简体中文项目说明书。
- `CONTEXT.md`：规范领域词汇。
- `AGENTS.md`：项目 Codex 规则。
- `CONTRIBUTING.md`：贡献与隐私要求。
- `SECURITY.md`：漏洞报告和本地数据边界。
- `docs/README.md`：文档地图。
- `docs/THREADVAULT_USAGE_MANUAL.md`：更详细的中文 CLI/桌面操作手册。
- `docs/MCP_INTEGRATION.md`：MCP 联动说明。
- `docs/ARCHITECTURE.md`、`docs/API.md`、`docs/DATABASE.md`：架构、合同和数据库说明。
- `docs/progress/releases/`：正式发布说明和验收记录。

## 开发与验证

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault capabilities --json
threadvault desktop smoke --json
threadvault mcp manifest --json
```

开始开发前请阅读 `AGENTS.md`、`CONTEXT.md`、当前长期文档和相关历史记录。

## 许可证

ThreadVault 使用 MIT License，详情见 `LICENSE`。
