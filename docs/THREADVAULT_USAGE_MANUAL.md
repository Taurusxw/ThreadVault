# ThreadVault 使用说明书

本文面向本机使用、脚本调用、UI 排查和后续维护。ThreadVault 是一个本地优先、隐私优先的 Codex 会话归档与复用工具：它把本机 Codex 的 `.jsonl` 会话记录导入 SQLite，建立全文搜索索引，并提供原生桌面应用、CLI、检索、摘要、导出、隐私扫描、诊断、备份、恢复、MCP 和治理预检能力。

## 1. 先弄懂它有什么用

ThreadVault 解决的是这几类问题：

- 以前和 Codex 讨论过的方案、报错、命令、文件改动，怎么找回来。
- 想让 Codex 继续接着旧工作做，怎么把旧会话导出成可读上下文。
- 不想翻原始 JSONL，怎么用搜索、摘要、事件预览和证据 ID 看清一段会话。
- 导出之前怎么知道里面有没有邮箱、token、私钥、绝对路径等敏感信息。
- 本地归档数据库怎么备份、恢复、诊断和维护。

一句话：ThreadVault 的“索引库”负责找旧记录，“导出目录”负责生成给人、Codex、Obsidian 或 Skill 使用的文件。

## 2. 当前能力边界

当前已经具备：

- 本地 Codex 会话扫描和导入。
- SQLite 归档数据库与 FTS5 全文搜索。
- 本地原生 Tkinter 桌面应用，作为 1.0.0 主界面。
- 旧 Web UI runtime、启动器、活跃 schema、测试和活跃发现元数据已从当前包中移除；历史证据保留在 `docs/progress/archive/legacy-v4/`。
- 会话列表、会话详情、摘要、事件预览和 warning 查看。
- v2 检索合同、hybrid retrieval、agent retrieval、summary chunks。
- 可选本地 deterministic vector adapter，默认关闭。
- Markdown、JSON、JSONL、CSV、Obsidian vault、Codex Skill candidate 导出。
- 导出预览、隐私扫描、隐私模式 `warn` / `redact` / `fail`。
- JSON Schema、机器可读输出、agent 调用入口。
- 本地备份、备份验证、恢复预检、恢复执行、历史记录。
- 可选治理状态、权限预检、审计、身份 actor、策略和业务命令 instrumentation 诊断。

当前仍不是默认能力：

- 不默认上传原始会话。
- 不默认调用外部 LLM。
- 不默认开启 vector index。
- 不要求云同步、共享服务器或团队权限。
- 不自动安装生成的 Codex Skill。

## 3. 重要路径

| 名称 | 默认或示例 | 用途 |
|---|---|---|
| 索引库 / Archive DB | `<repo-root>\data\threadvault.db` | 本地 SQLite 归档数据库，用于搜索、检索、UI、摘要、备份和恢复。可用 `--db`、`THREADVAULT_DB` 或 `[storage].archive_db` 覆盖。 |
| 导出目录 / Export folder | `threadvault-desktop-export/` 或显式 `--out` 目录 | 写出 Markdown、Obsidian、Skill 等文件。 |
| 备份目录 | `threadvault-desktop-backups/` 或自定义目录 | 保存 SQLite 备份文件和 manifest。 |
| Codex home | `%USERPROFILE%\.codex` | 原始 Codex transcript 来源目录。 |
| 配置文件 | `%APPDATA%\threadvault\threadvault.toml` | 隐私 allowlist、vector、历史保留、治理配置。 |

常见误解：

- `threadvault.db` 不是给人看的导出文件，它是索引库。
- `threadvault-desktop-export` 或你显式指定的 `--out` 目录才是 UI 默认写出的 Markdown/Skill/Obsidian 文件夹。
- 备份 `.db` 可能包含私密会话内容，不要当普通报告分享。

## 4. 安装

进入项目根目录：

```powershell
cd <repo-root>
```

安装开发版：

```powershell
py -3.12 -m pip install -e ".[dev]"
```

验证 CLI：

```powershell
threadvault --help
```

注意：请使用 `threadvault ...`。当前项目没有 `threadvault.__main__`，所以 `py -3.12 -m threadvault --help` 不工作是正常的。

## 5. 最快上手：本地界面

### 5.1 本地桌面应用

启动 1.0.0 方向的最小原生窗口：

```powershell
.\启动ThreadVault桌面版.cmd
```

或直接运行命令：

```powershell
threadvault desktop launch
```

不打开窗口，只做桌面端 smoke 检查：

```powershell
threadvault desktop smoke --json
```

桌面应用使用 Python 标准库 Tkinter，不需要浏览器、Electron、React、Tauri 或前端构建流程。当前迁入的高频页面包括：

| 页签 | 用途 |
|---|---|
| 浏览 | 搜索旧会话、打开摘要、查看搜索结果。 |
| 导出 | 对当前会话生成 Markdown、Obsidian 或 Skill 导出预览；不直接写文件。 |
| 安全 | 查看 parser warning 和 privacy scan 摘要；执行备份、备份验证、恢复预检和恢复到新目标库。 |
| MCP | 查看 MCP manifest/serve 命令和只读工具。 |
| 健康 | 运行数据库统计、doctor 诊断、重建搜索索引和数据库压缩。 |
| 高级 | 原生查看 Schema、机器人文档、治理状态和治理诊断；确认后写出 Schema 文件。 |

性能策略：窗口只负责显示和操作，归档读取、搜索、导出预览、隐私检查、备份、恢复预检、恢复执行、诊断和高级面板都通过后台线程调用现有接口，避免主窗口卡死。Tkinter 变量只在 UI 线程读取，后台线程只接收普通字符串/路径值。备份、重建索引、压缩数据库、恢复执行和 schema write 会先弹出本地确认框；桌面恢复执行只允许写到不存在的新目标库，拒绝覆盖已有数据库。

| 按钮 | 用途 | 结果 |
|---|---|---|
| 找回旧工作 | 按关键词、报错、项目名或决策查历史 Codex 工作。 | 显示匹配会话卡片。 |
| 打开上下文 | 直接看最新会话详情。 | 显示摘要、事件预览、证据 ID。 |
| 交给 AI 复用 | 打开 MCP 设置，或从当前/最近会话生成 Skill 预览。 | MCP 走只读记忆；Skill 先预览，再写入导出目录。 |

如果你只想“找到旧内容并继续用”，先用普通模式就够了。

## 6. 专业 UI 模式

专业模式是分层工作台：

| 页面 | 用途 |
|---|---|
| 归档 | 浏览会话列表，按项目/cwd 过滤。 |
| 搜索 | 标准搜索、retrieval query、hybrid retrieval、agent retrieve。 |
| 会话 | 查看单个会话的摘要、事件预览、证据 ID、warning 和导出入口。 |
| 联动 | 查看 MCP 命令、只读边界、Codex/ZCode/OpenCode/Obsidian 联动说明和能力检查。 |
| 导出 | 选择 session/profile/privacy，先生成预览，再写文件。 |
| 数据安全 | 运行 privacy scan、warning 检查、备份、验证、恢复预检、恢复执行和历史记录。 |
| 健康诊断 | 查看 stats、doctor、self-test、reindex、vacuum、配置查看和配置诊断。 |
| 高级 | 查看/验证/写出 JSON Schema、机器人文档、本地治理状态、预检、gap audit 和外部模型预检。 |

联动页中的 MCP 命令可以直接复制：

```powershell
threadvault mcp manifest --json
threadvault mcp serve
```

MCP 联动保持只读；真正写 Markdown、Obsidian 或 Skill 文件仍从“导出”页走预览和写入确认。

### 6.1 UI 反馈怎么看

顶部状态条显示当前动作：

- 绿色点：当前服务正常或动作完成。
- 转圈：动作正在运行。
- 绿色对勾：动作完成。
- 红色/失败提示：动作失败，详情看页面提示或 JSON 面板。

导出流程会显示三步：

```text
选择会话和格式 -> 生成预览 -> 写入文件
```

只有预览匹配当前 session、profile、privacy mode 和输出路径时，对应写入按钮才会解锁。

## 7. CLI 基础流程

初始化数据库：

```powershell
threadvault init
```

导入默认 Codex home：

```powershell
threadvault import --json
```

默认读取：

```text
%USERPROFILE%\.codex\sessions
%USERPROFILE%\.codex\archived_sessions
```

指定 Codex home：

```powershell
threadvault import --codex-home <user-home>\.codex --json
```

列出会话：

```powershell
threadvault list
threadvault list --json
```

搜索：

```powershell
threadvault search pytest
threadvault search pytest --json --fields minimal
threadvault search pytest --session SESSION_ID --json --fields standard
threadvault search pytest --cwd <repo-root> --json --fields standard
```

看统计和诊断：

```powershell
threadvault stats --json
threadvault doctor --json
threadvault warnings --summary --json
```

## 8. 检索、摘要和 Agent 上下文

普通 `search` 保持兼容；新脚本和 agent 推荐用 retrieval/agent 接口。

v2 检索：

```powershell
threadvault retrieval query pytest --json
threadvault retrieval diagnose --json
threadvault retrieval hybrid "parser failure" --json
```

Agent 检索：

```powershell
threadvault agent manifest --json
threadvault agent retrieve pytest --json
threadvault agent retrieve pytest --mode fts --json
threadvault agent retrieve "parser failure" --mode hybrid --json
```

默认 agent 输出不会包含 raw path metadata。只有本地调试时才显式打开：

```powershell
threadvault agent retrieve pytest --mode fts --local-debug --json
```

### 8.2 MCP 联动 Codex / ZCode / OpenCode

ThreadVault 可以作为本机 MCP stdio server 暴露给支持 MCP 的 agent。第一版 MCP 工具是只读的，适合把 ThreadVault 当作“历史记忆检索层”：

```powershell
threadvault mcp manifest --json
threadvault mcp serve
```

MCP tools：

| Tool | 用途 | 是否写文件 |
|---|---|---|
| `threadvault_capabilities` | 查看 ThreadVault 能力和 JSON 合同。 | 否 |
| `threadvault_stats` | 查看归档库统计和 clean index 诊断。 | 否 |
| `threadvault_doctor` | 本地数据库、FTS、Codex 发现诊断。 | 否 |
| `threadvault_retrieve` | 给 agent 检索历史上下文。 | 否 |
| `threadvault_session` | 打开某个 session 的摘要、证据和事件预览。 | 否 |
| `threadvault_export_preview` | 预览 Markdown/Obsidian/Skill 会写什么。 | 否 |

联动设计建议：

- Codex：用 Codex Hook 做轻量 enqueue/import，用 MCP 查历史。
- ZCode：把 `threadvault mcp serve` 配成 MCP server；后续可再包成 ZCode Skill/Plugin。
- OpenCode：把 ThreadVault 作为只读 memory MCP server；写导出文件仍用显式 CLI。
- Obsidian：使用 `export-target obsidian` 生成 Markdown vault；MCP 只做导出预览。

安全边界：

- MCP 默认不暴露 raw path metadata。
- `local_debug=true` 才会返回本地调试元数据。
- MCP 预览导出不写文件；真正写文件仍要运行 `threadvault export-target ...`。
- 不通过 MCP 绕过 privacy scan、preview gate 或 governance preflight。

详细配置示例和 AI 自配置协议见 `docs/MCP_INTEGRATION.md`。

生成本地规则摘要：

```powershell
threadvault summarize --session SESSION_ID
threadvault summarize --session SESSION_ID --json
```

生成 summary/evidence chunks：

```powershell
threadvault summary-pipeline chunks --session SESSION_ID --json
threadvault summary-pipeline chunks --project <repo-root> --json
```

### 8.1 可选 Vector

Vector 默认关闭。开启需要本地配置：

```toml
[retrieval.vector]
enabled = true
adapter = "local-hash"
dimensions = 64
```

查看状态：

```powershell
threadvault vector status --json
```

建立本地 vector index：

```powershell
threadvault vector index --session SESSION_ID --config <repo-root>\threadvault.toml --json
```

查询：

```powershell
threadvault vector query "parser failure" --config <repo-root>\threadvault.toml --json
```

说明：

- 当前 `local-hash` 是本地 deterministic adapter，不是神经语义 embedding。
- 输入来自 summary chunks，不默认向量化所有 raw events。
- Hybrid 可以在 vector 不可用时降级为 FTS-only。

## 9. 导出

### 9.1 单会话导出

Markdown：

```powershell
threadvault export --session SESSION_ID --out <repo-root>\exports
```

JSON / JSONL / CSV：

```powershell
threadvault export --session SESSION_ID --format json --out <repo-root>\exports
threadvault export --session SESSION_ID --format jsonl --out <repo-root>\exports
threadvault export --session SESSION_ID --format csv --out <repo-root>\exports
```

适合给 agent 阅读的轻量导出：

```powershell
threadvault export --session SESSION_ID --profile agent --last-turns 5 --out <repo-root>\exports
```

### 9.2 Export Target

`export-target` 适合批量生成有 manifest 的输出目录。

Markdown target：

```powershell
threadvault export-target markdown --session SESSION_ID --out <repo-root>\threadvault-ui-output --json
```

Obsidian vault target：

```powershell
threadvault export-target obsidian --session SESSION_ID --out <repo-root>\obsidian-vault --json
```

Codex Skill candidate：

```powershell
threadvault export-target skill --session SESSION_ID --out <repo-root>\skill-candidate --skill-name project-memory --json
```

Skill candidate 是轻量 Codex Skill 包，不是完整 transcript 转储。它默认写出：

- `SKILL.md`
- `references/index.md`
- `references/sessions.md`
- `references/evidence.md`
- `references/session-SESSION_ID.md`

读取顺序是先看 `references/index.md` 和 `references/sessions.md`，需要某个会话细节时再打开对应 `references/session-*.md`。`references/evidence.md` 只保留短证据片段和事件 ID；需要完整原文时，用 Markdown/Obsidian 导出或回到 ThreadVault 检索。

按项目目录导出：

```powershell
threadvault export-target markdown --project <repo-root> --out <repo-root>\vault-export --json
threadvault export-target obsidian --project <repo-root> --out <repo-root>\obsidian-vault --json
threadvault export-target skill --project <repo-root> --out <repo-root>\skill-candidate --json
```

导出目录里通常会有：

- `sessions/`
- `evidence/`
- `references/`
- `SKILL.md`
- `index.md`
- `threadvault-export-manifest.json`

具体取决于 target 类型。

### 9.3 导出预览

UI 导出必须先预览。CLI 的 client preview 也可以单独跑：

```powershell
threadvault client export-preview --session SESSION_ID --out <repo-root>\threadvault-ui-output --profile skill --json
```

预览只描述将要写什么，不写文件。真正写文件用 `export` 或 `export-target`。

## 10. 隐私扫描与安全导出

单独扫描：

```powershell
threadvault privacy-scan --session SESSION_ID --json
```

导出隐私模式：

```powershell
threadvault export --session SESSION_ID --privacy-mode warn --out <repo-root>\exports
threadvault export --session SESSION_ID --privacy-mode redact --out <repo-root>\exports
threadvault export --session SESSION_ID --privacy-mode fail --out <repo-root>\exports
```

含义：

| 模式 | 行为 |
|---|---|
| `warn` | 报告隐私发现，但仍写文件。 |
| `redact` | 对支持的敏感文本做脱敏后写文件。 |
| `fail` | 发现 high/critical 风险时阻止写文件。 |

### 10.1 Privacy Allowlist

`threadvault.toml` 示例：

```toml
[privacy]
allowlist = [
  { kind = "email", text = "dev@example.com" },
  { kind = "windows_abs_path", pattern = '^E:\\\\Codex\\\\' },
]
```

使用配置：

```powershell
threadvault privacy-scan --session SESSION_ID --privacy-config threadvault.toml --json
threadvault export --session SESSION_ID --privacy-mode fail --privacy-config threadvault.toml --out <repo-root>\exports --json
```

Allowlist 不修改数据库原文，只影响扫描结果里的有效风险判断。

## 11. 配置

创建配置：

```powershell
threadvault config init --json
```

查看配置：

```powershell
threadvault config show --json
threadvault config show --include-values --json
```

诊断配置：

```powershell
threadvault config doctor --json
```

默认配置路径：

```text
%APPDATA%\threadvault\threadvault.toml
```

配置可以控制：

- storage archive DB 自定义路径
- privacy allowlist
- audit / backup / restore history 保留数量
- retrieval vector 是否启用
- governance 是否启用
- local identity actors
- central policy / audit / backup policy 文件路径

## 12. 备份与恢复

创建备份：

```powershell
threadvault backup --out <repo-root>\backups --json
```

验证备份：

```powershell
threadvault backup-verify --backup <repo-root>\backups\BACKUP_FILE.db --manifest --json
threadvault backup-history verify-latest --dir <repo-root>\backups --json
```

查看备份历史：

```powershell
threadvault backup-history list --dir <repo-root>\backups --json
threadvault backup-history latest --dir <repo-root>\backups --json
```

恢复前预检：

```powershell
threadvault restore-plan --backup <repo-root>\backups\BACKUP_FILE.db --target-db <repo-root>\restored\threadvault.db --json
```

执行恢复：

```powershell
threadvault restore --backup <repo-root>\backups\BACKUP_FILE.db --target-db <repo-root>\restored\threadvault.db --apply --json
```

查看恢复历史：

```powershell
threadvault restore-history list --json
threadvault restore-history latest --json
```

恢复相关规则：

- `restore-plan` 不写目标数据库。
- `restore` 必须显式 `--apply` 才执行。
- UI 中恢复执行必须确认。
- 备份文件可能包含私密会话内容。

## 13. 治理与审计

治理是本地可选诊断和预检，不代表默认开启云/团队模式。

查看治理状态：

```powershell
threadvault governance status --json
```

权限预检：

```powershell
threadvault governance permission check --role viewer --operation search --actor reviewer@example --target-type archive --target-id local --json
```

治理 gap：

```powershell
threadvault governance enforcement gaps --json
threadvault governance v3 gap-audit --json
```

外部模型预检：

```powershell
threadvault governance preflight external-model --command "threadvault summarize --external" --role operator --json
```

本地审计记录：

```powershell
threadvault governance audit append --log <repo-root>\audit.jsonl --operation export --actor local-user --status preview --target-type session --target-id SESSION_ID --json
threadvault governance audit list --log <repo-root>\audit.jsonl --json
```

## 14. 自动入库队列和 Codex Hook

Hook 只负责轻量入队，不在 Hook 进程里做大扫描。

入队：

```powershell
threadvault ingest-queue enqueue --source hook --codex-home <user-home>\.codex --reason session-stop --json
```

查看队列：

```powershell
threadvault ingest-queue list --json
```

预览处理：

```powershell
threadvault ingest-queue process --json
```

执行处理：

```powershell
threadvault ingest-queue process --apply --json
```

生成 Codex Hook 配置片段：

```powershell
threadvault codex-hook config --json
```

Hook 调用入口：

```powershell
threadvault codex-hook ingest --db <repo-root>\data\threadvault.db
```

## 15. JSON 和 Schema

能力清单：

```powershell
threadvault capabilities --json
threadvault robot-docs guide --json
threadvault robot-docs schemas --json
threadvault mcp manifest --json
```

列出 schema：

```powershell
threadvault schemas list --json
```

查看 schema：

```powershell
threadvault schemas show retrieval_query --json
```

验证 JSON：

```powershell
threadvault validate-json --schema retrieval_query --input retrieval-output.json --json
threadvault validate-json --schema agent_retrieval --input agent-retrieval.json --json
threadvault validate-json --schema mcp_manifest --input mcp-manifest.json --json
```

写出 schema 文件：

```powershell
threadvault schemas write --out docs\schemas --json
```

## 16. 推荐日常工作流

### 16.1 第一次使用

```powershell
cd <repo-root>
py -3.12 -m pip install -e ".[dev]"
threadvault --help
threadvault init
threadvault import --json
threadvault stats --json
.\启动ThreadVault桌面版.cmd
```

### 16.2 每天更新归档

```powershell
threadvault import --json
threadvault doctor --json
```

### 16.3 查找历史问题

```powershell
threadvault search "sqlite error" --json --fields standard
threadvault agent retrieve "sqlite error" --json
threadvault client session --session SESSION_ID --json
```

### 16.4 给 Codex 继续用

```powershell
threadvault client export-preview --session SESSION_ID --out <repo-root>\threadvault-ui-output --profile skill --json
threadvault export-target skill --session SESSION_ID --out <repo-root>\threadvault-ui-output --json
```

或直接在普通 UI 里点击“导出给 Codex 继续用”。

### 16.5 周期性维护

```powershell
threadvault reindex --fts-only --json
threadvault backup --out <repo-root>\backups --json
threadvault backup-history list --dir <repo-root>\backups --json
```

## 17. 常见问题

### 17.1 索引库默认在哪里，怎么自定义

当前项目默认 archive database 在：

```text
<repo-root>\data\threadvault.db
```

解析优先级是：

```text
--db PATH > THREADVAULT_DB > threadvault.toml 的 [storage].archive_db > data/threadvault.db
```

这个数据库是长期索引库，不是导出文件。导出文件默认在项目下的 `threadvault-desktop-export` 或你指定的 `--out` 目录。

### 17.2 为什么都完成了还像在加载

桌面端长任务应通过状态栏反馈完成或失败。如果界面状态异常，可以运行：

```powershell
threadvault desktop smoke --json
```

### 17.3 `threadvault` 不是可识别命令

在项目根目录安装：

```powershell
py -3.12 -m pip install -e ".[dev]"
```

如果仍不可用，重新打开 PowerShell，或检查 Python Scripts 目录是否在 PATH。

### 17.4 导入时有 parse warnings 是不是失败

不一定。ThreadVault 宽容解析 Codex transcript：坏行、未知结构、缺失字段会记录 warning，但不会中断整个导入。

```powershell
threadvault warnings --summary --json
```

### 17.5 会不会上传我的会话

默认不会。ThreadVault 的导入、搜索、摘要、导出、诊断、UI、备份和恢复都在本机运行。外部模型相关能力必须显式配置/调用并通过治理可见。

### 17.6 如何确认数据库健康

```powershell
threadvault doctor --json
threadvault self-test --json
threadvault desktop smoke --json
```

### 17.7 如何重新建立搜索索引

```powershell
threadvault reindex --fts-only --json
```

### 17.8 如何安全恢复备份

先预检：

```powershell
threadvault restore-plan --backup BACKUP.db --target-db RESTORED.db --json
```

确认无误后再执行：

```powershell
threadvault restore --backup BACKUP.db --target-db RESTORED.db --apply --json
```

## 18. 项目内重要文档

- `README.md`：项目概览和快速上手。
- `CONTEXT.md`：统一术语。
- `docs/ARCHITECTURE.md`：架构和模块边界。
- `docs/API.md`：JSON 合同、MCP 和能力发现。
- `docs/DATABASE.md`：数据库和路径说明。
- `docs/KNOWLEDGE_GRAPH.md`：实体关系和安全边界。
- `docs/DOC_INDEX.md`：文档索引。
- `docs/PROGRESS.md`：当前进展和验证记录。
- `docs/progress/archive/`：历史开发归档。

## 19. 最小验收命令

```powershell
threadvault --help
threadvault capabilities --json
threadvault self-test --json
threadvault desktop smoke --json
py -3.12 -m pytest
py -3.12 -m ruff check .
```

当前验证结果以 `docs/PROGRESS.md` 为准。
