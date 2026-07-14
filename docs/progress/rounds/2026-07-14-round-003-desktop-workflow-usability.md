# 2026-07-14 Round 003: Desktop Workflow Usability

Status: completed

## 本轮目标

把原生桌面版从“功能入口集合”优化为普通用户可以直接理解和安全完成的日常工作流，重点闭环智能备份、会话浏览、导出、恢复和健康诊断。

## 背景原因

2.3.0 已有智能备份深模块，但桌面端仍只暴露旧的手动备份；导出预览只提示 CLI 命令；会话列表以技术字段和 UUID 为主；恢复目标默认指向当前数据库；健康与维护操作层级不清。实际窗口检查还发现缺少滚动条、目录选择器和一致的中文标签。

## 修改范围

- 扩展 `DesktopDataGateway` 的桌面专用视图模型和安全工作流。
- 重构 Tkinter 会话、导出、备份、Codex 联动、健康和高级页。
- 更新 capabilities、robot guide、desktop smoke 和版本元数据。
- 同步架构、API、规则、知识图谱、手册、变更、进度和索引文档。
- 完成专项、全量、静态、CLI、真实窗口和截图验收。

## 实施步骤

1. 从 Codex 本地 state 只读补充友好标题，内部仍以 session ID 定位。
2. 用 Treeview 表格显示标题、项目、时间、事件和警告，增加双击/回车打开及滚动条。
3. 建立不可变 `DesktopExportPlan`；参数变化立即失效，只有可执行预览才能进入本地确认和写入。
4. 将 `ArchiveStore.storage_auto_backup` 接入 Backup Center，显示自动计划、下次运行、磁盘守卫、档位与保留策略。
5. 默认生成不冲突的新恢复目标；健康页打开后自动诊断，把维护操作放入次级区域。
6. 增加目录/文件选择器、快捷键、可见焦点、中文标签和后台进度反馈。

## 关键决策

- `DesktopDataGateway` 是唯一桌面工作流边界；Tk 窗口只负责渲染、选择和确认。
- 备份中心不复制智能备份规则，继续复用同一档位、磁盘、验证、锁和保留实现。
- 桌面预览状态只在当前进程有效，不虚构跨 CLI 进程的 `preview_accepted` token。
- 会话 UUID 仍作为隐藏行键，用户可见主标签使用标题和项目。
- 恢复永远默认到新文件，桌面不提供覆盖当前库的捷径。

## 修改清单

- `src/threadvault/state.py`
- `src/threadvault/desktop_data.py`
- `src/threadvault/desktop_app.py`
- `src/threadvault/store.py`
- `tests/test_v407_desktop_app.py`
- `pyproject.toml`、`src/threadvault/__init__.py`
- 2.4.0 相关长期文档、schema 和本 round。

## 测试与验证

- 桌面专项：15 passed。
- 桌面相关 ruff 与 Python compile：passed。
- 全量回归：295 passed；Ruff 全项目：passed；`pip check`：No broken requirements found。
- 源码与安装元数据：2.4.0；capabilities JSON Schema：valid；desktop smoke：`desktop_smoke.v2`、`ok=true`；MCP manifest：2.4.0、六个只读工具。
- 真实库 doctor：schema v8，342 会话、835,177 事件、7 条已知 warning，FTS 835,177/835,177。
- 真实 Windows 窗口验收：会话标题/项目表格不再显示 thread URI；Backup Center 显示最近检查、03:15 自动计划、下次运行、磁盘与保留策略；导出确认在预览前禁用、预览后启用且未写盘；健康页自动加载并显示无必做维护。

## 文档更新

README、CONTEXT、DEVELOPMENT、RULES、ARCHITECTURE、API、KNOWLEDGE_GRAPH、CHANGELOG、TODO、DOC_INDEX、PROGRESS、使用手册和本 round。

## 风险与遗留问题

- Tkinter 的系统级辅助技术暴露能力受 Windows/Tk 运行时限制；本轮提供键盘焦点、原生控件和可见标签，但完整屏幕阅读器体验仍需 NVDA 等人工验收。
- “打开导出目录”仍在 TODO；当前会明确显示绝对输出目录和 manifest，不自动启动任意路径。

## 下一步计划

日常从“备份 → 智能备份中心”查看状态；后续如准备正式发布，再把 NVDA/屏幕阅读器人工检查和 MCP Inspector 纳入 release gate。
