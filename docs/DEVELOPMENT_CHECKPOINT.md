# Development checkpoint

- Version: `0.1.7`
- Updated: 2026-08-10 Europe/Zurich
- Status: 0.1.7 功能保持不变，源码仓库规范化与质量基线已完成。

## 源码仓库规范化

- 建立源码、用户运行数据、预览程序、永久测试源码和临时开发产物的明确边界。
- `runtime-data/`、`preview-builds/`、生成的 sidecar、依赖目录和 `development-artifacts/` 均排除版本控制；现有用户数据库、模型和导出文件未删除。
- 永久回归测试恢复到 `tests/agent/`，测试报告和临时数据库统一写入 `development-artifacts/`。
- 新增统一质量检查 `scripts/check.ps1` / `pnpm check`，不生成安装包。
- 补齐 `.editorconfig`、`.gitattributes`、私有许可证、开发说明、安全说明、仓库目录文档和 Python 精确依赖锁。
- 桌面端版本由 Vite 从应用清单注入，Python User-Agent 读取包版本；版本检查覆盖全部 7 个版本来源。
- Tauri 运行数据路径不再编译进开发机绝对路径：仓库内预览继续使用项目根目录 `runtime-data/`，移出的便携程序使用程序同级目录。
- `/health` 不再暴露本地数据库绝对路径。

### 当前验证结果

- Python：29 项永久回归测试通过。
- Ruff：通过。
- 前端 TypeScript 与 Vite 生产构建：通过；保留 Mermaid 大分块提示。
- Rust 格式检查与 Clippy `-D warnings`：通过。
- Python `pip check` 与 7 个版本来源一致性：通过。
- 本地 Python 可编辑包元数据已由 0.1.5 对齐到 0.1.7。
- 未生成安装包；原有 `preview-builds/0.1.7/` 预览文件保留。

## 0.1.7 完成内容

- 移除尚未投入使用的视频抽帧、视觉模型配置和视觉能力状态；课程理解继续基于网页元数据、字幕或本地音轨转写。
- 在主界面左上方增加与侧栏视觉风格协调的捐赠卡，指向 `https://buymeacoffee.com/jeromerlon`，并支持中、英、德三语。
- 开场动画内嵌版本号更新为 `0.1.7`，保留原 50 FPS 苏醒动画与透明背景。
- 前端构建固定使用 Vite runner 配置加载方式，避免 Windows 沙箱环境打包配置文件时越界扫描。
- 桌面 Release 明确定义并启用 `custom-protocol`，确保便携预览内嵌前端资源，不会尝试连接开发服务器 `127.0.0.1:1420`。
- 捐赠卡在 Tauri 中通过白名单命令调用 Windows 默认浏览器；不再依赖 WebView 对 `target="_blank"` 的处理。
- pnpm 项目版本与 Conda 环境中实际安装的 `11.20.0` 对齐。

## 验证快照

- Python：45 项测试通过；仅有上游 Starlette/httpx 弃用警告。
- Ruff：通过。
- TypeScript：通过。
- Vite 生产构建：通过；仅保留 Mermaid 大分块提示。
- Rust Clippy：通过，启用 `-D warnings`。
- 版本一致性：所有应用清单均为 `0.1.7`。
- 本地 UI：捐赠链接、三语文案、能力设置移除项与开场画面均已验收。
- Cargo release：通过；未生成安装包。

## 便携开发预览

- `preview-builds/0.1.7/study-assistant.exe`
- `preview-builds/0.1.7/study-assistant-agent.exe`

两个文件必须放在同一目录。该目录是开发预览，不是正式安装包。

## 清理与数据安全

- 已清除历史测试证据、日志、截图、工具缓存、旧版本构建目标与本轮编译中间文件。
- 保留 `runtime-data/`，其中的任务数据库、课程媒体、导出、语义索引和本地模型均未删除。
- 保留 `node_modules/` 作为当前开发依赖；它不会进入 Tauri 发布包。

## 安全续接点

0.1.7 已完成。后续中断后可说：**“从上一次的断点继续开发”**。
