# Study Assistant

[中文](#中文) · [English](#english) · [Deutsch](#deutsch)

[中文完整说明](#当前能力边界) · [English guide](#english-guide) · [Deutsche Anleitung](#deutsche-anleitung)

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
2. In **AI capability settings**, enter your compatible provider’s API base URL, API key, and model name. Save and test the settings. Re-enter the key after each full exit.
3. Create a learning task, add a course link, and start processing. The app may download local models the first time you use transcription or semantic search.

The 0.1.7 pre-release installer is unsigned, so Windows SmartScreen may show an unknown publisher warning. The application source is available on `main` under [LICENSE](LICENSE), which permits inspection and local evaluation. The `v0.1.7` tag predates source publication, so its automatically generated archives contain the README from that point in time.

If Study Assistant helps you, [support the project](https://buymeacoffee.com/jeromerlon) to help fund bug fixes and maintenance.

[Continue to the English guide](#english-guide) for limitations, API setup, development, and data storage.

## Deutsch

Study Assistant ist ein KI-Agent für Windows, der beim Lernen mit öffentlichen Onlinekursen hilft. Gib einen Kurslink ein und erhalte Notizen mit Zeitmarken aus Untertiteln oder einer lokalen Audiotranskription. Du kannst Notizen pro Lektion lesen und exportieren oder Fragen zu den verarbeiteten Lektionen stellen.

1. Lade **Study.Assistant_0.1.7_x64-setup.exe** von der [Vorabversion v0.1.7](https://github.com/jeromerlon99-svg/study-assistant-releases/releases/tag/v0.1.7) herunter, installiere die App und öffne sie.
2. Trage unter **KI-Fähigkeiten** die API-Basis-URL, den API-Schlüssel und den Modellnamen deines kompatiblen Anbieters ein. Speichere und teste die Einstellungen. Nach dem vollständigen Beenden musst du den Schlüssel erneut eingeben.
3. Erstelle eine Lernaufgabe, füge einen Kurslink hinzu und starte die Verarbeitung. Für die erste Transkription oder semantische Suche lädt die App bei Bedarf lokale Modelle herunter.

Das Installationsprogramm der Vorabversion 0.1.7 ist unsigniert. Windows SmartScreen kann deshalb einen unbekannten Herausgeber melden. Der Anwendungsquellcode steht unter [LICENSE](LICENSE) auf `main` zur Einsicht und zum lokalen Testen bereit. Der Tag `v0.1.7` stammt aus der Zeit vor der Veröffentlichung des Quellcodes. Seine automatisch erzeugten Archive enthalten die damalige README-Datei.

Wenn dir Study Assistant hilft, kannst du [das Projekt unterstützen](https://buymeacoffee.com/jeromerlon) und so zu Fehlerbehebungen und Wartung beitragen.

Die [deutsche Anleitung](#deutsche-anleitung) erklärt die Funktionsgrenzen, die API-Einrichtung, die Entwicklung und den Speicherort der Daten.

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

## English guide

### Current limitations

- Study Assistant processes public content you are authorized to access. It does not bypass DRM, login requirements, paywalls, or access controls.
- Version 0.1.7 uses captions or audio to understand a course. It does not analyze video frames, board writing, or slides. Visual model settings are unavailable in this version.
- Local transcription uses CPU inference in `int8` mode. `small` is a good default. `medium` and `large-v3` can improve accuracy at the cost of larger downloads and slower transcription.
- The text model provider must support `chat/completions`. faster-whisper decodes the audio on your device using the bundled PyAV library. No audio is sent to a cloud transcription API.
- Course Q&A uses course records and the model’s existing knowledge. It does not use a live search engine or an external retrieval API. Check time-sensitive information separately.

### Development environment

Development requires Windows 10 or 11, Microsoft C++ Build Tools, the Windows SDK, the Rust MSVC toolchain, and WebView2. [environment.yml](./environment.yml) defines the Conda environment. Python package requirements are in `services/agent/pyproject.toml`, and Node dependencies are locked in `pnpm-lock.yaml`.

```powershell
conda env create -f environment.yml
conda activate study-assistant
pnpm install --frozen-lockfile
```

#### Run in development mode

```powershell
conda activate study-assistant
pnpm tauri dev
```

Tauri development mode starts the Python Agent from the Conda environment and uses the FFmpeg provided by that environment. If the preferred port `8765` is in use, it chooses another available local port. To debug the frontend in a browser, run these commands in separate terminals:

```powershell
pnpm agent:dev
pnpm dev
```

#### Configure the AI API

Open **AI capability settings** in the lower-left corner of the main window and enter or select the following:

- API Base URL
- API key, kept in memory for the current session and required again after restart
- Text model
- Optional reasoning effort for Kimi K3. The default `low` balances speed and cost on long courses.
- Local faster-whisper model (`small`, `medium`, or `large-v3`)

Semantic search uses the built-in local model `intfloat/multilingual-e5-small`. The app downloads it automatically on first startup and then keeps the index up to date for all transcribed lessons. Settings show the model status without controls to disable, replace, or remove the model. See [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md) for the model source, pinned artifact version, license, and checksum.

Saving the settings sends a test request to the provider. The app sends course text to the configured text model provider when it generates notes or answers questions. If the model or session key is missing, or the test fails, the app prompts you to fix the settings before it can generate notes or answer questions.

After a full restart, open **Configure API**, enter your key, and check that the connection test passes. Existing transcripts stay on your device. You can regenerate notes from **Manage task** without downloading or transcribing the lesson again.

##### Kimi K3 configuration

- API Base URL. Use the address your account provides. The international endpoint is `https://api.moonshot.ai/v1`.
- Text model. Enter `kimi-k3`.
- Reasoning effort. Start with `low` and switch to `high` or `max` if you need deeper reasoning.
- Local transcription model. Start with `small`. Transcription runs independently of the Kimi API.

For `kimi-k3`, the app sends `max_completion_tokens` and `reasoning_effort` and omits the unsupported `temperature` parameter. For lessons without captions, local faster-whisper handles transcription without an extra API or key. See the [Kimi K3 quickstart](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart) and [faster-whisper documentation](https://github.com/SYSTRAN/faster-whisper).

The Kimi K3 connection test waits up to 120 seconds. Longer generation requests, such as course notes, wait up to 600 seconds. The app continues as soon as the model responds. If a request times out, the app reports the timeout and keeps the completed transcript so you can regenerate the notes later.

##### Local transcription models

- The app uses readable captions when available and downloads a Whisper model only when needed for local transcription.
- The first time you process a lesson without captions, the app downloads the selected model to `runtime-data\models\faster-whisper\<model-name>\`.
- The downloaded model can be reused for offline transcription. To free space, delete the corresponding model directory.
- If the download fails, the app keeps the error and task progress. Check your network connection or disk space before resuming.

#### Checks and cleanup

Keep the regression-test source in `tests/`. The app’s test reports, temporary databases, screenshots, logs, build caches, and PyInstaller working files go in `development-artifacts/`, which can be deleted as a whole.

```powershell
pnpm check
```

This command runs version and Python dependency checks, Ruff, pytest, the production frontend build, Rust formatting checks, and Clippy. Installer creation is a separate step.

#### Build the Windows installer

```powershell
pnpm release:build
```

This command packages the Python Agent, downloads and verifies the pinned LGPL FFmpeg and FFprobe binaries, then builds a single-file NSIS installer with the release configuration. The output is in `apps/desktop/src-tauri/target/release/bundle/nsis/`, or under `release/bundle/nsis/` in your configured `CARGO_TARGET_DIR`. Attach the EXE and tutorial to a GitHub Release when distributing them.

If the pinned FFmpeg build is withdrawn upstream, put the original ZIP with the same filename and SHA-256 in `development-artifacts/ffmpeg/` before retrying. When updating the pinned build, update the checksum and [third-party notices](THIRD_PARTY_NOTICES.md) together.

### Data storage

The app keeps its runtime data and exports in `runtime-data\`. When it runs from the source repository or its `preview-builds` directory, it uses the folder at the repository root. A portable executable kept elsewhere uses a `runtime-data\` folder next to the executable. Override this location with `STUDY_ASSISTANT_DATA_DIR`.

- `study-assistant.db` stores each task’s data separately in SQLite.
- `media/` stores course audio downloaded when needed.
- `exports/` stores Markdown exports.
- `models/faster-whisper/` stores local transcription models downloaded for reuse.
- `models/embedding/multilingual-e5-small/` stores the built-in multilingual semantic model, downloaded and verified automatically.
- `provider.json` stores non-secret model names and endpoints.
- `preferences.json` stores non-secret preferences such as the interface language.
- `backups/` stores consistent database backups created before migrations.
- `agent.log` is the local Agent log for release builds.

Deleting a learning task removes its database records, cached media, exports, and semantic index. Shared Whisper and E5 model files stay available for other tasks. The API key stays in memory for the session. The app does not write it to disk, the system credential store, or logs.

Earlier development builds used `%LOCALAPPDATA%\StudyAssistant`. The current default follows the `runtime-data\` rules above.

See the [architecture and state machine](./docs/ARCHITECTURE_ZH.md) and the [development checkpoint](./docs/DEVELOPMENT_CHECKPOINT.md) for more detail. Both documents are in Chinese.

## Deutsche Anleitung

### Aktuelle Funktionsgrenzen

- Study Assistant verarbeitet öffentliche Inhalte, auf die du zugreifen darfst. Die App umgeht weder DRM noch Anmeldepflichten, Bezahlschranken oder andere Zugriffsbeschränkungen.
- Version 0.1.7 wertet Untertitel oder die Tonspur eines Kurses aus. Videobilder, Tafelanschriften und Folien werden nicht analysiert. Einstellungen für Bildmodelle sind in dieser Version nicht verfügbar.
- Die lokale Transkription läuft auf der CPU im `int8`-Modus. `small` eignet sich als Standardeinstellung. `medium` und `large-v3` können genauer transkribieren, benötigen aber größere Downloads und mehr Rechenzeit.
- Der Anbieter des Textmodells muss `chat/completions` unterstützen. faster-whisper dekodiert den Ton lokal mit der mitgelieferten PyAV-Bibliothek. Die App sendet keine Audiodaten an eine Cloud-Transkriptions-API.
- Bei Kursfragen nutzt die App die Kursaufzeichnungen und das vorhandene Modellwissen. Sie verwendet keine Live-Websuche und keine externe Such-API. Prüfe zeitabhängige Angaben bei Bedarf separat.

### Entwicklungsumgebung

Für die Entwicklung brauchst du Windows 10 oder 11, die Microsoft C++ Build Tools, das Windows SDK, die Rust-Toolchain für MSVC und WebView2. [environment.yml](./environment.yml) definiert die Conda-Umgebung. Die Python-Paketanforderungen stehen in `services/agent/pyproject.toml`. Die Node-Abhängigkeiten sind in `pnpm-lock.yaml` festgeschrieben.

```powershell
conda env create -f environment.yml
conda activate study-assistant
pnpm install --frozen-lockfile
```

#### Im Entwicklungsmodus starten

```powershell
conda activate study-assistant
pnpm tauri dev
```

Im Entwicklungsmodus startet Tauri den Python-Agenten aus der Conda-Umgebung und verwendet das dort installierte FFmpeg. Ist der bevorzugte Port `8765` belegt, wird ein anderer freier lokaler Port gewählt. Um die Oberfläche im Browser zu testen, führe diese Befehle in getrennten Terminals aus:

```powershell
pnpm agent:dev
pnpm dev
```

#### KI-API einrichten

Öffne unten links im Hauptfenster **KI-Fähigkeiten**. Dort kannst du Folgendes eingeben oder auswählen:

- API-Basis-URL
- API-Schlüssel, der für die aktuelle Sitzung im Arbeitsspeicher bleibt und nach dem Neustart erneut eingegeben werden muss
- Textmodell
- Optionaler Reasoning-Aufwand für Kimi K3. Die Standardeinstellung `low` hält bei langen Kursen Rechenzeit und Kosten niedrig.
- Lokales faster-whisper-Modell (`small`, `medium` oder `large-v3`)

Die semantische Suche verwendet das integrierte lokale Modell `intfloat/multilingual-e5-small`. Die App lädt es beim ersten Start automatisch herunter und hält danach den Suchindex für alle transkribierten Lektionen aktuell. Die Einstellungen zeigen den Modellstatus an. Das Modell lässt sich dort weder deaktivieren noch austauschen oder entfernen. Quelle, festgelegte Version, Lizenz und Prüfsumme stehen in [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

Beim Speichern sendet die App eine Testanfrage an den Anbieter. Beim Erstellen von Notizen und Beantworten von Fragen übermittelt sie Kurstext an den eingerichteten Textmodellanbieter. Fehlt das Modell oder der aktuelle API-Schlüssel oder schlägt der Test fehl, fordert die App dich auf, die Einstellungen zu korrigieren.

Öffne nach einem vollständigen Neustart **API konfigurieren**, gib deinen Schlüssel ein und prüfe, ob der Verbindungstest erfolgreich ist. Vorhandene Transkripte bleiben auf deinem Gerät. Über **Aufgabe verwalten** kannst du Notizen mit diesen Transkripten neu erstellen.

##### Kimi K3 einrichten

- API-Basis-URL. Verwende die Adresse aus deinem Kimi-Konto. Der internationale Endpunkt lautet `https://api.moonshot.ai/v1`.
- Textmodell. Gib `kimi-k3` ein.
- Reasoning-Aufwand. Beginne mit `low`. Für komplexere Aufgaben kannst du `high` oder `max` wählen.
- Lokales Transkriptionsmodell. Beginne mit `small`. Die Transkription läuft unabhängig von der Kimi-API.

Für `kimi-k3` sendet die App `max_completion_tokens` und `reasoning_effort`. Der nicht unterstützte Parameter `temperature` wird weggelassen. Bei Lektionen ohne Untertitel übernimmt faster-whisper die lokale Transkription ohne weitere API und ohne zusätzlichen Schlüssel. Siehe die [Kimi-K3-Kurzanleitung](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart) und die [faster-whisper-Dokumentation](https://github.com/SYSTRAN/faster-whisper).

Der Kimi-K3-Verbindungstest wartet bis zu 120 Sekunden. Für längere Anfragen wie das Erstellen von Kursnotizen wartet die App bis zu 600 Sekunden. Sobald das Modell antwortet, setzt sie die Verarbeitung fort. Bei einer Zeitüberschreitung zeigt sie eine Meldung an und behält das fertige Transkript, damit du später erneut Notizen erstellen kannst.

##### Lokale Transkriptionsmodelle

- Wenn lesbare Untertitel vorliegen, verwendet die App diese. Ein Whisper-Modell wird erst heruntergeladen, wenn eine lokale Transkription nötig ist.
- Beim ersten Verarbeiten einer Lektion ohne Untertitel wird das ausgewählte Modell nach `runtime-data\models\faster-whisper\<Modellname>\` heruntergeladen.
- Das heruntergeladene Modell kann für die Offline-Transkription wiederverwendet werden. Um Speicherplatz freizugeben, kannst du das zugehörige Modellverzeichnis löschen.
- Schlägt der Download fehl, bleiben die Fehlermeldung und der bisherige Aufgabenfortschritt erhalten. Prüfe die Internetverbindung oder den freien Speicherplatz vor dem Fortsetzen.

#### Prüfungen und Bereinigung

Der Quellcode der Regressionstests gehört in `tests/` und bleibt im Repository. Testberichte, temporäre Datenbanken, Bildschirmfotos, Protokolle, Build-Caches und PyInstaller-Arbeitsdateien liegen in `development-artifacts/`. Dieses Verzeichnis lässt sich vollständig löschen.

```powershell
pnpm check
```

Der Befehl prüft die Versionsangaben und Python-Abhängigkeiten und führt Ruff, pytest, den Produktions-Build der Oberfläche, die Rust-Formatprüfung und Clippy aus. Das Erstellen des Installationsprogramms ist ein separater Schritt.

#### Windows-Installationsprogramm bauen

```powershell
pnpm release:build
```

Der Befehl verpackt den Python-Agenten, lädt die festgelegten LGPL-Versionen von FFmpeg und FFprobe herunter und prüft deren Integrität. Anschließend baut er mit der Release-Konfiguration ein NSIS-Installationsprogramm als einzelne Datei. Die Ausgabe liegt in `apps/desktop/src-tauri/target/release/bundle/nsis/` oder unter `release/bundle/nsis/` im konfigurierten `CARGO_TARGET_DIR`. Zur Veröffentlichung kannst du die EXE und die Anleitung als Anhänge zu einem GitHub Release hinzufügen.

Falls der festgelegte FFmpeg-Build beim Anbieter nicht mehr verfügbar ist, lege vor dem erneuten Versuch die ursprüngliche ZIP-Datei mit unverändertem Namen und identischer SHA-256-Prüfsumme in `development-artifacts/ffmpeg/` ab. Aktualisiere bei einem Versionswechsel sowohl die Prüfsumme als auch die [Hinweise zu Drittkomponenten](THIRD_PARTY_NOTICES.md).

### Speicherort der Daten

Die App speichert Laufzeitdaten und Exporte in `runtime-data\`. Startest du sie aus dem Quellcode-Repository oder dessen Unterordner `preview-builds`, verwendet sie das Verzeichnis am Repository-Stamm. Eine portable Programmdatei an einem anderen Ort verwendet ein `runtime-data\`-Verzeichnis neben der Programmdatei. Mit `STUDY_ASSISTANT_DATA_DIR` kannst du diesen Speicherort überschreiben.

- `study-assistant.db` speichert die Daten jeder Aufgabe getrennt in einer SQLite-Datenbank.
- `media/` enthält bei Bedarf heruntergeladene Kurstonspuren.
- `exports/` enthält Markdown-Exporte.
- `models/faster-whisper/` enthält heruntergeladene lokale Transkriptionsmodelle zur Wiederverwendung.
- `models/embedding/multilingual-e5-small/` enthält das integrierte mehrsprachige Suchmodell, das die App automatisch herunterlädt und überprüft.
- `provider.json` enthält nicht vertrauliche Modellnamen und Endpunkte.
- `preferences.json` enthält nicht vertrauliche Einstellungen wie die Sprache der Oberfläche.
- `backups/` enthält konsistente Datenbanksicherungen, die vor Migrationen erstellt werden.
- `agent.log` enthält das lokale Protokoll des Agenten in Release-Builds.

Beim Löschen einer Lernaufgabe entfernt die App deren Datenbankeinträge, zwischengespeicherte Medien, Exporte und Suchindex. Gemeinsam genutzte Whisper- und E5-Modelle bleiben für andere Aufgaben verfügbar. Der API-Schlüssel bleibt für die Sitzung im Arbeitsspeicher. Die App schreibt ihn weder auf den Datenträger noch in die Anmeldeinformationsverwaltung oder in Protokolle.

Ältere Entwicklungsversionen nutzten `%LOCALAPPDATA%\StudyAssistant`. Heute gilt standardmäßig die oben beschriebene Regel für `runtime-data\`.

Weitere Details findest du unter [Architektur und Zustandsmodell](./docs/ARCHITECTURE_ZH.md) und [Entwicklungsstand](./docs/DEVELOPMENT_CHECKPOINT.md). Beide Dokumente sind auf Chinesisch.
