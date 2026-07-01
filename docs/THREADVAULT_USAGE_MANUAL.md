# ThreadVault 使用说明书

本文是 ThreadVault 的独立使用说明，面向本机使用、脚本调用和后续维护。ThreadVault 是一个本地优先、隐私优先的 Codex 会话归档 CLI 工具，用来把本机 Codex 的 `.jsonl` 会话记录导入 SQLite，建立全文搜索索引，并支持搜索、摘要、导出、隐私扫描、诊断、备份和恢复。

## 1. 适用范围

ThreadVault 当前阶段适合做这些事：

- 扫描本机 Codex 会话目录：`~/.codex/sessions` 和 `~/.codex/archived_sessions`。
- 把 Codex `.jsonl` 会话文件导入本地 SQLite 数据库。
- 用 SQLite FTS5 做全文搜索。
- 按会话导出 Markdown、JSON、JSONL、CSV。
- 生成本地规则摘要，不调用外部 LLM。
- 在导出前扫描 API key、token、私钥、邮箱、绝对路径等敏感内容。
- 输出机器友好的 JSON，方便脚本或 agent 调用。
- 做本地诊断、索引重建、备份、恢复预检和恢复。

当前不包含：Web UI、TUI、桌面端、MCP Server、REST API、向量数据库、云同步、团队权限、外部 LLM 自动摘要。

## 2. 安装

进入项目根目录：

```powershell
cd E:\Codex\ThreadVault
```

安装开发版命令：

```powershell
py -3.12 -m pip install -e ".[dev]"
```

验证 CLI 是否可用：

```powershell
threadvault --help
```

注意：当前项目通过 `pyproject.toml` 的 console script 暴露 `threadvault` 命令。请使用 `threadvault ...`，不要使用 `py -3.12 -m threadvault ...`。

## 3. 数据库位置

默认数据库位置：

- Windows：`%LOCALAPPDATA%\threadvault\threadvault.db`
- macOS/Linux：`~/.local/share/threadvault/threadvault.db`

你也可以给每个命令显式指定数据库：

```powershell
threadvault list --db E:\Codex\ThreadVault\data\threadvault.db
```

如果只是试用，建议先指定一个临时数据库，避免影响默认库：

```powershell
threadvault init --db E:\Codex\ThreadVault\scratch\threadvault.db
```

## 4. 最快上手流程

第一步，初始化数据库：

```powershell
threadvault init
```

第二步，导入默认 Codex home：

```powershell
threadvault import
```

默认会读取：

- `%USERPROFILE%\.codex\sessions`
- `%USERPROFILE%\.codex\archived_sessions`

如果你的 Codex home 不在默认位置：

```powershell
threadvault import --codex-home C:\Users\Administrator\.codex
```

第三步，查看已导入会话：

```powershell
threadvault list
```

第四步，搜索关键词：

```powershell
threadvault search pytest
```

第五步，导出某个会话：

```powershell
threadvault export --session SESSION_ID --out E:\Codex\ThreadVault\exports
```

第六步，生成摘要：

```powershell
threadvault summarize --session SESSION_ID
```

## 5. 常用命令

### 5.1 初始化

```powershell
threadvault init
```

指定数据库：

```powershell
threadvault init --db E:\Codex\ThreadVault\data\threadvault.db
```

### 5.2 导入 Codex 会话

导入默认 Codex home：

```powershell
threadvault import
```

导入自定义 Codex home：

```powershell
threadvault import --codex-home C:\Users\Administrator\.codex
```

机器可读输出：

```powershell
threadvault import --codex-home C:\Users\Administrator\.codex --json
```

### 5.3 自动入库队列

v1 开始提供轻量 ingestion queue。Hook 或脚本可以先把入库请求写入本地 SQLite 队列，不在 Hook 进程里扫描和导入大量 transcript。

入队：

```powershell
threadvault ingest-queue enqueue --source hook --codex-home C:\Users\Administrator\.codex --reason session-stop --json
```

查看队列：

```powershell
threadvault ingest-queue list --json
```

预览将要处理的请求，不执行导入：

```powershell
threadvault ingest-queue process --json
```

显式处理队列并执行导入：

```powershell
threadvault ingest-queue process --apply --json
```

`process` 默认是 dry-run；只有加 `--apply` 才会调用实际导入流程。

### 5.4 Codex Hook 触发入口

v1 也提供 Codex Hook adapter。它从 stdin 读取 Codex Hook JSON，只把入库请求写入 ThreadVault 队列，不在 Hook 进程里执行重扫描或导入。

生成 `Stop` hook 配置片段：

```powershell
threadvault codex-hook config --json
```

如果要把数据库路径写入片段：

```powershell
threadvault codex-hook config --db E:\Codex\ThreadVault\data\threadvault.db --json
```

Codex Hook 中实际调用的命令形态：

```powershell
threadvault codex-hook ingest --db E:\Codex\ThreadVault\data\threadvault.db
```

调试 Hook payload 时可以输出 ThreadVault 诊断 JSON：

```powershell
threadvault codex-hook ingest --diagnostic-json --db E:\Codex\ThreadVault\data\threadvault.db
```

注意：Hook 只负责入队。之后仍需要显式运行：

```powershell
threadvault ingest-queue process --apply --json
```

### 5.5 列出会话

```powershell
threadvault list
```

JSON 输出：

```powershell
threadvault list --json
```

### 5.6 搜索

基础搜索：

```powershell
threadvault search pytest
```

限制结果数量：

```powershell
threadvault search pytest --limit 10
```

机器友好的低 token 输出：

```powershell
threadvault search pytest --json --fields minimal
```

标准 JSON 输出：

```powershell
threadvault search pytest --json --fields standard
```

完整 JSON 输出：

```powershell
threadvault search pytest --json --fields full
```

按会话过滤：

```powershell
threadvault search pytest --session SESSION_ID
```

按项目目录过滤：

```powershell
threadvault search pytest --cwd E:\Codex\ThreadVault
```

按时间过滤：

```powershell
threadvault search pytest --since 2026-01-01 --until 2026-12-31
```

按事件类型或工具过滤：

```powershell
threadvault search pytest --type function_call --tool shell
```

### 5.7 v2 检索合同与诊断

`threadvault search` 保持旧版兼容输出。v2 开始，agent 和未来接口优先使用 `retrieval` 命令组，因为它会返回带 diagnostics 的对象合同。

运行 v2 检索对象合同：

```powershell
threadvault retrieval query pytest --json
```

按会话、项目、事件类型或工具过滤：

```powershell
threadvault retrieval query pytest --session SESSION_ID --json
threadvault retrieval query pytest --cwd E:\Codex\ThreadVault --json
threadvault retrieval query pytest --type function_call --tool shell --json
```

只查看检索诊断，不执行查询：

```powershell
threadvault retrieval diagnose --json
```

输出约定：

- `retrieval query` 输出对象，包含 `contract_version`、`query`、`diagnostics`、`results`。
- `diagnostics` 会报告当前使用的检索模式、引擎、结果数量、fallback 状态和 FTS 索引健康状态。
- v2.1 只支持 `fts` 模式；语义检索和混合检索是后续 v2 阶段。
- diagnostics 不输出原始 transcript 路径或原始事件 payload。

### 5.8 v2 Summary Pipeline Chunk 选择

v2.2 开始提供 `summary-pipeline chunks`。它用于为后续可选 embedding / vector adapter 选择稳定输入，但本命令本身不生成 embedding，也不写入向量库。

按会话生成 summary/evidence chunks：

```powershell
threadvault summary-pipeline chunks --session SESSION_ID --json
```

按项目目录生成 chunks：

```powershell
threadvault summary-pipeline chunks --project E:\Codex\ThreadVault --json
```

限制每个 session 的 chunk 数量和单个 chunk 文本长度：

```powershell
threadvault summary-pipeline chunks --session SESSION_ID --max-chunks-per-session 8 --max-chars 1000 --json
```

输出约定：

- 顶层对象包含 `contract_version`、`selection`、`chunks`、`skipped`、`diagnostics`。
- chunk 类型包括 `session_summary`、`turn_summary`、`evidence`。
- 每个 chunk 都包含 `evidence_event_ids`，可回链到本地数据库事件。
- diagnostics 会明确 `embedding_generated: false`，表示本阶段只做选择，不做向量化。
- 本命令不会默认导出所有 raw events。

### 5.9 v2 本地 Vector Adapter

v2.3 开始提供 config-gated 本地 vector adapter。它使用本机 deterministic `local-hash` 向量，不调用外部 LLM，不下载模型，也不默认开启。它的输入来自 `summary_chunks`，不是全量 raw events。

先在本地 `threadvault.toml` 中显式开启：

```toml
[retrieval.vector]
enabled = true
adapter = "local-hash"
dimensions = 64
```

查看 vector index 状态，不需要开启 gate：

```powershell
threadvault vector status --json
```

按会话建立本地 vector index：

```powershell
threadvault vector index --session SESSION_ID --config E:\Codex\ThreadVault\threadvault.toml --json
```

按项目目录建立 index：

```powershell
threadvault vector index --project E:\Codex\ThreadVault --config E:\Codex\ThreadVault\threadvault.toml --json
```

查询本地 vector index：

```powershell
threadvault vector query "parser failure" --config E:\Codex\ThreadVault\threadvault.toml --json
```

输出约定：

- `vector index` 输出 `vector_index` 合同，记录 adapter、dimensions、source selection 和 indexed chunk 数量。
- `vector query` 输出 `vector_query` 合同，返回 ranked chunks、score 和 `evidence_event_ids`。
- `vector status` 输出 `vector_status` 合同，报告配置状态和当前 index 状态。
- 本阶段的 `local-hash` 是本地 deterministic vector adapter，不等同于神经语义 embedding。
- `threadvault retrieval query` 仍默认只走 FTS。

### 5.10 v2 Hybrid Retrieval

v2.4 开始提供 hybrid retrieval。它把 FTS event matches 和可选 vector chunk matches 合并到一个结果列表，并为每个结果输出 explanation。vector 未开启或没有 index 时，它会降级为 FTS-only，但仍返回 `hybrid_retrieval` 合同。

不使用 vector config，直接运行 FTS-only hybrid：

```powershell
threadvault retrieval hybrid pytest --json
```

使用已开启 vector 的配置进行 hybrid 检索：

```powershell
threadvault retrieval hybrid "parser failure" --config E:\Codex\ThreadVault\threadvault.toml --json
```

限制 FTS 和 vector 候选数量：

```powershell
threadvault retrieval hybrid "parser failure" --limit 10 --vector-limit 5 --config E:\Codex\ThreadVault\threadvault.toml --json
```

输出约定：

- 顶层对象包含 `contract_version`、`query`、`results`、`diagnostics`。
- `diagnostics.capabilities_used` 会说明本次用了 `fts`、`vector`、`hybrid` 中的哪些能力。
- 每个结果包含 `source`、`score`、`scores`、`evidence_event_ids` 和 `explanation`。
- `explanation.rank_factors` 会列出 FTS、vector、same-project、exact-hint 等分数因素。
- Hybrid 不会自动创建 vector index；需要先显式运行 `threadvault vector index`。

### 5.11 v2 Agent-Facing Retrieval Interface

v2.5 开始提供 `agent` 命令组。它把 retrieval、hybrid retrieval、schema discovery 和隐私默认值包装成更小的 agent-facing interface，供 Codex agents、未来 MCP adapter 或其他机器客户端调用。

查看 agent interface manifest：

```powershell
threadvault agent manifest --json
```

默认使用 hybrid 模式；如果 vector 未开启或 index 不可用，会保留 FTS-only 降级：

```powershell
threadvault agent retrieve pytest --json
```

显式使用 FTS-only 模式：

```powershell
threadvault agent retrieve pytest --mode fts --json
```

使用已开启 vector 的配置：

```powershell
threadvault agent retrieve "parser failure" --mode hybrid --config E:\Codex\ThreadVault\threadvault.toml --json
```

默认 agent 输出不包含本地 raw path metadata。仅在本地调试时显式打开：

```powershell
threadvault agent retrieve pytest --mode fts --local-debug --json
```

输出约定：

- `agent manifest` 输出 `agent_interface_manifest`。
- `agent retrieve` 输出 `agent_retrieval`。
- `agent_retrieval.results[*].evidence_event_ids` 可回链到 ThreadVault event。
- `privacy.raw_paths_included` 明确说明本次输出是否包含本地路径 metadata。

### 5.12 导出

导出 Markdown，默认格式是 `md`：

```powershell
threadvault export --session SESSION_ID --out E:\Codex\ThreadVault\exports
```

导出 JSON：

```powershell
threadvault export --session SESSION_ID --format json --out E:\Codex\ThreadVault\exports
```

导出 JSONL：

```powershell
threadvault export --session SESSION_ID --format jsonl --out E:\Codex\ThreadVault\exports
```

导出 CSV：

```powershell
threadvault export --session SESSION_ID --format csv --out E:\Codex\ThreadVault\exports
```

导出简洁摘要版：

```powershell
threadvault export --session SESSION_ID --brief --out E:\Codex\ThreadVault\exports
```

只导出最后 N 轮：

```powershell
threadvault export --session SESSION_ID --last-turns 3 --out E:\Codex\ThreadVault\exports
```

适合给 agent 阅读的轻量导出：

```powershell
threadvault export --session SESSION_ID --profile agent --out E:\Codex\ThreadVault\exports
```

排除工具输出和 reasoning：

```powershell
threadvault export --session SESSION_ID --no-tool-output --no-reasoning --out E:\Codex\ThreadVault\exports
```

限制单条事件文本长度：

```powershell
threadvault export --session SESSION_ID --max-chars 2000 --max-tool-chars 1000 --out E:\Codex\ThreadVault\exports
```

按项目目录导出索引：

```powershell
threadvault export --project E:\Codex\ThreadVault --format md --out E:\Codex\ThreadVault\exports
```

### 5.12 批量目标导出

v1 开始提供 `export-target`。它适合把一组会话或一个项目目录下的会话导出到同一个目标目录，并在目标根目录写入 `threadvault-export-manifest.json`。

#### 5.8.1 Markdown target

```powershell
threadvault export-target markdown --session SESSION_ID --out E:\Codex\ThreadVault\vault-export --json
```

`--session` 可以重复使用：

```powershell
threadvault export-target markdown --session A --session B --out E:\Codex\ThreadVault\vault-export --json
```

按项目目录导出：

```powershell
threadvault export-target markdown --project E:\Codex\ThreadVault --out E:\Codex\ThreadVault\vault-export --json
```

导出结果：

- 会话 Markdown 写入 `sessions/`。
- 项目导出会额外写入 `project-index.md`。
- `threadvault-export-manifest.json` 记录导出的文件、跳过的 session、隐私扫描摘要和 evidence event IDs。
- CLI 的 `--json` 输出和 manifest 文件使用同一个 `export_target_manifest` JSON contract。

#### 5.8.2 Obsidian/Markdown vault target

导出 Obsidian 可直接打开的 Markdown vault：

```powershell
threadvault export-target obsidian --session SESSION_ID --out E:\Codex\ThreadVault\obsidian-vault --json
```

按项目目录导出 vault：

```powershell
threadvault export-target obsidian --project E:\Codex\ThreadVault --out E:\Codex\ThreadVault\obsidian-vault --json
```

导出结果：

- `index.md`：vault 总入口。
- `sessions/SESSION_ID.md`：会话摘要页。
- `evidence/SESSION_ID-evidence.md`：证据事件页。
- 页面之间使用 Obsidian wiki link，例如 `[[sessions/SESSION_ID|Session]]`。
- evidence event IDs 同时保留在页面和 manifest 中，方便回链到 ThreadVault SQLite 事实层。

`export-target` 支持和普通导出一致的隐私模式：

```powershell
threadvault export-target obsidian --session SESSION_ID --out E:\Codex\ThreadVault\obsidian-vault --privacy-mode redact --json
```

#### 5.8.3 Codex Skill candidate target

导出 Codex Skill candidate 文件夹：

```powershell
threadvault export-target skill --session SESSION_ID --out E:\Codex\ThreadVault\skill-candidate --skill-name project-memory --json
```

按项目目录导出 Skill candidate：

```powershell
threadvault export-target skill --project E:\Codex\ThreadVault --out E:\Codex\ThreadVault\skill-candidate --skill-name threadvault-memory --json
```

导出结果：

- `SKILL.md`：可审阅的 Skill 主说明。
- `references/sessions.md`：会话摘要和 evidence event IDs。
- `references/evidence.md`：摘要引用到的证据事件。
- `threadvault-export-manifest.json`：记录文件、跳过项、隐私扫描摘要和 evidence。

这个 target 只生成候选 Skill 文件夹，不会自动安装到 `$CODEX_HOME/skills`。生成后应先人工审阅本地路径、摘要、证据和隐私扫描结果。

### 5.9 摘要

生成本地规则摘要：

```powershell
threadvault summarize --session SESSION_ID
```

JSON 摘要：

```powershell
threadvault summarize --session SESSION_ID --json
```

摘要包含会话主题、用户目标、关键步骤、关键命令、涉及文件、遇到的问题、下一步建议、证据 event_id，以及证据覆盖率字段。

## 6. 隐私扫描与安全导出

ThreadVault 默认不上传任何原始会话数据。所有导入、搜索、摘要、导出都在本机完成。

单独扫描某个会话：

```powershell
threadvault privacy-scan --session SESSION_ID
```

JSON 输出：

```powershell
threadvault privacy-scan --session SESSION_ID --json
```

导出时默认使用 `warn` 模式：发现敏感内容只警告，不修改原文。

```powershell
threadvault export --session SESSION_ID --privacy-mode warn --out E:\Codex\ThreadVault\exports
```

脱敏导出：

```powershell
threadvault export --session SESSION_ID --privacy-mode redact --out E:\Codex\ThreadVault\exports
```

严格模式：发现 high 或 critical 风险时拒绝写文件。

```powershell
threadvault export --session SESSION_ID --privacy-mode fail --out E:\Codex\ThreadVault\exports
```

### 6.1 隐私 allowlist

如果某些内容是已知安全样例，可以用本地 `threadvault.toml` 降低误报。

示例：

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
```

导出时使用配置：

```powershell
threadvault export --session SESSION_ID --privacy-mode fail --privacy-config threadvault.toml --out E:\Codex\ThreadVault\exports --json
```

allowlist 不会修改数据库原文，只影响扫描结果里的有效风险判断。

## 7. 诊断与维护

查看整体统计：

```powershell
threadvault stats
```

机器可读统计：

```powershell
threadvault stats --json
```

运行诊断：

```powershell
threadvault doctor
```

JSON 诊断：

```powershell
threadvault doctor --json
```

检查解析 warning：

```powershell
threadvault warnings
```

按 warning code 聚合：

```powershell
threadvault warnings --summary --json
```

不入库，只抽样检查 Codex JSONL 解析健康度：

```powershell
threadvault ingest-sample --codex-home C:\Users\Administrator\.codex --limit 20 --dry-run --json
```

重建 FTS5 索引：

```powershell
threadvault reindex --fts-only --json
```

整理 SQLite 数据库：

```powershell
threadvault vacuum --json
```

本地自检：

```powershell
threadvault self-test --json
```

## 8. 备份与恢复

创建备份：

```powershell
threadvault backup --out E:\Codex\ThreadVault\backups --json
```

验证备份：

```powershell
threadvault backup-verify --backup E:\Codex\ThreadVault\backups\BACKUP_FILE.db --manifest --json
```

查看备份 manifest：

```powershell
threadvault backup-manifest --backup E:\Codex\ThreadVault\backups\BACKUP_FILE.db --json
```

恢复前预检，不写入目标数据库：

```powershell
threadvault restore-plan --backup E:\Codex\ThreadVault\backups\BACKUP_FILE.db --target-db E:\Codex\ThreadVault\restored\threadvault.db --json
```

执行恢复：

```powershell
threadvault restore --backup E:\Codex\ThreadVault\backups\BACKUP_FILE.db --target-db E:\Codex\ThreadVault\restored\threadvault.db --apply --json
```

查看恢复历史：

```powershell
threadvault restore-history list --json
```

## 9. Agent / 脚本调用

查看能力清单：

```powershell
threadvault capabilities --json
```

查看 agent 使用说明：

```powershell
threadvault robot-docs guide --json
```

查看 JSON schema 风格说明：

```powershell
threadvault robot-docs schemas --json
```

运行 v2 检索对象合同：

```powershell
threadvault retrieval query pytest --json
```

查看 v2 检索诊断：

```powershell
threadvault retrieval diagnose --json
```

列出内置 schema：

```powershell
threadvault schemas list --json
```

验证某个 JSON 输出：

```powershell
threadvault validate-json --schema search_minimal --input payload.json
```

验证 v2 检索输出：

```powershell
threadvault validate-json --schema retrieval_query --input retrieval-output.json --json
threadvault validate-json --schema retrieval_diagnostics --input retrieval-diagnostics.json --json
threadvault validate-json --schema hybrid_retrieval --input hybrid-retrieval.json --json
```

验证 v2 Summary Pipeline chunk 输出：

```powershell
threadvault validate-json --schema summary_chunks --input summary-chunks.json --json
```

验证 v2 vector 输出：

```powershell
threadvault validate-json --schema vector_index --input vector-index.json --json
threadvault validate-json --schema vector_query --input vector-query.json --json
threadvault validate-json --schema vector_status --input vector-status.json --json
```

验证 v2 agent interface 输出：

```powershell
threadvault validate-json --schema agent_interface_manifest --input agent-manifest.json --json
threadvault validate-json --schema agent_retrieval --input agent-retrieval.json --json
```

约定：

- 带 `--json` 的命令，stdout 只输出 JSON。
- 人类可读的 Rich 表格只在没有 `--json` 时输出。
- JSON contract 原则是字段尽量追加，不随意删除或改名。

## 10. 推荐日常工作流

### 10.1 第一次使用

```powershell
cd E:\Codex\ThreadVault
py -3.12 -m pip install -e ".[dev]"
threadvault --help
threadvault init
threadvault import --json
threadvault stats
threadvault list
```

### 10.2 每天更新归档

```powershell
threadvault import --json
threadvault doctor --json
```

### 10.3 查找历史问题

```powershell
threadvault search "sqlite error" --json --fields standard
threadvault summarize --session SESSION_ID --json
threadvault export --session SESSION_ID --profile review --out E:\Codex\ThreadVault\exports
```

### 10.4 给 agent 提供上下文

```powershell
threadvault search pytest --json --fields minimal
threadvault agent manifest --json
threadvault agent retrieve pytest --json
threadvault export --session SESSION_ID --profile agent --last-turns 5 --out E:\Codex\ThreadVault\exports
```

### 10.5 导出前先做隐私检查

```powershell
threadvault privacy-scan --session SESSION_ID --json
threadvault export --session SESSION_ID --privacy-mode redact --out E:\Codex\ThreadVault\exports
```

### 10.6 周期性维护

```powershell
threadvault reindex --fts-only --json
threadvault backup --out E:\Codex\ThreadVault\backups --json
threadvault backup-history list --json
```

## 11. 常见问题

### 11.1 `threadvault` 不是可识别的命令

先在项目根目录安装：

```powershell
py -3.12 -m pip install -e ".[dev]"
```

如果仍不可用，关闭并重新打开 PowerShell，或者使用当前 Python Scripts 目录所在 PATH。

### 11.2 为什么 `py -3.12 -m threadvault --help` 不工作

当前项目没有 `threadvault.__main__`，入口是 console script：

```powershell
threadvault --help
```

### 11.3 导入时有 parse warnings 是不是失败

不一定。Codex transcript 格式不是稳定公开 API，ThreadVault 的原则是宽容解析：坏行、未知结构、缺失字段会记录 warning，但不会中断整个导入。可以查看：

```powershell
threadvault warnings --summary --json
```

### 11.4 会不会上传我的会话

不会。ThreadVault 默认本地运行，不上传原始会话数据。真实语料诊断命令也默认只输出统计和 warning metadata。

### 11.5 如何确认数据库健康

```powershell
threadvault doctor --json
threadvault self-test --json
```

### 11.6 如何重新建立搜索索引

```powershell
threadvault reindex --fts-only --json
```

### 11.7 如何安全恢复备份

先预检：

```powershell
threadvault restore-plan --backup BACKUP.db --target-db RESTORED.db --json
```

确认无误后再执行：

```powershell
threadvault restore --backup BACKUP.db --target-db RESTORED.db --apply --json
```

## 12. 项目内重要文档

- 主 README：`README.md`
- 本说明书：`docs/THREADVAULT_USAGE_MANUAL.md`
- 开发进度：`docs/development-progress.md`
- 最终验收：`docs/v0/phases/phase-31-final-cli-mvp-acceptance/final-cli-mvp-acceptance.md`
- 完成度审计：`docs/v0/phases/phase-30-completion-gap-audit/completion-gap-audit.md`
- 研究报告归档副本：`docs/v0/research/codex-session-archive-research.md`

## 13. 最小验收命令

如果你想确认当前项目能正常工作，可以跑：

```powershell
threadvault --help
threadvault capabilities --json
threadvault self-test --json
py -3.12 -m pytest
py -3.12 -m ruff check .
```

当前最终验收记录显示：

- `py -3.12 -m pytest`：138 passed
- `py -3.12 -m ruff check .`：All checks passed


