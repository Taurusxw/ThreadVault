# 2026-07-06 Round 008: Compact UI Density

## 本轮目标

把个人 Web UI 统一调整为紧凑的桌面工具风格，参考小型原生工具窗口的密度：小字号、低留白、低圆角、扁平边框、控件高度稳定。

## 背景原因

用户希望所有 UI 页面采用更紧凑、操作友好、结构清楚的风格。参考图只作为视觉密度参考，不需要复刻微信助手界面。

## 修改范围

- `src/threadvault/personal_ui.py`
- `tests/test_v403_personal_ui_workbench.py`
- `README.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- `docs/CHANGELOG.md`
- `docs/PROGRESS.md`
- `docs/DOC_INDEX.md`
- `pyproject.toml`
- `src/threadvault/__init__.py`

## 实施步骤

1. 引入紧凑尺寸变量：`--control-height: 32px` 和 `--radius: 4px`。
2. 收窄专业模式侧栏和 JSON 面板占比。
3. 降低全局字号、标题字号、面板 padding、表格单元格 padding。
4. 将普通模式三步卡片、联动页、按钮组、表格和 JSON 面板统一为低留白样式。
5. 更新布局测试断言和版本文档。

## 关键决策

- 不改功能逻辑，只改视觉密度和布局尺寸。
- 不引入前端构建链，不改静态 HTML/CSS/JS 结构。
- 保留 MCP/导出/隐私门禁等安全交互。
- 参考图只抽象为“紧凑桌面工具”风格，不复制具体品牌或图标。

## 修改清单

- 全局 body 字号改为 13px。
- 专业模式布局改为 `188px minmax(360px, 1fr) minmax(300px, 30vw)`。
- 控件高度统一到约 32px。
- 面板、按钮、输入框和表格统一 4px 低圆角。
- 普通模式大标题、卡片高度、按钮组和搜索表单压缩。
- 包版本推进到 `0.37.0`。

## 测试与验证

已运行：

```powershell
python -m ruff check src\threadvault\personal_ui.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py
node -e "<extract APP_JS from personal_ui.py and compile with new Function(...)>"
rg -n -- "--control-height: 32px|--radius: 4px|0\.37\.0" src tests README.md docs pyproject.toml
```

结果：

- ruff passed。
- `APP_JS` 语法检查 passed。
- 关键 CSS token 和版本号静态检查 passed。
- focused pytest 已尝试，但当前受限运行环境无法收集测试：`py` 不在 PATH，bundled Python 与默认 Conda Python 缺少 `attrs`，项目 Python 可执行文件被 sandbox 拒绝执行。
- 浏览器截图检查已尝试，但当前 bundled Node 的 `playwright` 缺少 `playwright-core`，无法启动截图。

## 文档更新

- `README.md` 更新版本线。
- `docs/THREADVAULT_USAGE_MANUAL.md` 增加紧凑工具式布局说明。
- `docs/CHANGELOG.md` 新增 `0.37.0` 条目。
- `docs/PROGRESS.md` 更新当前版本、最近完成事项和开发记录。
- `docs/DOC_INDEX.md` 登记本轮记录。

## 风险与遗留问题

- 紧凑样式需要浏览器截图确认，尤其是移动宽度和中文长文本。
- 过度紧凑可能降低大屏留白舒适度；目前优先满足本地工具高密度操作。

## 下一步计划

- 运行 focused UI 测试和 ruff。
- 若环境允许，启动本地 UI 并截图检查桌面/移动宽度。

## 状态

completed
