# Study Assistant

[中文](#中文) · [English](#english) · [Deutsch](#deutsch) · [开发与构建](#开发环境)

[下载 Windows x64 安装包](https://github.com/jeromerlon99-svg/study-assistant-releases/releases/tag/v0.1.7) · [中英德使用教程 (PDF)](Study_Assistant_0.1.7_Tutorial_ZH_EN_DE.pdf) · [版本记录 / Changelog](CHANGELOG.md)

> “直心是道场，无虚伪故” ——《维摩诘经》。愿我们真诚。

## 中文

Study Assistant 是一款面向公开课的 Windows 桌面学习 AI Agent。添加课程链接后，它优先读取字幕，缺少字幕时在本机转写音频，再生成带时间戳的速学笔记。你可以按节查看和导出笔记，也可以就已处理的课程内容提问。

1. 在 [v0.1.7 预发布页](https://github.com/jeromerlon99-svg/study-assistant-releases/releases/tag/v0.1.7) 下载 **Study.Assistant_0.1.7_x64-setup.exe**，安装后打开应用。
2. 在「智能能力设置」填写兼容服务的 API Base URL、API Key 和模型名称，保存并测试。每次完全退出后需重新填写 Key。
3. 新建学习任务，添加课程链接并开始处理。首次需要本地转写或语义检索时，程序可能下载模型。

0.1.7 安装包尚未签名，Windows SmartScreen 可能提示「未知发布者」。应用源码已公开在 `main`，可按 [LICENSE](LICENSE) 查阅和本地编译试用。旧标签 `v0.1.7` 早于源码公开，所以该 Release 自动生成的源码压缩包只包含当时的 README。

如果它对你有帮助，欢迎 [请我喝杯咖啡](https://buymeacoffee.com/jeromerlon)，支持修复 bug 和维护项目。

## English

Study Assistant is a Windows desktop AI agent for public online courses. Give it a course link to generate timestamped notes from captions or local audio transcription. Read and export notes by lesson, or ask questions across the lessons you have processed.

1. Download **Study.Assistant_0.1.7_x64-setup.exe** from the [v0.1.7 pre-release](https://github.com/jeromerlon99-svg/study-assistant-releases/releases/tag/v0.1.7), install it, and open the app.
2. In **AI Settings**, enter your compatible provider’s API base URL, API key, and model name. Save and test the settings. Re-enter the key after each full exit.
3. Create a learning task, add a course link, and start processing. The app may download local models the first time you use transcription or semantic search.

The 0.1.7 pre-release installer is unsigned, so Windows SmartScreen may show an unknown publisher warning. The application source is available on `main` under [LICENSE](LICENSE), which permits inspection and local evaluation. The `v0.1.7` tag predates source publication, so its automatically generated archives contain the README from that point in time.

If Study Assistant helps you, [support the project](https://buymeacoffee.com/jeromerlon) to help fund bug fixes and maintenance.

## Deutsch

Study Assistant ist ein KI-Agent für Windows, der beim Lernen mit öffentlichen Onlinekursen hilft. Gib einen Kurslink ein und erhalte Notizen mit Zeitmarken aus Untertiteln oder einer lokalen Audiotranskription. Du kannst Notizen pro Lektion lesen und exportieren oder Fragen zu den verarbeiteten Lektionen stellen.

1. Lade **Study.Assistant_0.1.7_x64-setup.exe** von der [Vorabversion v0.1.7](https://github.com/jeromerlon99-svg/study-assistant-releases/releases/tag/v0.1.7) herunter, installiere die App und öffne sie.
2. Trage in den **KI-Einstellungen** die API-Basis-URL, den API-Schlüssel und den Modellnamen deines kompatiblen Anbieters ein. Speichere und teste die Einstellungen. Nach dem vollständigen Beenden musst du den Schlüssel erneut eingeben.
3. Erstelle eine Lernaufgabe, füge einen Kurslink hinzu und starte die Verarbeitung. Für die erste Transkription oder semantische Suche lädt die App bei Bedarf lokale Modelle herunter.

Das Installationsprogramm der Vorabversion 0.1.7 ist unsigniert. Windows SmartScreen kann deshalb einen unbekannten Herausgeber melden. Der Anwendungsquellcode steht unter [LICENSE](LICENSE) auf `main` zur Einsicht und zum lokalen Testen bereit. Der Tag `v0.1.7` stammt aus der Zeit vor der Veröffentlichung des Quellcodes. Seine automatisch erzeugten Archive enthalten die damalige README-Datei.

Wenn dir Study Assistant hilft, kannst du [das Projekt unterstützen](https://buymeacoffee.com/jeromerlon) und so zu Fehlerbehebungen und Wartung beitragen.

## 当前能力边界

- 只处理用户有权访问的公开内容，不绕过 DRM、登录、付费墙或站点访问控制。
- 0.1.7 仍以字幕或音轨理解课程，不读取视频画面、板书和幻灯片；当前界面不提供未启用的视觉模型配置。
- 本地转写当前固定使用 CPU `int8` 推理；`small` 适合作为默认，`medium` 和 `large-v3` 准确率更高但下载更大、运行更慢。
- 文本模型提供方必须兼容 `chat/completions`。语音不会上传到云端转写 API；faster-whisper 通过随程序打包的 PyAV 解码音轨。
- 问答不调用搜索引擎或外部检索 API。模型内部知识不是实时联网结果，涉及最新信息时应另行核实。

## 开发环境

系统依赖：Windows 10/11、Microsoft C++ Build Tools、Windows SDK、Rust MSVC 工具链和 WebView2。Conda 环境由 [environment.yml](./environment.yml) 统一描述；Python 包继续以 `services/agent/pyproject.toml` 为版本来源，Node 包由 `pnpm-lock.yaml` 锁定。

```powershell
conda env create -f environment.yml
conda activate study-assistant
pnpm install --frozen-lockfile
```

### 开发运行

```powershell
conda activate study-assistant
pnpm tauri dev
```

Tauri 开发模式直接启动 Conda 环境中的 Python Agent，使用开发环境提供的 FFmpeg。若首选端口 `8765` 被占用，会选择一个空闲的本机端口。浏览器单独调试前端时，可分别运行：

```powershell
pnpm agent:dev
pnpm dev
```

### 配置智能 API

在主界面左下角打开“智能能力设置”，填写：

- API Base URL；
- API Key（只在当前运行期间驻留内存，程序重启后必须重新填写）；
- 文本模型；
- Kimi K3 可选的推理强度（默认 `low`，适合长课程的速度与成本平衡）；
- 本地 faster-whisper 模型（`small`、`medium` 或 `large-v3`）；

语义检索不使用这里填写的文本模型 API。程序固定使用本地 `intfloat/multilingual-e5-small`，首次启动时自动下载，之后自动为全部已转写课程维护索引。设置页只显示其状态，不提供开关、模型输入或删除入口。
模型来源、固定工件版本、许可和校验值见 [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md)。

保存时会执行真实连接测试。课程内容在生成速学速记或回答时会发送给所配置的文本模型提供方；未配置模型、未填写本次运行的 Key 或测试失败时，程序会阻止开始智能处理并提示修复，不再把基础摘录冒充为已完成的速学笔记。

由于 API Key 按要求不会跨启动保存，每次重新打开程序后都要先点击“配置 API”，重新输入 Key 并看到连接测试成功。已有课程文字不会因此丢失；可在“管理任务”中直接重新生成速学速记，无需再次下载或转写课程。

#### Kimi K3 配置

Kimi K3 已有专门兼容路径。推荐设置如下：

- API Base URL：使用 Kimi 开放平台为账户提供的地址（官方国际端点为 `https://api.moonshot.ai/v1`）；
- 文本模型：`kimi-k3`；
- 推理强度：先使用 `low`，需要更深推理时再切换为 `high` 或 `max`；
- 本地转写模型：建议先使用 `small`；它与 Kimi API 相互独立。

程序会针对 `kimi-k3` 自动使用 `max_completion_tokens` 和 `reasoning_effort`，并省略该模型不接受的 `temperature`。无字幕课程由本地 faster-whisper 转写，不需要额外的转写 API 或 Key。参见 [Kimi K3 快速开始](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart) 与 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)。

Kimi K3 的短连接测试和正式生成使用不同的等待策略：连接测试最长等待 120 秒，课程笔记等长生成请求最长等待 600 秒。模型提前返回时会立即继续；若仍然超时，界面会明确显示读取超时，并保留已完成的课程转写供重新生成。

#### 本地转写模型

- 有可读字幕时不会加载或下载 Whisper 模型。
- 无字幕课程首次开始记录时，模型会下载到项目目录的 `runtime-data\models\faster-whisper\<模型名>\`。
- 下载完成后同一模型会永久保留在本地，后续可离线转写；可以通过删除对应模型目录释放磁盘空间。
- 模型下载失败时任务会保留错误和断点，检查网络或磁盘空间后可以继续。

### 验证与清理

永久回归测试源码保存在 `tests/`，属于规范源码仓库的一部分，不应在发布清理时删除。测试报告、临时数据库、截图、日志、编译缓存和 PyInstaller 工作目录统一写入可整体删除的 `development-artifacts/`。运行完整质量检查：

```powershell
pnpm check
```

该命令依次检查版本一致性、Python 依赖、Ruff、pytest、前端生产构建、Rust 格式和 Clippy；不会生成安装包。

### 构建发布版

```powershell
pnpm release:build
```

该命令会依次打包 Python Agent、下载并校验固定版本的 LGPL FFmpeg/FFprobe，再传入发布专用配置生成单文件 NSIS 安装器。安装包位于 `apps/desktop/src-tauri/target/release/bundle/nsis/`（如果设置了 `CARGO_TARGET_DIR`，则在对应的目标目录下）。发布到 GitHub 时将 EXE 和教程添加为 Release 附件。

如果固定的 FFmpeg 构建在上游下架，可以将同名、同 SHA-256 的原始 ZIP 放入 `development-artifacts/ffmpeg/` 后重试。更新构建版本时，须同步更新校验值和 [第三方声明](THIRD_PARTY_NOTICES.md)。

## 数据位置

正式运行数据和用户导出文件统一保存在 `runtime-data\`。程序位于源码仓库或其 `preview-builds` 子目录时会自动使用项目根目录的数据；便携程序移到其他目录后会使用程序同级的 `runtime-data\`。也可用 `STUDY_ASSISTANT_DATA_DIR` 显式覆盖：

- `study-assistant.db`：任务隔离的 SQLite 数据库；
- `media/`：必要时下载的课程音轨；
- `exports/`：导出的 Markdown；
- `models/faster-whisper/`：首次使用时下载并长期复用的本地转写模型；
- `models/embedding/multilingual-e5-small/`：0.1.5 首次启动时自动下载并校验的内置多语言语义模型；
- `provider.json`：非敏感模型名称和端点；
- `preferences.json`：界面语言等非敏感偏好；
- `backups/`：版本迁移前的一致性数据库备份；
- `agent.log`：发布版本地 Agent 日志。

删除单个学习任务时，会删除该任务的数据库记录、媒体缓存、对应导出文件和语义索引，但不会删除可供其他任务复用的 faster-whisper 或 E5 模型。API Key 不写入上述任何文件，也不写入系统凭据库或日志。

早期开发版曾使用 `%LOCALAPPDATA%\StudyAssistant`。当前版本默认使用上面的 `runtime-data\` 规则。

架构与状态机详见 [docs/ARCHITECTURE_ZH.md](./docs/ARCHITECTURE_ZH.md)，当前开发断点见 [docs/DEVELOPMENT_CHECKPOINT.md](./docs/DEVELOPMENT_CHECKPOINT.md)。
