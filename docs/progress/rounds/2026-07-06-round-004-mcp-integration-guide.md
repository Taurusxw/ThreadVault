# 2026-07-06 Round 004 - MCP Integration Guide

## 本轮目标

补齐 ThreadVault MCP 联动说明，让人和 AI 都能根据项目文档配置 Codex、OpenCode、ZCode、Obsidian 相关工作流。

## 背景原因

`0.34.0` 已经提供 `threadvault mcp manifest` 和 `threadvault mcp serve`，但现有文档更多说明了接口和联动计划，缺少一份直接可执行的配置说明书。

## 修改范围

- 新增 `docs/MCP_INTEGRATION.md`。
- 更新 README、文档地图、文档索引、API 文档、中文使用手册、进度总览和 changelog。
- 不修改运行时代码。

## 实施步骤

1. 读取 Codex MCP 官方手册缓存，确认 `config.toml` 的 `mcp_servers` stdio 配置字段。
2. 查询 OpenCode 官方 MCP server 配置，确认 `mcp`、`type: "local"` 和 `command` 数组等字段。
3. 查询 Z.AI 官方 MCP 文档，确认其支持 stdio MCP server 和通用 MCP-compatible client 配置，但不把未核实的 ZCode UI 菜单名称写死。
4. 运行 `threadvault mcp manifest --json`，以实际 manifest 校准工具列表和安全边界。
5. 写入专门的 MCP integration guide，并从现有标准文档接入口。

## 关键决策

- 把 Codex 和 OpenCode 写成可复制配置，因为配置格式已核实。
- 把 ZCode 写成本地 stdio server 的命令和字段含义，不臆造未核实的配置文件格式。
- 把 Obsidian 定位为 Markdown/Obsidian vault 输出消费端；直接 Obsidian MCP 属于另一个插件/server 的边界。
- 不推进包版本号，因为没有改变运行时代码或公开命令行为。

## 修改清单

- `docs/MCP_INTEGRATION.md`
- `README.md`
- `docs/README.md`
- `docs/DOC_INDEX.md`
- `docs/API.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- `docs/PROGRESS.md`
- `docs/CHANGELOG.md`
- `docs/progress/rounds/2026-07-06-round-004-mcp-integration-guide.md`

## 测试与验证

实际验证：

```powershell
threadvault mcp manifest --json
py -3.12 -m pytest tests\test_v334_mcp_stdio_server.py tests\test_v301_client_interface_readiness.py -q
rg -n "MCP_INTEGRATION|threadvault mcp serve|threadvault_export_preview" README.md docs
```

结果：

- `threadvault mcp manifest --json` 成功输出 `threadvault_mcp_manifest.v1`，包含 6 个只读 MCP tools。
- `py -3.12 -m pytest tests\test_v334_mcp_stdio_server.py tests\test_v301_client_interface_readiness.py -q` 通过：`7 passed in 0.82s`。
- `rg` 检查确认 README、文档索引、API、中文手册、进度记录和新说明书都包含 MCP guide 或关键命令入口。
- Codex MCP 手册、OpenCode MCP servers 文档、Z.AI MCP integration 文档均已读取或验证。

## 文档更新

- 新增专门 MCP 联动说明书。
- 更新文档索引和入口文档。
- 更新进度总览与 changelog。

## 风险与遗留问题

- ZCode 的具体配置文件格式可能随版本变化，文档只固定 stdio 命令和配置意图。
- Obsidian 直接 MCP 读写 vault 需要额外 Obsidian MCP 插件或 Local REST API 类插件，不属于 ThreadVault MCP 的当前边界。

## 下一步计划

- 后续可实现 `threadvault integrations doctor` 检查客户端是否能看到 MCP server。
- 后续可实现 `threadvault integrations install <target> --dry-run` 生成配置计划。

## 状态

completed
