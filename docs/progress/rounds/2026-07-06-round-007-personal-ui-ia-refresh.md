# 2026-07-06 Round 007: Personal UI IA Refresh

## 本轮目标

优化个人 Web UI 的信息架构，让界面适配 MCP/AI 联动后的日常工作流，同时保持最简、结构化、操作友好。

## 背景原因

MCP stdio server 和轻量 Skill 导出已经成为 ThreadVault 的核心复用路径，但旧专业模式仍把 Privacy、Maintenance、Backup/Restore、Config、Schemas、Governance 等低频控制平铺在顶层导航。该结构更像 CLI 控制台映射，不利于普通操作路径。

## 修改范围

- `src/threadvault/personal_ui.py`
- `tests/test_v403_personal_ui_workbench.py`
- `tests/test_v406_ui_chinese_localization.py`
- `README.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- `docs/CHANGELOG.md`
- `docs/PROGRESS.md`
- `docs/DOC_INDEX.md`
- `pyproject.toml`
- `src/threadvault/__init__.py`

## 实施步骤

1. 将专业模式顶层导航重排为 Archive、Search、Session、Integrations、Export、Data Safety、Health、Advanced。
2. 新增 Integrations 页面，展示 MCP manifest/serve 命令、只读边界、可联动对象和联动检查。
3. 将 Privacy 与 Backup/Restore 合并为 Data Safety。
4. 将 Maintenance 与 Config 合并为 Health。
5. 将 Schemas、Robot docs 和 Governance 合并为 Advanced。
6. 将普通模式改为三步：Find old work、Open context、Reuse with AI。
7. 更新中文本地化、测试断言和用户文档。

## 关键决策

- 不引入 React/Vite 或新的前端构建链，继续使用项目既有静态 HTML/CSS/JS。
- MCP 在 UI 中作为只读联动入口呈现，不提供写文件捷径。
- 导出写入仍必须经过现有 preview gate 和 privacy mode。
- 低频开发者能力不删除，只从顶层导航降级到 Advanced。

## 修改清单

- 新增 `renderIntegrations`、`renderSafety`、`renderHealth`、`renderAdvanced` 页面。
- 新增 MCP 命令复制按钮和普通模式 MCP setup 入口。
- 新增最小 CSS 支持三步卡片、命令按钮、联动布局。
- 更新中文 HTML/JS 资源生成逻辑。
- 更新 UI workbench 和中文本地化测试。
- 将包版本推进到 `0.36.0`。

## 测试与验证

已运行：

```powershell
py -3.12 -m pytest tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py tests\test_v404_ui_action_coverage.py -q
py -3.12 -m pytest -q
py -3.12 -m ruff check src tests
```

结果：focused UI 测试 `23 passed`，全量 pytest `422 passed`，全量 ruff passed。

浏览器验证：

- 本地服务：`http://127.0.0.1:8767/zh`
- Chrome 桌面宽度截图检查：普通模式、联动页、专业模式导航无横向溢出。
- Chrome 390px 移动宽度截图检查：普通模式无横向溢出，三步卡片按顺序堆叠。

## 文档更新

- `README.md` 更新版本和 UI 快速开始说明。
- `docs/THREADVAULT_USAGE_MANUAL.md` 更新普通/专业模式说明和 MCP 联动页说明。
- `docs/CHANGELOG.md` 新增 `0.36.0` 条目。
- `docs/PROGRESS.md` 更新当前版本、最近完成事项和开发记录。
- `docs/DOC_INDEX.md` 登记本轮记录。

## 风险与遗留问题

- 中文本地化仍依赖广泛字符串替换，未来应迁移为结构化翻译表。
- 新 UI 布局需要浏览器截图复核，确认真实窗口中没有文字拥挤或错位。
- MCP 联动页目前提供命令复制和检查入口，不自动写客户端配置；这保持安全，但后续可设计 dry-run installer。

## 下一步计划

- 运行 ruff、版本检查和更完整 UI 测试。
- 启动本地 UI，进行浏览器渲染截图检查。

## 状态

completed
