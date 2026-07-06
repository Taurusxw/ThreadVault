# 2026-07-06 Round 003 MCP Stdio Server

## 本轮目标

设计并实现 ThreadVault MCP stdio server，让 Codex、ZCode、OpenCode 和其他 MCP-capable local agents 能通过统一工具读取 ThreadVault 本地归档知识。

## 背景原因

ThreadVault 已有 agent retrieval、client session、client export preview、capabilities、stats、doctor 等深模块。跨 agent 联动不应该让每个工具重新解析 Codex transcript 或直接读取 SQLite 表，而应该通过稳定的小接口复用现有能力。

## 详细计划书

### 目标架构

```text
Codex / ZCode / OpenCode
  -> MCP stdio JSON-RPC
  -> threadvault.mcp
  -> ArchiveStore
  -> agent_interface / client_interface / diagnostics
  -> MCP content + structuredContent
```

Obsidian 不直接连接 SQLite。它继续消费 `export-target obsidian` 生成的 Markdown vault；MCP 只提供导出预览，让 agent 可以先看计划再建议用户显式写文件。

### 第一版工具范围

| Tool | 复用接口 | 写文件 |
|---|---|---|
| `threadvault_capabilities` | `capabilities()` | 否 |
| `threadvault_stats` | `ArchiveStore.stats` | 否 |
| `threadvault_doctor` | `ArchiveStore.doctor` | 否 |
| `threadvault_retrieve` | `ArchiveStore.agent_retrieve` | 否 |
| `threadvault_session` | `ArchiveStore.client_session` | 否 |
| `threadvault_export_preview` | `ArchiveStore.client_export_preview` | 否 |

### 安全边界

- MCP 工具第一版只读。
- 导出只做 preview，不写 Markdown/Obsidian/Skill 文件。
- 默认不返回 raw local paths；`local_debug=true` 才返回调试元数据。
- 不绕过 privacy scan、preview gate、governance preflight 或 confirmation gate。
- 不引入独立前端构建链或后台托管服务。

### 后续阶段

1. 增加 `threadvault integrations doctor`，检查 Codex/ZCode/OpenCode/Obsidian 侧配置状态。
2. 增加 `threadvault integrations install <target> --dry-run`，默认只输出写入计划。
3. 在用户确认后再实现 `--apply` 配置写入。
4. 如需 MCP 写工具，必须先设计 preview/confirm/governance gate，不能直接写文件。

## 修改范围

- 新增 MCP runtime 模块和合同常量。
- 新增 CLI `mcp manifest` 和 `mcp serve`。
- 更新 agent/capabilities/robot docs/schema 发现面。
- 更新 MCP 测试和既有 readiness 测试。
- 更新 README、API、Architecture、Knowledge Graph、Usage Manual、Development、Progress、Changelog、Doc Index。

## 实施步骤

1. 新增 `mcp_contracts.py` 保存协议/manifest 常量。
2. 新增 `mcp.py` 处理 JSON-RPC initialize、ping、tools/list、tools/call。
3. 在 `cli.py` 挂载 `threadvault mcp manifest` 和 `threadvault mcp serve`。
4. 更新 `agent_interface.py`，把 MCP runtime 标记为已包含。
5. 更新 `store.py` 能力发现、robot guide、robot schemas。
6. 更新 `schemas.py` 注册 `mcp_manifest`。
7. 增加 focused tests 验证 manifest、tool list、工具调用和错误返回。
8. 更新标准文档和本轮进度记录。

## 关键决策

- 不引入额外 MCP SDK 依赖，使用 stdio JSON-RPC 最小实现，保持当前依赖面稳定。
- MCP module 只负责 transport adapter，不拥有检索、摘要、导出或数据库逻辑。
- `structuredContent` 返回原 ThreadVault JSON payload，便于支持结构化工具结果的客户端使用。
- `content[0].text` 同时返回格式化 JSON，兼容只读取文本内容的客户端。

## 修改清单

- `src/threadvault/mcp_contracts.py`
- `src/threadvault/mcp.py`
- `src/threadvault/cli.py`
- `src/threadvault/agent_interface.py`
- `src/threadvault/store.py`
- `src/threadvault/schemas.py`
- `tests/test_v334_mcp_stdio_server.py`
- `tests/test_v206_agent_interface.py`
- `tests/test_v301_client_interface_readiness.py`
- `pyproject.toml`
- `src/threadvault/__init__.py`
- `README.md`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWLEDGE_GRAPH.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- `docs/DEVELOPMENT.md`
- `docs/README.md`
- `docs/DOC_INDEX.md`
- `docs/PROGRESS.md`
- `docs/CHANGELOG.md`

## 测试与验证

```powershell
py -3.12 -m pytest tests\test_v334_mcp_stdio_server.py tests\test_v206_agent_interface.py tests\test_v301_client_interface_readiness.py -q
py -3.12 -m ruff check src\threadvault\mcp.py src\threadvault\mcp_contracts.py src\threadvault\cli.py src\threadvault\agent_interface.py src\threadvault\store.py src\threadvault\schemas.py tests\test_v334_mcp_stdio_server.py tests\test_v206_agent_interface.py tests\test_v301_client_interface_readiness.py
threadvault mcp manifest --json
threadvault schemas write --out docs\schemas --json
threadvault validate-json --schema mcp_manifest --input <user-temp>\threadvault-mcp-manifest.json --json
```

Results:

- Focused pytest: `13 passed`.
- Focused ruff: passed.
- Schema write generated `docs/schemas/mcp_manifest.schema.json`.
- MCP manifest schema validation passed.
- Stdio smoke for `threadvault mcp serve` returned `initialize` and `tools/list` responses.

## 文档更新

- `README.md` 增加 0.34.0 和 MCP 快速入口。
- `docs/API.md` 增加 MCP stdio interface 和联动计划书。
- `docs/ARCHITECTURE.md` 增加 MCP 模块、数据流和安全决策。
- `docs/KNOWLEDGE_GRAPH.md` 增加 MCP Tool 实体和跨 agent 数据流。
- `docs/THREADVAULT_USAGE_MANUAL.md` 增加中文 MCP 联动说明。
- `docs/PROGRESS.md`、`docs/CHANGELOG.md`、`docs/DOC_INDEX.md` 同步状态和索引。

## 风险与遗留问题

- 第一版 MCP 未提供自动安装 Codex/ZCode/OpenCode 配置的命令。
- 第一版 MCP 未提供写文件工具；导出写入仍需显式 CLI/UI。
- 不同 MCP 客户端对 `structuredContent` 支持程度可能不同，因此同时返回 text JSON。

## 下一步计划

- 后续单独设计 integrations doctor/install dry-run。
- 根据真实 Codex/ZCode/OpenCode 客户端配置体验微调 manifest 文案。

## 状态

completed
