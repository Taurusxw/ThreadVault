# 2026-07-03 Round 001 - Personal UI Interaction Fix

## 1. 本轮目标

修复 ThreadVault 中文个人 Web UI 的会话详情展示和导出预览流程，按全局 `AGENTS.md` 要求补齐开发留痕与标准文档入口，并在用户确认后迁移旧文档结构。

## 2. 背景原因

用户截图显示会话详情页事件预览列为空、导出页可以绕过真实预览门槛、部分中文界面仍显粗糙。后续复查还发现项目缺少全局规则要求的
`docs/PROGRESS.md`、`docs/DOC_INDEX.md` 和本轮 `docs/progress/rounds/` 留痕。用户随后确认旧文档迁移后删除旧位置，因此本轮继续完成旧文档归档迁移。

## 3. 修改范围

- Personal Web UI 前端资源和动作流程。
- UI 相关测试。
- 标准项目文档入口。
- 本轮开发进度记录。
- 旧文档路径迁移和活动引用更新。

## 4. 实施步骤

1. 阅读全局 `<user-home>\.codex\AGENTS.md`。
2. 阅读项目入口和现有 v4 文档。
3. 修复会话详情事件预览映射、时间格式、摘要折叠和会话输入框可读性。
4. 修复导出页预览状态机，禁止默认硬编码 `preview_accepted: true`。
5. 为导出结果添加中文摘要，同时保留右侧原始 JSON 输出。
6. 修复危险动作取消确认后的前端行为。
7. 增加静态测试和 JavaScript 语法检查。
8. 使用浏览器和本地 API 验证主要页面、导出、备份和危险动作拦截。
9. 补齐标准文档入口和本轮进度记录。
10. 在用户确认后，将 `docs/v0` 至 `docs/v4` 和 `docs/development-progress.md` 迁移到 `docs/progress/archive/`，删除旧位置并更新活动引用。

## 5. 关键决策

- 右侧 JSON 面板继续保留英文 key、命令、路径和原始隐私发现，避免破坏排查价值。
- 导出写入按钮只在当前 session、profile、privacy mode 与预览状态匹配时启用。
- 后端 `preview_required` 仍作为最终安全门，前端只提供更清晰的流程约束。
- 旧文档迁移后保留原始历史文件内容作为 archive 证据，但活动代码、测试和文档不再引用旧位置。

## 6. 修改清单

```text
src/threadvault/personal_ui.py
tests/test_v402_local_ui_server.py
tests/test_v403_personal_ui_workbench.py
tests/test_v404_ui_action_coverage.py
tests/test_v406_ui_chinese_localization.py
启动ThreadVault中文界面.cmd
AGENTS.md
docs/DEVELOPMENT.md
docs/RULES.md
docs/ARCHITECTURE.md
docs/API.md
docs/DATABASE.md
docs/KNOWLEDGE_GRAPH.md
docs/CHANGELOG.md
docs/TODO.md
docs/DOC_INDEX.md
docs/PROGRESS.md
docs/progress/README.md
docs/progress/rounds/2026-07-03-round-001-personal-ui-interaction-fix.md
docs/progress/archive/legacy-development-progress.md
docs/progress/archive/legacy-v0/
docs/progress/archive/legacy-v1/
docs/progress/archive/legacy-v2/
docs/progress/archive/legacy-v3/
docs/progress/archive/legacy-v4/
```

## 7. 测试与验证

已执行或计划在本轮结束前重新执行：

```powershell
py -3.12 -m pytest tests/test_v406_ui_chinese_localization.py tests/test_v404_ui_action_coverage.py tests/test_v403_personal_ui_workbench.py
py -3.12 -m pytest tests/test_v402_local_ui_server.py
py -3.12 -m pytest
node --check <served-app.js>
node --check <served-app.zh.js>
Invoke-WebRequest -Uri http://127.0.0.1:8766/api/health -UseBasicParsing
```

当前结果：

- Focused UI suite：28 passed。
- Full pytest suite：412 passed。
- Served English JavaScript：`node --check` passed。
- Served Chinese JavaScript：`node --check` passed。
- `/api/health`：returned `ok` for `127.0.0.1:8766`。

浏览器 QA 已覆盖：

- 归档
- 搜索
- 会话
- 导出
- 隐私
- 维护
- 备份 / 恢复
- 配置
- 结构定义
- 治理

浏览器 QA 证据：

```text
<user-temp>\threadvault-ui-qa-20260703\01-home.png
<user-temp>\threadvault-ui-qa-20260703\02-pro-governance-after-navigation.png
<user-temp>\threadvault-ui-qa-20260703\03-session-detail.png
<user-temp>\threadvault-ui-qa-20260703\04-export-flow.png
<user-temp>\threadvault-ui-qa-20260703\05-export-invalidated.png
```

真实本地写入结果：

```text
<repo-root>\threadvault-ui-output\sessions\019f185c-12b1-7f53-8e32-bbd240782f93.md
<repo-root>\threadvault-ui-output\threadvault-export-manifest.json
```

危险动作验证：

- `reindex` 不带 `confirm=true` 调用 `/api/action` 返回 `confirm_required`，未执行写入。
- Browser 插件在维护页原生确认交互中出现点击通道超时，因此危险动作只采用后端确认门槛和静态前端确认分支验证，没有确认执行。

## 8. 文档更新

本轮新增标准文档入口、进度总览、变更记录、文档索引和 round 留痕。用户确认后，本轮已把旧 `docs/v0` 至 `docs/v4` 和
`docs/development-progress.md` 迁移至 `docs/progress/archive/`，并删除旧位置。

## 9. 风险与遗留问题

- `docs/progress/archive/legacy-v*` 下仍保留旧式小写阶段文档名，作为历史证据存在。
- `threadvault-ui-output/` 与 `threadvault-ui-backups/` 是本地 QA 输出，可能包含私有数据。
- Browser 插件在原生确认弹窗场景下不稳定，视觉 QA 需要优先使用独立 Chrome/Playwright。

## 10. 下一步计划

1. 决定是否忽略或清理本地 UI 输出目录。
2. 将浏览器 QA 流程沉淀为可重复的脚本或 release 验收产物。

## 11. 状态

completed
