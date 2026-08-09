import type { UiLanguage } from "./types";

type Entry = [zh: string, en: string, de: string];

const ENTRIES: Entry[] = [
  ["课程理解工作台", "Course learning workspace", "Kurs-Lernarbeitsplatz"],
  ["添加公开课", "Add public course", "Öffentlichen Kurs hinzufügen"],
  ["学习任务", "Learning tasks", "Lernaufgaben"],
  ["智能能力设置", "AI capability settings", "KI-Fähigkeiten"],
  ["本地 Agent 已连接", "Local Agent connected", "Lokaler Agent verbunden"],
  ["正在连接本地 Agent", "Connecting to Local Agent", "Lokaler Agent wird verbunden"],
  ["管理任务", "Manage task", "Aufgabe verwalten"],
  ["查看提示词", "View prompts", "Prompts anzeigen"],
  ["重新检查", "Recheck", "Erneut prüfen"],
  ["开始记录", "Start processing", "Verarbeitung starten"],
  ["暂停", "Pause", "Pausieren"],
  ["继续", "Resume", "Fortsetzen"],
  ["重新生成笔记", "Regenerate notes", "Notizen neu erstellen"],
  ["课程目录", "Course lessons", "Kurslektionen"],
  ["添加下一节", "Add lesson", "Lektion hinzufügen"],
  ["当前课程来源", "Current course source", "Aktuelle Kursquelle"],
  ["课程来源", "Course source", "Kursquelle"],
  ["删除本节", "Delete lesson", "Lektion löschen"],
  ["课程速学", "Rapid learning", "Schnelllernen"],
  ["详细介绍与速学速记", "Detailed guide and rapid notes", "Detailübersicht und Schnellnotizen"],
  ["导出速学笔记", "Export notes", "Notizen exportieren"],
  ["课程问答", "Course Q&A", "Kursfragen"],
  ["向助手提问", "Ask the assistant", "Assistenten fragen"],
  ["新对话", "New chat", "Neuer Chat"],
  ["请先配置并通过 API 连接测试", "Configure and test the API first", "API zuerst konfigurieren und testen"],
  ["从课程内容开始", "Start with course content", "Mit dem Kursinhalt beginnen"],
  ["正在核对课程证据…", "Checking course evidence…", "Kursbelege werden geprüft…"],
  ["课程优先 · 模型知识补充", "Course first · model knowledge supplement", "Kurs zuerst · Ergänzung durch Modellwissen"],
  ["课程证据优先；未覆盖部分由当前模型知识补充，未经实时联网核实。", "Course evidence first; uncovered points are supplemented from the current model's knowledge without real-time web verification.", "Kursbelege zuerst; nicht abgedeckte Punkte werden durch das Wissen des aktuellen Modells ergänzt und nicht in Echtzeit im Web geprüft."],
  ["待开始", "Not started", "Nicht gestartet"],
  ["正在检查", "Checking", "Wird geprüft"],
  ["正在观看", "Processing", "In Verarbeitung"],
  ["正在转写", "Transcribing", "Transkription"],
  ["生成速学速记", "Generating notes", "Notizen werden erstellt"],
  ["等待操作", "Action required", "Aktion erforderlich"],
  ["已暂停", "Paused", "Pausiert"],
  ["可以提问", "Ready for questions", "Bereit für Fragen"],
  ["暂不支持", "Unsupported", "Nicht unterstützt"],
  ["处理失败", "Failed", "Fehlgeschlagen"],
  ["已停止", "Stopped", "Gestoppt"],
  ["这次学习放在哪里？", "Where should this lesson go?", "Wo soll diese Lektion abgelegt werden?"],
  ["作为新任务", "New task", "Neue Aufgabe"],
  ["继续旧任务", "Add to existing task", "Zu bestehender Aufgabe hinzufügen"],
  ["任务名称", "Task name", "Aufgabenname"],
  ["选择已有任务", "Select an existing task", "Bestehende Aufgabe wählen"],
  ["公开课网址", "Public course URL", "URL des öffentlichen Kurses"],
  ["主要语言", "Course language", "Kurssprache"],
  ["笔记详细程度", "Note detail level", "Detailgrad der Notizen"],
  ["快速摘要", "Quick summary", "Kurzübersicht"],
  ["标准详解（推荐）", "Standard guide (recommended)", "Standard-Lernhilfe (empfohlen)"],
  ["深度研习", "Deep study", "Vertiefendes Lernen"],
  ["笔记输出语言", "Note output language", "Ausgabesprache der Notizen"],
  ["跟随软件语言", "Follow app language", "App-Sprache verwenden"],
  ["取消", "Cancel", "Abbrechen"],
  ["添加并检查", "Add and check", "Hinzufügen und prüfen"],
  ["解析播放列表 / 批量网址", "Parse playlist / URL list", "Playlist / URL-Liste analysieren"],
  ["选择要加入的课程小节", "Select lessons to add", "Hinzuzufügende Lektionen wählen"],
  ["取消全选", "Clear all", "Auswahl aufheben"],
  ["全选", "Select all", "Alle auswählen"],
  ["每行一个网址，也可以粘贴播放列表网址", "One URL per line, or paste a playlist URL", "Eine URL pro Zeile oder eine Playlist-URL einfügen"],
  ["模型与转写", "Models and transcription", "Modelle und Transkription"],
  ["保存并测试", "Save and test", "Speichern und testen"],
  ["关闭", "Close", "Schließen"],
  ["文本模型", "Text model", "Textmodell"],
  ["本地 faster-whisper 模型", "Local faster-whisper model", "Lokales faster-whisper-Modell"],
  ["任务管理", "Task management", "Aufgabenverwaltung"],
  ["管理学习任务", "Manage learning task", "Lernaufgabe verwalten"],
  ["保存任务名称", "Save task name", "Aufgabenname speichern"],
  ["速学速记", "Rapid notes", "Schnellnotizen"],
  ["重新生成速学速记", "Regenerate rapid notes", "Schnellnotizen neu erstellen"],
  ["删除任务", "Delete task", "Aufgabe löschen"],
  ["永久删除这个任务", "Permanently delete this task", "Diese Aufgabe dauerhaft löschen"],
  ["笔记详细程度与生成规则", "Note detail and generation rules", "Detailgrad und Erstellungsregeln"],
  ["系统规则", "System rules", "Systemregeln"],
  ["逐段整理规则", "Section processing rules", "Regeln für Abschnittsnotizen"],
  ["整节总览规则", "Lesson overview rules", "Regeln für die Lektionsübersicht"],
  ["使用这套提示词", "Use this prompt", "Diesen Prompt verwenden"],
  ["能力检查", "Capability check", "Fähigkeitsprüfung"],
  ["网页", "Web page", "Webseite"],
  ["视频", "Video", "Video"],
  ["字幕", "Captions", "Untertitel"],
  ["转写", "Transcription", "Transkription"],
  ["课程已通过完整能力检查", "Course passed all capability checks", "Kurs hat alle Fähigkeitsprüfungen bestanden"],
  ["可以处理，但会使用降级能力", "Course can be processed with limited capabilities", "Kurs kann mit eingeschränkten Fähigkeiten verarbeitet werden"],
  ["需要你完成一项操作", "Action required from you", "Eine Aktion ist erforderlich"],
  ["当前配置无法可靠处理", "Current setup cannot process this course reliably", "Die aktuelle Konfiguration kann diesen Kurs nicht zuverlässig verarbeiten"],
  ["速学速记会在这里生成", "Rapid notes will appear here", "Schnellnotizen erscheinen hier"],
  ["你的课程理解工作台", "Your course learning workspace", "Ihr Kurs-Lernarbeitsplatz"],
  ["添加第一个公开课", "Add your first public course", "Ersten öffentlichen Kurs hinzufügen"],
  ["先检查能力", "Check capabilities first", "Fähigkeiten zuerst prüfen"],
  ["课程优先笔记", "Course-first notes", "Kursorientierte Notizen"],
  ["独立任务问答", "Task-based Q&A", "Aufgabenbezogene Fragen"],
  ["选择一个学习任务后开始提问。", "Select a learning task to ask questions.", "Wählen Sie eine Lernaufgabe, um Fragen zu stellen."],
  ["请先选择任务", "Select a task first", "Zuerst eine Aufgabe wählen"],
  ["主要基于课程内容提问…", "Ask mainly about the course content…", "Vor allem zum Kursinhalt fragen…"],
  ["请先配置并测试 API", "Configure and test the API first", "API zuerst konfigurieren und testen"],
  ["API 可用", "API ready", "API bereit"],
  ["API 待验证", "API not verified", "API nicht verifiziert"],
  ["配置 API", "Configure API", "API konfigurieren"],
  ["例如：“老师为什么这样定义？”或“总结这一节的推导过程。”", "For example: “Why does the lecturer define it this way?” or “Summarize this lesson’s derivation.”", "Zum Beispiel: „Warum definiert die Lehrkraft es so?“ oder „Fasse die Herleitung dieser Lektion zusammen.“"],
  ["只读提示词", "Read-only prompts", "Schreibgeschützte Prompts"],
  ["提示词由版本控制，只能查看和选择，不能在此修改。更改只影响这节课下一次生成或重新生成的笔记。", "Prompts are version-controlled and can only be viewed and selected here. Changes apply the next time this lesson’s notes are generated or regenerated.", "Prompts sind versionsverwaltet und können hier nur angezeigt und ausgewählt werden. Änderungen gelten bei der nächsten Erstellung oder Neuerstellung der Notizen dieser Lektion."],
  ["学习助手待命", "Study Assistant ready", "Study Assistant bereit"],
  ["正在连接助手", "Connecting to Study Assistant", "Verbindung zu Study Assistant wird hergestellt"],
  ["正在启动", "Starting", "Wird gestartet"],
  ["当前任务", "Current task", "Aktuelle Aufgabe"],
  ["暂无运行中的任务", "No task is currently running", "Derzeit läuft keine Aufgabe"],
  ["暂无正在处理的课程小节", "No lesson is currently being processed", "Derzeit wird keine Lektion verarbeitet"],
  ["查看当前任务", "View current task", "Aktuelle Aufgabe anzeigen"],
  ["收起当前任务", "Collapse current task", "Aktuelle Aufgabe einklappen"],
  ["隐藏电子宠物", "Hide desktop pet", "Desktop-Haustier ausblenden"],
  ["拖动电子宠物", "Drag desktop pet", "Desktop-Haustier verschieben"],
  ["隐藏", "Hide", "Ausblenden"],
  ["暂停或继续", "Pause or resume", "Pausieren oder fortsetzen"],
  ["打开主界面", "Open main window", "Hauptfenster öffnen"],
  ["隐藏状态浮窗", "Hide status window", "Statusfenster ausblenden"],
  ["检查完成，等待开始", "Check complete; ready to start", "Prüfung abgeschlossen; startbereit"],
  ["定位网页和课程媒体", "Locating the page and course media", "Webseite und Kursmedien werden gesucht"],
  ["读取课程内容", "Reading course content", "Kursinhalt wird gelesen"],
  ["将音频转换为文字", "Converting audio to text", "Audio wird in Text umgewandelt"],
  ["整理课程主线与速记卡", "Organizing the course and review cards", "Kursstruktur und Merkkarten werden erstellt"],
  ["需要登录或授权", "Login or authorization required", "Anmeldung oder Autorisierung erforderlich"],
  ["从当前断点继续", "Resume from the current checkpoint", "Am aktuellen Kontrollpunkt fortsetzen"],
  ["课程笔记已准备好", "Course notes are ready", "Kursnotizen sind bereit"],
  ["查看能力检查详情", "View capability-check details", "Details der Fähigkeitsprüfung anzeigen"],
  ["查看错误并重试", "Review the error and retry", "Fehler prüfen und erneut versuchen"],
  ["已完成内容仍然保留", "Completed content is preserved", "Fertige Inhalte bleiben erhalten"],
  ["等待课程网址", "Waiting for a course URL", "Warten auf eine Kurs-URL"],
  ["课程网址已添加，等待能力检查", "Course URL added; waiting for capability check", "Kurs-URL hinzugefügt; Fähigkeitsprüfung ausstehend"],
  ["应用重新启动，可继续任务", "App restarted; the task can be resumed", "App neu gestartet; die Aufgabe kann fortgesetzt werden"],
  ["正在检查网页、字幕与模型能力", "Checking the page, captions, and model capabilities", "Webseite, Untertitel und Modellfähigkeiten werden geprüft"],
  ["检查通过，可以开始记录课程", "Checks passed; course processing can start", "Prüfung bestanden; Kursverarbeitung kann beginnen"],
  ["可以开始，但存在能力限制", "Ready to start with capability limitations", "Startbereit mit eingeschränkten Fähigkeiten"],
  ["需要用户完成登录或授权", "User login or authorization required", "Anmeldung oder Autorisierung durch den Benutzer erforderlich"],
  ["当前无法处理此课程", "This course cannot currently be processed", "Dieser Kurs kann derzeit nicht verarbeitet werden"],
  ["任务已暂停，可从当前断点继续", "Task paused; it can resume from the current checkpoint", "Aufgabe pausiert; Fortsetzung am aktuellen Kontrollpunkt möglich"],
  ["正在从断点继续", "Resuming from the checkpoint", "Fortsetzung am Kontrollpunkt"],
  ["任务已停止，已完成内容仍然保留", "Task stopped; completed content is preserved", "Aufgabe gestoppt; fertige Inhalte bleiben erhalten"],
  ["正在重新生成速学速记", "Regenerating rapid-learning notes", "Schnelllernnotizen werden neu erstellt"],
  ["速学速记已重新生成，可以开始提问", "Rapid-learning notes regenerated; ready for questions", "Schnelllernnotizen neu erstellt; bereit für Fragen"],
  ["重新生成已中断，可稍后继续", "Regeneration interrupted; it can be resumed later", "Neuerstellung unterbrochen; spätere Fortsetzung möglich"],
  ["正在下载音轨并准备转写", "Downloading audio and preparing transcription", "Audio wird heruntergeladen und die Transkription vorbereitet"],
  ["正在生成速学速记", "Generating rapid-learning notes", "Schnelllernnotizen werden erstellt"],
  ["速学速记已生成，可以开始提问", "Rapid-learning notes generated; ready for questions", "Schnelllernnotizen erstellt; bereit für Fragen"],
  ["任务已中断，可稍后继续", "Task interrupted; it can be resumed later", "Aufgabe unterbrochen; spätere Fortsetzung möglich"],
  ["正在生成速学模块", "Generating rapid-learning module", "Schnelllernmodul wird erstellt"],
  ["正在生成本节课速学总览", "Generating the lesson overview", "Lektionsübersicht wird erstellt"],
  ["处理失败：", "Processing failed: ", "Verarbeitung fehlgeschlagen: "],
  ["还没有课程。添加一个公开课网址开始学习。", "No courses yet. Add a public course URL to start learning.", "Noch keine Kurse. Fügen Sie zum Start eine öffentliche Kurs-URL hinzu."],
  ["等待处理", "Waiting to be processed", "Warten auf Verarbeitung"],
  ["请添加课程小节", "Add a course lesson", "Kurslektion hinzufügen"],
  ["文本模型连接测试已通过", "Text-model connection test passed", "Verbindungstest des Textmodells bestanden"],
  ["打开 API 与模型设置", "Open API and model settings", "API- und Modelleinstellungen öffnen"],
  ["停止", "Stop", "Stoppen"],
  ["助手会先整理逐段知识，再把整节课汇总为详细内容介绍、知识地图和一页速记表。", "The assistant first organizes each segment, then turns the full lesson into a detailed guide, knowledge map, and one-page review table.", "Der Assistent strukturiert zunächst jeden Abschnitt und fasst dann die gesamte Lektion als ausführliche Übersicht, Wissenslandkarte und einseitige Wiederholungstabelle zusammen."],
  ["把公开课交给助手，把注意力留给理解。", "Give the course to the assistant and keep your attention on understanding.", "Überlassen Sie den Kurs dem Assistenten und konzentrieren Sie sich auf das Verstehen."],
  ["助手会定位课程视频、优先读取字幕，再将课程内容整理成详细介绍、知识地图和速学速记。", "The assistant locates the course video, reads captions first, and organizes the content into a detailed guide, knowledge map, and rapid-learning notes.", "Der Assistent findet das Kursvideo, liest bevorzugt die Untertitel und strukturiert den Inhalt als ausführliche Übersicht, Wissenslandkarte und Schnelllernnotizen."],
  ["你", "You", "Sie"],
  ["任务名称已更新。", "Task name updated.", "Aufgabenname aktualisiert."],
  ["复用任务中已经保存的字幕或转写文字，按新的固定模板重新生成，不会重新下载课程音轨。", "Reuse the saved captions or transcript with the selected template; the course audio will not be downloaded again.", "Gespeicherte Untertitel oder Transkripte werden mit der gewählten Vorlage erneut verwendet; das Kursaudio wird nicht erneut heruntergeladen."],
  ["删除任务数据库记录、课程音轨和该任务的导出文件；共享的本地 Whisper 模型不会删除。", "Delete this task’s database records, course audio, and exports. Shared local Whisper models are kept.", "Datenbankeinträge, Kursaudio und Exporte dieser Aufgabe werden gelöscht. Gemeinsam genutzte lokale Whisper-Modelle bleiben erhalten."],
  ["系统会先检查网页、字幕、音轨和模型能力。发现登录、DRM 或能力不足时会先停下并提示。", "The system first checks the page, captions, audio, and model capabilities. It stops and explains if login, DRM, or missing capabilities are detected.", "Das System prüft zunächst Webseite, Untertitel, Audio und Modellfähigkeiten. Bei Anmeldung, DRM oder fehlenden Fähigkeiten stoppt es und zeigt einen Hinweis."],
  ["正在基于现有课程文字重新生成速学速记。", "Regenerating rapid-learning notes from the existing course text.", "Schnelllernnotizen werden aus dem vorhandenen Kurstext neu erstellt."],
  ["提示词方案已保存；重新生成本节笔记时生效。", "Prompt preset saved; it will apply when this lesson’s notes are regenerated.", "Prompt-Voreinstellung gespeichert; sie gilt bei der Neuerstellung der Notizen dieser Lektion."],
  ["课程小节已删除。任务中的其他小节和问答仍然保留。", "Lesson deleted. Other lessons and task conversations are preserved.", "Lektion gelöscht. Andere Lektionen und Aufgabengespräche bleiben erhalten."],
  ["学习任务及其关联文件已删除。", "Learning task and associated files deleted.", "Lernaufgabe und zugehörige Dateien gelöscht."],
  ["操作失败", "Operation failed", "Vorgang fehlgeschlagen"],
  ["检查失败", "Capability check failed", "Fähigkeitsprüfung fehlgeschlagen"],
  ["回答失败", "Answer failed", "Antwort fehlgeschlagen"],
  ["导出失败", "Export failed", "Export fehlgeschlagen"],
  ["课程处理失败，请检查 API 设置后重试。", "Course processing failed. Check the API settings and retry.", "Kursverarbeitung fehlgeschlagen. Prüfen Sie die API-Einstellungen und versuchen Sie es erneut."],
  ["无法连接本地 Agent 服务", "Cannot connect to the Local Agent service", "Keine Verbindung zum lokalen Agent-Dienst"],
  ["读取任务失败", "Failed to load tasks", "Aufgaben konnten nicht geladen werden"],
  ["停止任务？已经生成的字幕和笔记会保留。", "Stop the task? Existing captions and notes will be preserved.", "Aufgabe stoppen? Vorhandene Untertitel und Notizen bleiben erhalten."],
  ["使用现有课程文字重新生成速学速记？当前笔记将被替换。", "Regenerate rapid-learning notes from the existing course text? Current notes will be replaced.", "Schnelllernnotizen aus dem vorhandenen Kurstext neu erstellen? Die aktuellen Notizen werden ersetzt."],
  ["例如：MIT 线性代数", "For example: MIT Linear Algebra", "Zum Beispiel: MIT Lineare Algebra"],
  ["API Key（仅本次运行）", "API key (this session only)", "API-Key (nur diese Sitzung)"],
  ["请重新输入；留空会立即清除", "Enter it again; leaving this blank clears it immediately", "Erneut eingeben; ein leeres Feld löscht den Wert sofort"],
  ["程序重启后自动清空", "Cleared automatically when the app restarts", "Wird beim Neustart der App automatisch gelöscht"],
  ["用于笔记和问答", "Used for notes and Q&A", "Für Notizen und Fragen"],
  ["Kimi K3 推理强度", "Kimi K3 reasoning effort", "Kimi-K3-Denktiefe"],
  ["Low（推荐，速度与成本优先）", "Low (recommended; prioritizes speed and cost)", "Niedrig (empfohlen; priorisiert Geschwindigkeit und Kosten)"],
  ["High（质量优先）", "High (prioritizes quality)", "Hoch (priorisiert Qualität)"],
  ["Max（最强推理，耗时更长）", "Max (strongest reasoning; takes longer)", "Maximal (stärkstes Reasoning; dauert länger)"],
  ["Small（推荐，速度与体积均衡）", "Small (recommended; balanced speed and size)", "Small (empfohlen; ausgewogenes Verhältnis von Geschwindigkeit und Größe)"],
  ["Medium（更准确、运行更慢）", "Medium (more accurate; runs slower)", "Medium (genauer; läuft langsamer)"],
  ["Large v3（最高质量、资源占用高）", "Large v3 (highest quality; resource intensive)", "Large v3 (höchste Qualität; ressourcenintensiv)"],
  ["本地语义检索", "Local semantic retrieval", "Lokale semantische Suche"],
  ["已就绪", "Ready", "Bereit"],
  ["等待重试", "Waiting to retry", "Wartet auf erneuten Versuch"],
  ["正在初始化", "Initializing", "Wird initialisiert"],
  ["等待初始化本地语义检索", "Waiting to initialize local semantic retrieval", "Lokale semantische Suche wartet auf Initialisierung"],
  ["正在下载内置多语言语义模型", "Downloading the built-in multilingual semantic model", "Integriertes mehrsprachiges Semantikmodell wird heruntergeladen"],
  ["正在下载本地语义模型", "Downloading the local semantic model", "Lokales Semantikmodell wird heruntergeladen"],
  ["本地语义模型下载完成", "Local semantic model download is complete", "Das lokale Semantikmodell wurde heruntergeladen"],
  ["正在优化本地语义模型", "Optimizing the local semantic model", "Lokales Semantikmodell wird optimiert"],
  ["本地语义模型准备完成", "Local semantic model is prepared", "Lokales Semantikmodell ist vorbereitet"],
  ["正在加载本地语义模型", "Loading the local semantic model", "Lokales Semantikmodell wird geladen"],
  ["正在为已有课程建立本地语义索引", "Building local semantic indexes for existing lessons", "Lokale semantische Indizes für vorhandene Lektionen werden erstellt"],
  ["正在更新课程语义索引", "Updating the lesson semantic index", "Semantischer Lektionsindex wird aktualisiert"],
  ["本地语义检索已就绪", "Local semantic retrieval is ready", "Lokale semantische Suche ist bereit"],
  ["本地语义检索初始化失败；课程问答将继续使用词法检索。", "Local semantic retrieval could not be initialized; course Q&A will continue with lexical retrieval.", "Die lokale semantische Suche konnte nicht initialisiert werden; Kursfragen verwenden weiterhin die lexikalische Suche."],
  ["已索引", "Indexed", "Indiziert"],
  ["节课程", "lessons", "Lektionen"],
  ["个语义片段", "semantic passages", "semantische Abschnitte"],
  ["节等待处理", "lessons pending", "Lektionen ausstehend"],
  ["模型 API Key 只保存在当前程序进程内存中，关闭程序后失效，下次启动必须重新填写；旧版本保存过的系统凭据会在启动时删除。本地转写模型仅在无字幕课程首次需要时下载，随后保存在本机复用。内置多语言语义模型会自动下载并在本机维护课程索引，不需要额外 API。Kimi K3 会自动使用其兼容参数。", "The model API key is kept only in this app process and is discarded when the app closes; enter it again after every start. Credentials saved by older versions are removed at startup. The local transcription model is downloaded only when first needed for a course without captions and is then reused locally. The built-in multilingual semantic model is downloaded automatically and maintains course indexes locally without another API. Kimi K3 automatically uses compatible parameters.", "Der Modell-API-Schlüssel bleibt ausschließlich im Speicher dieses App-Prozesses und wird beim Schließen verworfen; nach jedem Start muss er neu eingegeben werden. Von älteren Versionen gespeicherte Anmeldedaten werden beim Start entfernt. Das lokale Transkriptionsmodell wird nur bei der ersten Lektion ohne Untertitel heruntergeladen und anschließend lokal wiederverwendet. Das integrierte mehrsprachige Semantikmodell wird automatisch geladen und verwaltet Kursindizes lokal, ohne zusätzliche API. Kimi K3 verwendet automatisch kompatible Parameter."],
  ["把公开课交给助手，", "Give the course to the assistant,", "Überlassen Sie den Kurs dem Assistenten,"],
  ["把注意力留给理解。", "and keep your attention on understanding.", "und konzentrieren Sie sich auf das Verstehen."],
  ["缺少字幕，且本地 faster-whisper 运行库不可用。", "No captions are available, and the local faster-whisper runtime is unavailable.", "Keine Untertitel verfügbar und die lokale faster-whisper-Laufzeit ist nicht verfügbar."],
  ["重新安装包含本地转写组件的完整发布版。", "Reinstall the complete release that includes local transcription.", "Installieren Sie die vollständige Version mit lokaler Transkription erneut."],
  ["未配置文本模型，无法生成 AI 速学速记或课程回答。", "No text model is configured, so AI rapid-learning notes and course answers are unavailable.", "Kein Textmodell konfiguriert; KI-Schnelllernnotizen und Kursantworten sind nicht verfügbar."],
  ["打开“API 设置”，填写文本模型和 API Key 并完成连接测试。", "Open API settings, enter a text model and API key, and complete the connection test.", "Öffnen Sie die API-Einstellungen, geben Sie Textmodell und API-Key ein und führen Sie den Verbindungstest aus."],
  ["当前运行未填写 API Key，AI 速学速记和课程问答不可用。", "No API key was entered for this session, so AI notes and course Q&A are unavailable.", "Für diese Sitzung wurde kein API-Key eingegeben; KI-Notizen und Kursfragen sind nicht verfügbar."],
  ["程序每次启动都会清空 Key；请重新填写并确认连接测试成功。", "The key is cleared at every startup; enter it again and confirm that the connection test passes.", "Der Schlüssel wird bei jedem Start gelöscht; geben Sie ihn erneut ein und bestätigen Sie den erfolgreichen Verbindungstest."],
  ["支持 Study Assistant", "Support Study Assistant", "Study Assistant unterstützen"],
  ["请我喝杯咖啡", "Buy me a coffee", "Spendiere mir einen Kaffee"],
  ["首次开始记录时需要联网下载本地转写模型，下载后可离线复用。", "The local transcription model needs to be downloaded when processing starts for the first time and can then be reused offline.", "Das lokale Transkriptionsmodell wird beim ersten Verarbeitungsstart heruntergeladen und kann danach offline wiederverwendet werden."],
  ["课程小节", "Course lesson", "Kurslektion"],
  ["课程命名", "Lesson naming", "Lektionsbenennung"],
  ["设置课程名称", "Set lesson name", "Lektionsnamen festlegen"],
  ["自定义名称", "Custom name", "Benutzerdefinierter Name"],
  ["恢复默认名称", "Restore default name", "Standardnamen wiederherstellen"],
  ["保存课程名称", "Save lesson name", "Lektionsnamen speichern"],
  ["网页原始课程标题仍会保留为来源信息。", "The original page title is preserved as source information.", "Der ursprüngliche Seitentitel bleibt als Quelleninformation erhalten."],
  ["留空时使用默认名称", "Leave blank to use the default name", "Leer lassen, um den Standardnamen zu verwenden"],
  ["重命名课程", "Rename lesson", "Lektion umbenennen"],
  ["课程名称已更新。", "Lesson name updated.", "Lektionsname aktualisiert."],
  ["课程已恢复默认名称。", "Default lesson name restored.", "Standardname der Lektion wiederhergestellt."],
  ["管理对话", "Manage conversations", "Gespräche verwalten"],
  ["对话名称", "Conversation name", "Gesprächsname"],
  ["打开对话", "Open conversation", "Gespräch öffnen"],
  ["保存名称", "Save name", "Namen speichern"],
  ["删除对话", "Delete conversation", "Gespräch löschen"],
  ["清空全部对话", "Clear all conversations", "Alle Gespräche löschen"],
  ["还没有保存的对话。", "No saved conversations yet.", "Noch keine gespeicherten Gespräche."],
  ["永久删除这个对话？", "Permanently delete this conversation?", "Dieses Gespräch dauerhaft löschen?"],
  ["永久删除当前任务的全部对话？", "Permanently delete all conversations in this task?", "Alle Gespräche dieser Aufgabe dauerhaft löschen?"],
];

export function translateUiText(value: string, locale: UiLanguage): string {
  for (const entry of ENTRIES) {
    const index = entry.indexOf(value);
    if (index >= 0) return locale === "zh-CN" ? entry[0] : locale === "en" ? entry[1] : entry[2];
  }
  const lesson = value.match(/^(?:第\s*(\d+)\s*节|Lesson\s+(\d+)|Lektion\s+(\d+))(.*)$/);
  if (lesson) {
    const number = lesson[1] || lesson[2] || lesson[3];
    const prefix = locale === "zh-CN" ? `第 ${number} 节` : locale === "en" ? `Lesson ${number}` : `Lektion ${number}`;
    const tail = translateUiText(lesson[4], locale);
    const separator = locale !== "zh-CN" && tail && !/^[\s·:：,，.\-]/.test(tail) ? " " : "";
    return prefix + separator + tail;
  }
  const completed = value.match(/^(\d+)\/(\d+)\s*(?:节已完成|lessons completed|Lektionen abgeschlossen)(.*)$/);
  if (completed) {
    const prefix = locale === "zh-CN"
      ? `${completed[1]}/${completed[2]} 节已完成`
      : locale === "en"
        ? `${completed[1]}/${completed[2]} lessons completed`
        : `${completed[1]}/${completed[2]} Lektionen abgeschlossen`;
    return prefix + completed[3];
  }
  const deleteLesson = value.match(/^永久删除第\s*(\d+)\s*节及其转写和笔记？$/);
  if (deleteLesson) {
    return locale === "zh-CN"
      ? `永久删除第 ${deleteLesson[1]} 节及其转写和笔记？`
      : locale === "en"
        ? `Permanently delete lesson ${deleteLesson[1]}, its transcript, and its notes?`
        : `Lektion ${deleteLesson[1]} samt Transkript und Notizen dauerhaft löschen?`;
  }
  const deleteTask = value.match(/^永久删除任务“(.+)”？此操作无法撤销。$/);
  if (deleteTask) {
    return locale === "zh-CN"
      ? value
      : locale === "en"
        ? `Permanently delete task “${deleteTask[1]}”? This cannot be undone.`
        : `Aufgabe „${deleteTask[1]}“ dauerhaft löschen? Dies kann nicht rückgängig gemacht werden.`;
  }
  if (value.startsWith("处理失败：")) {
    const detail = value.slice("处理失败：".length);
    return locale === "zh-CN"
      ? value
      : locale === "en"
        ? `Processing failed: ${detail}`
        : `Verarbeitung fehlgeschlagen: ${detail}`;
  }
  for (const entry of ENTRIES) {
    for (const source of entry) {
      if (value.includes(source)) {
        const target = locale === "zh-CN" ? entry[0] : locale === "en" ? entry[1] : entry[2];
        return value.replace(source, target);
      }
    }
  }
  return value;
}

function translateNode(node: Text, locale: UiLanguage) {
  const parent = node.parentElement;
  if (!parent || parent.closest(".markdown-body, pre")) return;
  const raw = node.data;
  const trimmed = raw.trim();
  if (!trimmed) return;
  const next = translateUiText(trimmed, locale);
  if (next !== trimmed) node.data = raw.replace(trimmed, next);
}

export function localizeUi(root: HTMLElement, locale: UiLanguage): () => void {
  document.documentElement.lang = locale;
  const apply = () => {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node = walker.nextNode();
    while (node) {
      translateNode(node as Text, locale);
      node = walker.nextNode();
    }
    root.querySelectorAll<HTMLElement>("[placeholder], [title], [aria-label]").forEach((element) => {
      for (const name of ["placeholder", "title", "aria-label"]) {
        const value = element.getAttribute(name);
        if (!value) continue;
        const next = translateUiText(value, locale);
        if (next !== value) element.setAttribute(name, next);
      }
    });
  };
  apply();
  const observer = new MutationObserver(apply);
  observer.observe(root, { childList: true, subtree: true, characterData: true, attributes: true });
  return () => observer.disconnect();
}
