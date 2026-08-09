import {
  AlertTriangle,
  BookOpen,
  Check,
  ChevronRight,
  CirclePause,
  CirclePlay,
  Coffee,
  ExternalLink,
  FileDown,
  Gauge,
  GripHorizontal,
  Globe2,
  LoaderCircle,
  MessageCircle,
  MoreHorizontal,
  PanelsTopLeft,
  Pencil,
  Plus,
  RefreshCw,
  Settings2,
  Sparkles,
  Square,
  Trash2,
  X,
} from "lucide-react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import {
  FormEvent,
  MouseEvent as ReactMouseEvent,
  PointerEvent as ReactPointerEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { api, eventUrl, initializeConnection, waitForAgent } from "./api";
import idlePet from "./assets/pet/idle.webp";
import wakePet from "./assets/pet/wake.webp";
import workingPet from "./assets/pet/working.webp";
import { MermaidBlock } from "./MermaidBlock";
import { localizeUi, translateUiText } from "./i18n";
import type {
  CapabilityReport,
  Citation,
  Conversation,
  Message,
  LessonCandidate,
  NoteBlock,
  PromptPreset,
  ProviderSettings,
  SemanticStatus,
  Source,
  Task,
  TaskStatus,
  UiLanguage,
} from "./types";

function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        pre({ children: preChildren }) {
          return <>{preChildren}</>;
        },
        code({ className, children: codeChildren, ...props }) {
          const code = String(codeChildren).replace(/\n$/, "");
          if (className === "language-mermaid") return <MermaidBlock chart={code} />;
          if (className?.startsWith("language-")) {
            return <pre><code className={className} {...props}>{codeChildren}</code></pre>;
          }
          return <code className={className} {...props}>{codeChildren}</code>;
        },
      }}
    >
      {children}
    </ReactMarkdown>
  );
}

const ACTIVE_STATES: TaskStatus[] = ["CHECKING", "WATCHING", "TRANSCRIBING", "NOTE_TAKING"];

const STATUS_META: Record<
  TaskStatus,
  { label: string; tone: string; action: string }
> = {
  IDLE: { label: "待开始", tone: "neutral", action: "检查完成，等待开始" },
  CHECKING: { label: "正在检查", tone: "running", action: "定位网页和课程媒体" },
  WATCHING: { label: "正在观看", tone: "running", action: "读取课程内容" },
  TRANSCRIBING: { label: "正在转写", tone: "running", action: "将音频转换为文字" },
  NOTE_TAKING: { label: "生成速学速记", tone: "running", action: "整理课程主线与速记卡" },
  NEEDS_USER: { label: "等待操作", tone: "warning", action: "需要登录或授权" },
  PAUSED: { label: "已暂停", tone: "warning", action: "从当前断点继续" },
  READY_FOR_QA: { label: "可以提问", tone: "success", action: "课程笔记已准备好" },
  UNSUPPORTED: { label: "暂不支持", tone: "danger", action: "查看能力检查详情" },
  FAILED: { label: "处理失败", tone: "danger", action: "查看错误并重试" },
  STOPPED: { label: "已停止", tone: "neutral", action: "已完成内容仍然保留" },
};

const EMPTY_SETTINGS: ProviderSettings = {
  api_base_url: "https://api.openai.com/v1",
  text_model: "",
  reasoning_effort: "low",
  local_whisper_model: "small",
};

const EMPTY_SEMANTIC_STATUS: SemanticStatus = {
  state: "NOT_READY",
  model: "intfloat/multilingual-e5-small",
  model_revision: "",
  runtime_available: false,
  model_downloaded: false,
  progress: 0,
  indexed_sources: 0,
  pending_sources: 0,
  indexed_chunks: 0,
  message: "等待初始化本地语义检索",
};

function formatDate(value: string, locale: UiLanguage = "zh-CN"): string {
  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatTime(seconds: number | null): string {
  if (seconds === null) return "--:--";
  const value = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const secs = value % 60;
  return hours
    ? `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}:${secs
        .toString()
        .padStart(2, "0")}`
    : `${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

function StatusPill({ status }: { status: TaskStatus }) {
  const meta = STATUS_META[status];
  return (
    <span className={`status-pill status-${meta.tone}`}>
      <span className="status-dot" />
      {meta.label}
    </span>
  );
}

function CapabilityCard({ report }: { report: CapabilityReport }) {
  const headline = {
    READY: "课程已通过完整能力检查",
    LIMITED: "可以处理，但会使用降级能力",
    NEEDS_USER: "需要你完成一项操作",
    UNSUPPORTED: "当前配置无法可靠处理",
  }[report.status];
  const metrics = [
    ["网页", report.page_accessible],
    ["视频", report.video_detected],
    ["字幕", report.captions_available],
    ["转写", report.transcription_available],
  ] as const;
  return (
    <section className={`capability-card capability-${report.status.toLowerCase()}`}>
      <div className="capability-heading">
        <div>
          <span className="eyebrow">能力检查</span>
          <h3>{headline}</h3>
        </div>
        <div className="capability-metrics">
          {metrics.map(([name, enabled]) => (
            <span className={enabled ? "metric-on" : "metric-off"} key={name}>
              {enabled ? <Check size={12} /> : <X size={12} />} {name}
            </span>
          ))}
        </div>
      </div>
      {report.reasons.length > 0 && (
        <ul className="reason-list">
          {report.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
      {report.suggestions.length > 0 && (
        <div className="suggestion-line">
          <Sparkles size={14} /> {report.suggestions.join(" · ")}
        </div>
      )}
    </section>
  );
}

function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return (
    <div className="citation-list">
      {citations.map((citation, index) => {
        const label =
          citation.source_type === "course"
            ? `课程 ${formatTime(citation.start_seconds)}`
            : citation.title;
        const body = (
          <>
            <span>{index + 1}</span>
            {label}
            {citation.url && <ExternalLink size={11} />}
          </>
        );
        return citation.url ? (
          <a href={citation.url} target="_blank" rel="noreferrer" key={`${label}-${index}`}>
            {body}
          </a>
        ) : (
          <div key={`${label}-${index}`}>{body}</div>
        );
      })}
    </div>
  );
}

function NewTaskDialog({
  tasks,
  onClose,
  onSubmit,
}: {
  tasks: Task[];
  onClose: () => void;
  onSubmit: (input: {
    mode: "new" | "existing";
    taskId: string;
    title: string;
    lessons: LessonCandidate[];
    language: string;
    promptPresetId: "quick" | "standard" | "deep";
    outputLanguage: "auto" | "zh-CN" | "en" | "de";
  }) => Promise<void>;
}) {
  const [mode, setMode] = useState<"new" | "existing">("new");
  const [taskId, setTaskId] = useState(tasks[0]?.id || "");
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [candidates, setCandidates] = useState<LessonCandidate[]>([]);
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(new Set());
  const [language, setLanguage] = useState("zh-CN");
  const [promptPresetId, setPromptPresetId] = useState<"quick" | "standard" | "deep">("standard");
  const [outputLanguage, setOutputLanguage] = useState<"auto" | "zh-CN" | "en" | "de">("auto");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const rawLessons = url.split(/\r?\n/).map((item) => item.trim()).filter(Boolean).map((item) => ({ url: item, title: "" }));
      const lessons = candidates.length
        ? candidates.filter((item) => selectedUrls.has(item.url))
        : rawLessons;
      if (!lessons.length) throw new Error("请至少选择一节课程。");
      await onSubmit({ mode, taskId, title, lessons, language, promptPresetId, outputLanguage });
      onClose();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "无法创建任务");
    } finally {
      setBusy(false);
    }
  }

  async function discover() {
    const urls = url.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
    if (!urls.length) return;
    setBusy(true);
    setError("");
    try {
      const groups = await Promise.all(urls.map((item) => api.discoverLessons(item)));
      const unique = Array.from(
        new Map(groups.flat().map((item) => [item.url, item])).values(),
      );
      setCandidates(unique);
      setSelectedUrls(new Set(unique.map((item) => item.url)));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "无法解析课程列表");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <form className="dialog" onSubmit={submit} onMouseDown={(event) => event.stopPropagation()}>
        <div className="dialog-header">
          <div>
            <span className="eyebrow">添加公开课</span>
            <h2>这次学习放在哪里？</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="关闭">
            <X size={18} />
          </button>
        </div>
        <div className="mode-switch">
          <button
            type="button"
            className={mode === "new" ? "selected" : ""}
            onClick={() => setMode("new")}
          >
            <Plus size={16} /> 作为新任务
          </button>
          <button
            type="button"
            className={mode === "existing" ? "selected" : ""}
            onClick={() => setMode("existing")}
            disabled={!tasks.length}
          >
            <RefreshCw size={16} /> 继续旧任务
          </button>
        </div>
        {mode === "new" ? (
          <label>
            任务名称
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="例如：MIT 线性代数"
              required
              autoFocus
            />
          </label>
        ) : (
          <label>
            选择已有任务
            <select value={taskId} onChange={(event) => setTaskId(event.target.value)} required>
              {tasks.map((task) => (
                <option value={task.id} key={task.id}>
                  {task.title}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          公开课网址
          <textarea
            value={url}
            onChange={(event) => { setUrl(event.target.value); setCandidates([]); }}
            placeholder="每行一个网址，也可以粘贴播放列表网址"
            rows={3}
            required
          />
        </label>
        <button type="button" className="button ghost full-width" disabled={busy || !url.trim()} onClick={discover}>
          <RefreshCw size={14} /> 解析播放列表 / 批量网址
        </button>
        {candidates.length > 0 && (
          <div className="lesson-candidates">
            <div><strong>选择要加入的课程小节</strong><button type="button" onClick={() => setSelectedUrls(selectedUrls.size === candidates.length ? new Set() : new Set(candidates.map((item) => item.url)))}>{selectedUrls.size === candidates.length ? "取消全选" : "全选"}</button></div>
            {candidates.map((item, index) => (
              <label key={item.url}>
                <input
                  type="checkbox"
                  checked={selectedUrls.has(item.url)}
                  onChange={(event) => setSelectedUrls((current) => {
                    const next = new Set(current);
                    if (event.target.checked) next.add(item.url); else next.delete(item.url);
                    return next;
                  })}
                />
                <span>{index + 1}. {item.title || item.url}</span>
              </label>
            ))}
          </div>
        )}
        {mode === "new" && (
          <label>
            主要语言
            <select value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option value="zh-CN">中文</option>
              <option value="en">English</option>
              <option value="de">Deutsch</option>
              <option value="fr">Français</option>
            </select>
          </label>
        )}
        <div className="settings-grid compact-grid">
          <label>
            笔记详细程度
            <select
              value={promptPresetId}
              onChange={(event) => setPromptPresetId(event.target.value as typeof promptPresetId)}
            >
              <option value="quick">快速摘要</option>
              <option value="standard">标准详解（推荐）</option>
              <option value="deep">深度研习</option>
            </select>
          </label>
          <label>
            笔记输出语言
            <select
              value={outputLanguage}
              onChange={(event) => setOutputLanguage(event.target.value as typeof outputLanguage)}
            >
              <option value="auto">跟随软件语言</option>
              <option value="zh-CN">中文</option>
              <option value="en">English</option>
              <option value="de">Deutsch</option>
            </select>
          </label>
        </div>
        <div className="privacy-note">
          系统会先检查网页、字幕、音轨和模型能力。发现登录、DRM 或能力不足时会先停下并提示。
        </div>
        {error && <div className="inline-error">{error}</div>}
        <div className="dialog-actions">
          <button type="button" className="button ghost" onClick={onClose}>
            取消
          </button>
          <button type="submit" className="button primary" disabled={busy}>
            {busy && <LoaderCircle className="spin" size={16} />}
            添加并检查
          </button>
        </div>
      </form>
    </div>
  );
}

function SettingsDialog({
  initial,
  semanticStatus,
  onClose,
  onSaved,
}: {
  initial: ProviderSettings;
  semanticStatus: SemanticStatus;
  onClose: () => void;
  onSaved: (settings: ProviderSettings, testPassed: boolean) => void;
}) {
  const [value, setValue] = useState<ProviderSettings>({ ...initial, api_key: "" });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  function field(name: keyof ProviderSettings, label: string, placeholder = "") {
    return (
      <label>
        {label}
        <input
          value={String(value[name] || "")}
          placeholder={placeholder}
          onChange={(event) => setValue({ ...value, [name]: event.target.value })}
          type={name.includes("key") ? "password" : "text"}
          autoComplete={name.includes("key") ? "off" : undefined}
          spellCheck={false}
        />
      </label>
    );
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const payload: ProviderSettings = { ...value };
      const saved = await api.saveSettings(payload);
      const tested = await api.testSettings();
      onSaved(saved, tested.text);
      setMessage(tested.message);
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "保存失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <form className="dialog settings-dialog" onSubmit={save} onMouseDown={(event) => event.stopPropagation()}>
        <div className="dialog-header">
          <div>
            <span className="eyebrow">模型与转写</span>
            <h2>智能能力设置</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="关闭">
            <X size={18} />
          </button>
        </div>
        <div className="settings-grid">
          {field("api_base_url", "API Base URL", "https://api.openai.com/v1")}
          {field("api_key", "API Key（仅本次运行）", initial.has_api_key ? "请重新输入；留空会立即清除" : "程序重启后自动清空")}
          {field("text_model", "文本模型", "用于笔记和问答")}
          <label>
            Kimi K3 推理强度
            <select
              value={value.reasoning_effort}
              onChange={(event) => setValue({
                ...value,
                reasoning_effort: event.target.value as ProviderSettings["reasoning_effort"],
              })}
            >
              <option value="low">Low（推荐，速度与成本优先）</option>
              <option value="high">High</option>
              <option value="max">Max（最强推理，耗时更长）</option>
            </select>
          </label>
          <label>
            本地 faster-whisper 模型
            <select
              value={value.local_whisper_model}
              onChange={(event) => setValue({
                ...value,
                local_whisper_model: event.target.value as ProviderSettings["local_whisper_model"],
              })}
            >
              <option value="small">Small（推荐，速度与体积均衡）</option>
              <option value="medium">Medium（更准确、运行更慢）</option>
              <option value="large-v3">Large v3（最高质量、资源占用高）</option>
            </select>
          </label>
        </div>
        <div className={`semantic-status semantic-${semanticStatus.state.toLowerCase()}`}>
          <div>
            <strong>本地语义检索</strong>
            <span>{semanticStatus.state === "READY" ? "已就绪" : semanticStatus.state === "FAILED" ? "等待重试" : "正在初始化"}</span>
          </div>
          <code>{semanticStatus.model}</code>
          <p>{semanticStatus.state === "FAILED"
            ? "本地语义检索初始化失败；课程问答将继续使用词法检索。"
            : semanticStatus.message}</p>
          <div className="semantic-progress"><i style={{ width: `${Math.round(semanticStatus.progress * 100)}%` }} /></div>
          <small>
            已索引 {semanticStatus.indexed_sources} 节课程 · {semanticStatus.indexed_chunks} 个语义片段
            {semanticStatus.pending_sources > 0 ? ` · ${semanticStatus.pending_sources} 节等待处理` : ""}
          </small>
        </div>
        <div className="privacy-note">
          模型 API Key 只保存在当前程序进程内存中，关闭程序后失效，下次启动必须重新填写；旧版本保存过的系统凭据会在启动时删除。本地转写模型仅在无字幕课程首次需要时下载，随后保存在本机复用。内置多语言语义模型会自动下载并在本机维护课程索引，不需要额外 API。Kimi K3 会自动使用其兼容参数。
        </div>
        {message && <div className="settings-message">{message}</div>}
        <div className="dialog-actions">
          <button type="button" className="button ghost" onClick={onClose}>
            关闭
          </button>
          <button type="submit" className="button primary" disabled={busy}>
            {busy && <LoaderCircle className="spin" size={16} />}
            保存并测试
          </button>
        </div>
      </form>
    </div>
  );
}

function PromptDialog({
  prompts,
  selected,
  onSelect,
  onClose,
}: {
  prompts: PromptPreset[];
  selected: Source["prompt_preset_id"];
  onSelect: (id: Source["prompt_preset_id"]) => Promise<void>;
  onClose: () => void;
}) {
  const [active, setActive] = useState<Source["prompt_preset_id"]>(selected);
  const [busy, setBusy] = useState(false);
  const prompt = prompts.find((item) => item.id === active);
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="dialog prompt-dialog" onMouseDown={(event) => event.stopPropagation()}>
        <div className="dialog-header">
          <div><span className="eyebrow">只读提示词 · v{prompt?.version || "1.2"}</span><h2>笔记详细程度与生成规则</h2></div>
          <button className="icon-button" onClick={onClose} aria-label="关闭"><X size={18} /></button>
        </div>
        <div className="prompt-tabs">
          {prompts.map((item) => (
            <button key={item.id} className={active === item.id ? "selected" : ""} onClick={() => setActive(item.id)}>
              <strong>{item.name}</strong><span>{item.description}</span>
            </button>
          ))}
        </div>
        {prompt && (
          <div className="prompt-content">
            <section><strong>系统规则</strong><pre>{prompt.system_prompt}</pre></section>
            <section><strong>逐段整理规则</strong><pre>{prompt.module_instruction}</pre></section>
            <section><strong>整节总览规则</strong><pre>{prompt.overview_instruction}</pre></section>
          </div>
        )}
        <div className="privacy-note">提示词由版本控制，只能查看和选择，不能在此修改。更改只影响这节课下一次生成或重新生成的笔记。</div>
        <div className="dialog-actions">
          <button className="button ghost" onClick={onClose}>关闭</button>
          <button
            className="button primary"
            disabled={busy || active === selected}
            onClick={async () => { setBusy(true); try { await onSelect(active); onClose(); } finally { setBusy(false); } }}
          >
            {busy && <LoaderCircle className="spin" size={15} />} 使用这套提示词
          </button>
        </div>
      </div>
    </div>
  );
}

function TaskManageDialog({
  task,
  onClose,
  onRename,
  onRegenerate,
  onDelete,
}: {
  task: Task;
  onClose: () => void;
  onRename: (title: string) => Promise<void>;
  onRegenerate: () => Promise<void>;
  onDelete: () => Promise<void>;
}) {
  const [title, setTitle] = useState(task.title);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  async function run(action: string, callback: () => Promise<void>) {
    setBusy(action);
    setMessage("");
    try {
      await callback();
      if (action === "rename") setMessage("任务名称已更新。");
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "操作失败");
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="dialog task-manage-dialog" onMouseDown={(event) => event.stopPropagation()}>
        <div className="dialog-header">
          <div><span className="eyebrow">任务管理</span><h2>管理学习任务</h2></div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="关闭"><X size={18} /></button>
        </div>
        <label>
          任务名称
          <input value={title} onChange={(event) => setTitle(event.target.value)} />
        </label>
        <button
          className="button secondary full-width"
          disabled={!title.trim() || title.trim() === task.title || Boolean(busy)}
          onClick={() => run("rename", () => onRename(title.trim()))}
        >
          保存任务名称
        </button>
        <div className="manage-section">
          <strong>速学速记</strong>
          <p>复用任务中已经保存的字幕或转写文字，按新的固定模板重新生成，不会重新下载课程音轨。</p>
          <button
            className="button ghost full-width"
            disabled={Boolean(busy)}
            onClick={() => run("regenerate", onRegenerate)}
          >
            <RefreshCw size={15} /> 重新生成速学速记
          </button>
        </div>
        <div className="manage-section danger-zone">
          <strong>删除任务</strong>
          <p>删除任务数据库记录、课程音轨和该任务的导出文件；共享的本地 Whisper 模型不会删除。</p>
          <button className="button danger full-width" disabled={Boolean(busy)} onClick={() => run("delete", onDelete)}>
            <Trash2 size={15} /> 永久删除这个任务
          </button>
        </div>
        {message && <div className="settings-message">{message}</div>}
      </div>
    </div>
  );
}

function LessonNameDialog({
  source,
  uiLanguage,
  onClose,
  onSave,
}: {
  source: Source;
  uiLanguage: UiLanguage;
  onClose: () => void;
  onSave: (title: string) => Promise<void>;
}) {
  const [title, setTitle] = useState(source.custom_title);
  const [busy, setBusy] = useState(false);
  const defaultName = translateUiText(`第 ${source.lesson_index} 节`, uiLanguage);
  const namingHint = uiLanguage === "zh-CN"
    ? `留空时使用默认名称“${defaultName}”。网页原始课程标题仍会保留为来源信息。`
    : uiLanguage === "en"
      ? `Leave blank to use the default name “${defaultName}”. The original page title is preserved as source information.`
      : `Leer lassen, um den Standardnamen „${defaultName}“ zu verwenden. Der ursprüngliche Seitentitel bleibt als Quelleninformation erhalten.`;
  async function save(value: string) {
    setBusy(true);
    try {
      await onSave(value.trim());
      onClose();
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="dialog lesson-name-dialog" onMouseDown={(event) => event.stopPropagation()}>
        <div className="dialog-header">
          <div><span className="eyebrow">课程命名</span><h2>设置课程名称</h2></div>
          <button className="icon-button" onClick={onClose} aria-label="关闭"><X size={18} /></button>
        </div>
        <label>
          自定义名称
          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder={defaultName} maxLength={200} autoFocus />
        </label>
        <div className="privacy-note">{namingHint}</div>
        <div className="dialog-actions">
          <button className="button ghost" onClick={() => void save("")} disabled={busy || !source.custom_title}>恢复默认名称</button>
          <button className="button primary" onClick={() => void save(title)} disabled={busy || title.trim() === source.custom_title}>
            {busy && <LoaderCircle className="spin" size={15} />} 保存课程名称
          </button>
        </div>
      </div>
    </div>
  );
}

function ConversationManageDialog({
  conversations,
  selectedId,
  uiLanguage,
  onOpen,
  onRename,
  onDelete,
  onClear,
  onClose,
}: {
  conversations: Conversation[];
  selectedId: string | null;
  uiLanguage: UiLanguage;
  onOpen: (id: string) => void;
  onRename: (id: string, title: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onClear: () => Promise<void>;
  onClose: () => void;
}) {
  const [activeId, setActiveId] = useState(selectedId || conversations[0]?.id || "");
  const active = conversations.find((item) => item.id === activeId) || null;
  const [title, setTitle] = useState(active?.title || "");
  const [busy, setBusy] = useState(false);
  useEffect(() => setTitle(active?.title || ""), [active?.id, active?.title]);
  useEffect(() => {
    if (activeId && !conversations.some((item) => item.id === activeId)) {
      setActiveId(conversations[0]?.id || "");
    }
  }, [activeId, conversations]);
  async function run(callback: () => Promise<void>) {
    setBusy(true);
    try { await callback(); } finally { setBusy(false); }
  }
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="dialog conversation-manage-dialog" onMouseDown={(event) => event.stopPropagation()}>
        <div className="dialog-header">
          <div><span className="eyebrow">课程问答</span><h2>管理对话</h2></div>
          <button className="icon-button" onClick={onClose} aria-label="关闭"><X size={18} /></button>
        </div>
        {conversations.length ? (
          <>
            <div className="conversation-manage-list">
              {conversations.map((conversation) => (
                <button key={conversation.id} className={activeId === conversation.id ? "selected" : ""} onClick={() => setActiveId(conversation.id)}>
                  <strong>{conversation.title}</strong><span>{formatDate(conversation.updated_at, uiLanguage)}</span>
                </button>
              ))}
            </div>
            {active && (
              <div className="conversation-editor">
                <label>对话名称<input value={title} maxLength={200} onChange={(event) => setTitle(event.target.value)} /></label>
                <div className="dialog-actions split-actions">
                  <button className="button ghost" onClick={() => { onOpen(active.id); onClose(); }}>打开对话</button>
                  <button className="button secondary" disabled={busy || !title.trim() || title.trim() === active.title} onClick={() => void run(() => onRename(active.id, title.trim()))}>保存名称</button>
                  <button className="button danger" disabled={busy} onClick={() => void run(() => onDelete(active.id))}><Trash2 size={14} /> 删除对话</button>
                </div>
              </div>
            )}
            <button className="button danger full-width" disabled={busy} onClick={() => void run(onClear)}>清空全部对话</button>
          </>
        ) : <div className="empty-list">还没有保存的对话。</div>}
      </div>
    </div>
  );
}

function StatusWidget() {
  const [task, setTask] = useState<Task | null>(null);
  const [source, setSource] = useState<Source | null>(null);
  const [ready, setReady] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [uiLanguage, setUiLanguage] = useState<UiLanguage>("zh-CN");
  const petDragOrigin = useRef<{ pointerId: number; screenX: number; screenY: number } | null>(null);
  const suppressPetClick = useRef(false);
  const dragResetTimer = useRef<number | null>(null);

  useEffect(() => localizeUi(document.body, uiLanguage), [uiLanguage]);

  useEffect(() => {
    document.documentElement.classList.add("status-window-root");
    if (window.__TAURI_INTERNALS__) {
      void import("@tauri-apps/api/core").then(({ invoke }) =>
        invoke("set_status_window_expanded", { expanded: false }),
      );
    }
    return () => {
      document.documentElement.classList.remove("status-window-root");
      if (dragResetTimer.current !== null) window.clearTimeout(dragResetTimer.current);
    };
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [tasks, preferences] = await Promise.all([
        api.listTasks(),
        api.preferences().catch(() => ({ ui_language: "zh-CN" as const })),
      ]);
      const nextTask =
        tasks.find((item) => ACTIVE_STATES.includes(item.status))
        || tasks.find((item) => item.status === "PAUSED")
        || tasks[0]
        || null;
      setTask(nextTask);
      if (nextTask) {
        const sources = await api.listSources(nextTask.id).catch(() => [] as Source[]);
        const nextSource =
          sources.find((item) => ACTIVE_STATES.includes(item.status))
          || sources.find((item) => item.status === "PAUSED")
          || [...sources].sort((left, right) => right.lesson_index - left.lesson_index)[0]
          || null;
        setSource(nextSource);
      } else {
        setSource(null);
      }
      setUiLanguage(preferences.ui_language);
      setReady(true);
    } catch {
      setReady(false);
    }
  }, []);

  useEffect(() => {
    void initializeConnection().then(refresh);
    const interval = window.setInterval(refresh, 2000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  async function setPanelOpen(next: boolean) {
    if (window.__TAURI_INTERNALS__) {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("set_status_window_expanded", { expanded: next });
    }
    setExpanded(next);
  }

  async function openMain() {
    if (window.__TAURI_INTERNALS__) {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("show_main_window");
    }
  }

  async function toggle() {
    if (!task) return;
    await api.control(task.id, task.status === "PAUSED" ? "resume" : "pause");
    await refresh();
  }

  async function hideStatus() {
    if (window.__TAURI_INTERNALS__) {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("set_status_window_expanded", { expanded: false });
      setExpanded(false);
      await invoke("toggle_status_window");
    }
  }

  function beginPetDrag(event: ReactPointerEvent<HTMLButtonElement>) {
    if (!window.__TAURI_INTERNALS__ || !event.isPrimary || event.button !== 0) return;
    petDragOrigin.current = {
      pointerId: event.pointerId,
      screenX: event.screenX,
      screenY: event.screenY,
    };
    suppressPetClick.current = false;
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function continuePetDrag(event: ReactPointerEvent<HTMLButtonElement>) {
    const origin = petDragOrigin.current;
    if (!origin || origin.pointerId !== event.pointerId || suppressPetClick.current) return;
    if (Math.hypot(event.screenX - origin.screenX, event.screenY - origin.screenY) < 4) return;

    petDragOrigin.current = null;
    suppressPetClick.current = true;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    void getCurrentWindow()
      .startDragging()
      .catch(() => {
        suppressPetClick.current = false;
      })
      .finally(() => {
        if (dragResetTimer.current !== null) window.clearTimeout(dragResetTimer.current);
        dragResetTimer.current = window.setTimeout(() => {
          suppressPetClick.current = false;
          dragResetTimer.current = null;
        }, 500);
      });
  }

  function endPetDrag(event: ReactPointerEvent<HTMLButtonElement>) {
    if (petDragOrigin.current?.pointerId === event.pointerId) petDragOrigin.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  function activatePet() {
    if (suppressPetClick.current) {
      suppressPetClick.current = false;
      return;
    }
    void setPanelOpen(!expanded);
  }

  const meta = task ? STATUS_META[task.status] : STATUS_META.IDLE;
  const isWorking = Boolean(task && ACTIVE_STATES.includes(task.status));
  const petImage = isWorking ? workingPet : idlePet;
  const petMode = isWorking ? "working" : "idle";
  const taskTitle = task?.title || translateUiText(ready ? "学习助手待命" : "正在连接助手", uiLanguage);
  const sourceTitle = source
    ? source.custom_title.trim() || translateUiText(`第 ${source.lesson_index} 节`, uiLanguage)
    : translateUiText("暂无正在处理的课程小节", uiLanguage);
  const stateLabel = translateUiText(meta.label, uiLanguage);
  const detail = translateUiText(task?.status_detail || meta.action, uiLanguage);
  const progress = Math.round((source?.progress ?? task?.progress ?? 0) * 100);

  return (
    <main className={`pet-window pet-${petMode} ${expanded ? "is-expanded" : "is-collapsed"}`}>
      {expanded && (
        <section className={`pet-task-board status-${meta.tone}`}>
          <header className="pet-board-header">
            <div>
              <span>{translateUiText("当前任务", uiLanguage)}</span>
              <strong title={taskTitle}>{taskTitle}</strong>
            </div>
            <button
              onClick={() => void setPanelOpen(false)}
              aria-label={translateUiText("收起当前任务", uiLanguage)}
            >
              <X size={15} />
            </button>
          </header>

          {task ? (
            <>
              <div className="pet-lesson-line" title={sourceTitle}>
                <BookOpen size={14} />
                <span>{sourceTitle}</span>
              </div>
              <p className="pet-status-detail">{detail}</p>
              <div className="pet-board-progress" aria-label={`${progress}%`}>
                <i style={{ width: `${progress}%` }} />
              </div>
              <div className="pet-progress-copy">
                <span>{stateLabel}</span>
                <strong>{progress}%</strong>
              </div>
            </>
          ) : (
            <p className="pet-empty-copy">{translateUiText("暂无运行中的任务", uiLanguage)}</p>
          )}

          <div className="pet-board-actions">
            <button onClick={openMain} title={translateUiText("打开主界面", uiLanguage)}>
              <PanelsTopLeft size={15} />
              <span>{translateUiText("打开主界面", uiLanguage)}</span>
            </button>
            {task && (isWorking || task.status === "PAUSED") && (
              <button onClick={toggle} title={translateUiText("暂停或继续", uiLanguage)}>
                {task.status === "PAUSED" ? <CirclePlay size={15} /> : <CirclePause size={15} />}
                <span>{translateUiText(task.status === "PAUSED" ? "继续" : "暂停", uiLanguage)}</span>
              </button>
            )}
            <button
              className="pet-hide-button"
              onClick={hideStatus}
              title={translateUiText("隐藏电子宠物", uiLanguage)}
            >
              <X size={15} />
              <span>{translateUiText("隐藏", uiLanguage)}</span>
            </button>
          </div>
        </section>
      )}

      <section className="pet-stage">
        <button
          className="pet-avatar"
          onClick={activatePet}
          onPointerDown={beginPetDrag}
          onPointerMove={continuePetDrag}
          onPointerUp={endPetDrag}
          onPointerCancel={endPetDrag}
          aria-label={translateUiText(expanded ? "收起当前任务" : "查看当前任务", uiLanguage)}
        >
          <img key={petImage} src={petImage} alt="Study Assistant" draggable={false} />
          <span className={`pet-state-chip status-${meta.tone}`}>
            <i /> {stateLabel}
          </span>
        </button>
        <div
          className="pet-drag-handle"
          title={translateUiText("拖动电子宠物", uiLanguage)}
          aria-hidden="true"
        >
          <GripHorizontal size={15} />
        </div>
      </section>
    </main>
  );
}

function SplashScreen() {
  useEffect(() => {
    document.documentElement.classList.add("splash-window-root");
    const finishTimer = window.setTimeout(async () => {
      if (window.__TAURI_INTERNALS__) {
        const { invoke } = await import("@tauri-apps/api/core");
        await invoke("finish_splash");
      }
    }, 3200);
    return () => {
      document.documentElement.classList.remove("splash-window-root");
      window.clearTimeout(finishTimer);
    };
  }, []);

  return (
    <main className="splash-screen" aria-label={`Study Assistant ${__APP_VERSION__} startup`}>
      <img
        src={wakePet}
        alt={`Study Assistant ${__APP_VERSION__} — Dedicated to Xiaowei`}
        draggable={false}
      />
    </main>
  );
}

function MainApp() {
  const [connected, setConnected] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [capability, setCapability] = useState<CapabilityReport | null>(null);
  const [notes, setNotes] = useState<NoteBlock[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [newDialog, setNewDialog] = useState(false);
  const [settingsDialog, setSettingsDialog] = useState(false);
  const [taskManageDialog, setTaskManageDialog] = useState(false);
  const [lessonNameDialog, setLessonNameDialog] = useState(false);
  const [conversationManageDialog, setConversationManageDialog] = useState(false);
  const [promptDialog, setPromptDialog] = useState(false);
  const [prompts, setPrompts] = useState<PromptPreset[]>([]);
  const [providerSettings, setProviderSettings] = useState<ProviderSettings>(EMPTY_SETTINGS);
  const [semanticStatus, setSemanticStatus] = useState<SemanticStatus>(EMPTY_SEMANTIC_STATUS);
  const [providerTestPassed, setProviderTestPassed] = useState(false);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [uiLanguage, setUiLanguage] = useState<UiLanguage>("zh-CN");
  const chatEnd = useRef<HTMLDivElement>(null);
  const selectedSourceRef = useRef<string | null>(null);

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedId) || null,
    [tasks, selectedId],
  );
  const selectedSource = useMemo(
    () => sources.find((source) => source.id === selectedSourceId) || sources.at(-1) || null,
    [sources, selectedSourceId],
  );
  const lessonDisplayName = useCallback(
    (source: Source) => source.custom_title || translateUiText(`第 ${source.lesson_index} 节`, uiLanguage),
    [uiLanguage],
  );

  useEffect(() => localizeUi(document.body, uiLanguage), [uiLanguage]);

  const refreshTasks = useCallback(async () => {
    const result = await api.listTasks();
    setTasks(result);
    setSelectedId((current) => current || result[0]?.id || null);
  }, []);

  const loadTaskDetails = useCallback(async (taskId: string, preferredSourceId?: string | null) => {
    const nextSources = await api.listSources(taskId);
    const preferred = preferredSourceId ?? selectedSourceRef.current;
    const lessonId = nextSources.some((item) => item.id === preferred)
      ? preferred
      : nextSources.at(-1)?.id || null;
    const [nextCapability, nextNotes, nextConversations] = await Promise.all([
      api.capability(taskId, lessonId),
      api.notes(taskId, lessonId),
      api.conversations(taskId),
    ]);
    setSources(nextSources);
    setSelectedSourceId(lessonId);
    selectedSourceRef.current = lessonId;
    setCapability(nextCapability);
    setNotes(nextNotes);
    setConversations(nextConversations);
    setConversationId((current) =>
      current && nextConversations.some((item) => item.id === current)
        ? current
        : nextConversations[0]?.id || null,
    );
  }, []);

  useEffect(() => {
    let stream: EventSource | null = null;
    void initializeConnection()
      .then(async () => {
        await waitForAgent();
        setConnected(true);
        const preferences = await api.preferences().catch(() => ({ ui_language: "zh-CN" as const }));
        setUiLanguage(preferences.ui_language);
        await Promise.all([
          refreshTasks(),
          api.settings().then(setProviderSettings),
          api.semanticStatus().then(setSemanticStatus),
          api.prompts(preferences.ui_language).then(setPrompts),
        ]);
        stream = new EventSource(eventUrl());
        const taskListener = (event: MessageEvent) => {
          const payload = JSON.parse(event.data).payload as Task;
          setTasks((current) => {
            const exists = current.some((item) => item.id === payload.id);
            return exists
              ? current.map((item) => (item.id === payload.id ? payload : item))
              : [payload, ...current];
          });
        };
        for (const type of ["task.created", "task.updated"]) {
          stream.addEventListener(type, taskListener as EventListener);
        }
        const contentListener = () => {
          if (selectedId) void loadTaskDetails(selectedId);
        };
        stream.addEventListener("note.created", contentListener);
        stream.addEventListener("task.completed", contentListener);
        stream.addEventListener("task.error", ((event: MessageEvent) => {
          const payload = JSON.parse(event.data).payload as { message?: string };
          setError(payload.message || "课程处理失败，请检查 API 设置后重试。");
        }) as EventListener);
        stream.addEventListener("semantic.status", ((event: MessageEvent) => {
          const payload = JSON.parse(event.data).payload as SemanticStatus;
          setSemanticStatus(payload);
        }) as EventListener);
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "无法连接本地 Agent 服务");
      });
    return () => stream?.close();
  }, [loadTaskDetails, refreshTasks, selectedId]);

  useEffect(() => {
    if (!selectedId) {
      setSources([]);
      setSelectedSourceId(null);
      setCapability(null);
      setNotes([]);
      setConversations([]);
      setMessages([]);
      return;
    }
    selectedSourceRef.current = selectedSourceId;
    void loadTaskDetails(selectedId, selectedSourceId).catch((caught) =>
      setError(caught instanceof Error ? caught.message : "读取任务失败"),
    );
  }, [loadTaskDetails, selectedId, selectedSourceId]);

  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    void api.messages(conversationId).then(setMessages).catch(() => setMessages([]));
  }, [conversationId]);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function createOrContinue(input: {
    mode: "new" | "existing";
    taskId: string;
    title: string;
    lessons: LessonCandidate[];
    language: string;
    promptPresetId: "quick" | "standard" | "deep";
    outputLanguage: "auto" | "zh-CN" | "en" | "de";
  }) {
    setBusy("create");
    setError("");
    try {
      const task =
        input.mode === "new"
          ? await api.createTask({
              title: input.title,
              language: input.language,
            })
          : tasks.find((item) => item.id === input.taskId)!;
      const added: Source[] = [];
      for (const candidate of input.lessons) {
        const lesson = await api.addLesson(task.id, {
          url: candidate.url,
          prompt_preset_id: input.promptPresetId,
          output_language: input.outputLanguage,
        });
        added.push(lesson);
      }
      const lesson = added[0];
      setSelectedId(task.id);
      setSelectedSourceId(lesson.id);
      await refreshTasks();
      const report = await api.check(task.id, lesson.id);
      setCapability(report);
      await Promise.all([refreshTasks(), loadTaskDetails(task.id, lesson.id)]);
    } finally {
      setBusy("");
    }
  }

  async function control(action: "run" | "pause" | "resume" | "stop") {
    if (!selectedTask) return;
    if (action === "stop" && !window.confirm(translateUiText("停止任务？已经生成的字幕和笔记会保留。", uiLanguage))) return;
    setBusy(action);
    setError("");
    try {
      await api.control(selectedTask.id, action, selectedSource?.id);
      await refreshTasks();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "操作失败");
    } finally {
      setBusy("");
    }
  }

  async function recheck() {
    if (!selectedTask) return;
    setBusy("check");
    try {
      setCapability(await api.check(selectedTask.id, selectedSource?.id));
      await refreshTasks();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "检查失败");
    } finally {
      setBusy("");
    }
  }

  async function sendQuestion(event: FormEvent) {
    event.preventDefault();
    if (!selectedTask || !providerUsable || !question.trim()) return;
    const content = question.trim();
    setQuestion("");
    setBusy("chat");
    const optimistic: Message = {
      id: `local-${Date.now()}`,
      conversation_id: conversationId || "",
      role: "user",
      content,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages((current) => [...current, optimistic]);
    try {
      const response = await api.chat(selectedTask.id, {
        question: content,
        conversation_id: conversationId,
      });
      setConversationId(response.conversation_id);
      setMessages((current) => [
        ...current,
        {
          id: response.message_id,
          conversation_id: response.conversation_id,
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          created_at: new Date().toISOString(),
        },
      ]);
      setConversations(await api.conversations(selectedTask.id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "回答失败");
    } finally {
      setBusy("");
    }
  }

  async function exportNotes() {
    if (!selectedTask) return;
    try {
      const result = await api.export(selectedTask.id, selectedSource?.id);
      setNotice(`笔记已导出：${result.path}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "导出失败");
    }
  }

  function saveProviderSettings(settings: ProviderSettings, testPassed: boolean) {
    setProviderSettings(settings);
    setProviderTestPassed(testPassed);
    if (testPassed && selectedTask) {
      void recheck();
    }
  }

  async function renameSelectedTask(title: string) {
    if (!selectedTask) return;
    const updated = await api.updateTask(selectedTask.id, { title });
    setTasks((current) => current.map((item) => (item.id === updated.id ? updated : item)));
  }

  async function renameSelectedLesson(title: string) {
    if (!selectedTask || !selectedSource) return;
    const updated = await api.updateLesson(selectedTask.id, selectedSource.id, {
      custom_title: title,
    });
    setSources((current) => current.map((item) => item.id === updated.id ? updated : item));
    setNotice(title ? "课程名称已更新。" : "课程已恢复默认名称。");
  }

  async function renameConversation(id: string, title: string) {
    if (!selectedTask) return;
    const updated = await api.updateConversation(selectedTask.id, id, title);
    setConversations((current) => current.map((item) => item.id === id ? updated : item));
  }

  async function deleteConversation(id: string) {
    if (!selectedTask || !window.confirm(translateUiText("永久删除这个对话？", uiLanguage))) return;
    await api.deleteConversation(selectedTask.id, id);
    const next = await api.conversations(selectedTask.id);
    setConversations(next);
    if (conversationId === id) setConversationId(next[0]?.id || null);
  }

  async function clearConversations() {
    if (!selectedTask || !window.confirm(translateUiText("永久删除当前任务的全部对话？", uiLanguage))) return;
    await api.clearConversations(selectedTask.id);
    setConversations([]);
    setConversationId(null);
    setMessages([]);
    setConversationManageDialog(false);
  }

  async function regenerateSelectedTask() {
    if (!selectedTask) return;
    if (!window.confirm(translateUiText("使用现有课程文字重新生成速学速记？当前笔记将被替换。", uiLanguage))) return;
    await api.regenerate(selectedTask.id, selectedSource?.id);
    setNotes([]);
    setTaskManageDialog(false);
    setNotice("正在基于现有课程文字重新生成速学速记。");
    await refreshTasks();
  }

  async function updatePromptPreset(id: Source["prompt_preset_id"]) {
    if (!selectedTask || !selectedSource) return;
    const updated = await api.updateLesson(selectedTask.id, selectedSource.id, {
      prompt_preset_id: id,
    });
    setSources((current) => current.map((item) => item.id === updated.id ? updated : item));
    setNotice("提示词方案已保存；重新生成本节笔记时生效。");
  }

  async function changeUiLanguage(language: UiLanguage) {
    setUiLanguage(language);
    await api.savePreferences(language);
    setPrompts(await api.prompts(language));
  }

  async function openDonationPage(event: ReactMouseEvent<HTMLAnchorElement>) {
    if (!window.__TAURI_INTERNALS__) return;
    event.preventDefault();
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("open_donation_page");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "无法打开捐赠页面");
    }
  }

  async function deleteSelectedLesson() {
    if (!selectedTask || !selectedSource) return;
    if (!window.confirm(translateUiText(`永久删除第 ${selectedSource.lesson_index} 节及其转写和笔记？`, uiLanguage))) return;
    await api.deleteLesson(selectedTask.id, selectedSource.id);
    setSelectedSourceId(null);
    await Promise.all([refreshTasks(), loadTaskDetails(selectedTask.id)]);
    setNotice("课程小节已删除。任务中的其他小节和问答仍然保留。");
  }

  async function deleteSelectedTask() {
    if (!selectedTask) return;
    if (!window.confirm(translateUiText(`永久删除任务“${selectedTask.title}”？此操作无法撤销。`, uiLanguage))) return;
    await api.deleteTask(selectedTask.id);
    const remaining = await api.listTasks();
    setTasks(remaining);
    setSelectedId(remaining[0]?.id || null);
    setTaskManageDialog(false);
    setNotice("学习任务及其关联文件已删除。");
  }

  const providerConfigured = Boolean(
    providerSettings.text_model && providerSettings.has_api_key,
  );
  const providerUsable = providerConfigured && providerTestPassed;
  const canStart = capability
    && ["READY", "LIMITED"].includes(capability.status)
    && providerUsable;
  const lessonStatus = selectedSource?.status || selectedTask?.status || "IDLE";
  const isActive = ACTIVE_STATES.includes(lessonStatus);

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><BookOpen size={20} /></div>
          <div><strong>Study Assistant</strong><span>课程理解工作台 · {__APP_VERSION__}</span></div>
        </div>
        <a
          className="donation-card"
          href="https://buymeacoffee.com/jeromerlon"
          target="_blank"
          rel="noreferrer"
          title="buymeacoffee.com/jeromerlon"
          onClick={openDonationPage}
        >
          <span className="donation-icon"><Coffee size={18} /></span>
          <span className="donation-copy">
            <small>支持 Study Assistant</small>
            <strong>请我喝杯咖啡</strong>
          </span>
          <ExternalLink size={13} />
        </a>
        <button className="new-task-button" onClick={() => setNewDialog(true)}>
          <Plus size={17} /> 添加公开课
        </button>
        <div className="sidebar-section-title"><span>学习任务</span><small>{tasks.length}</small></div>
        <nav className="task-list">
          {tasks.map((task) => (
            <button
              className={`task-item ${selectedId === task.id ? "selected" : ""}`}
              onClick={() => setSelectedId(task.id)}
              key={task.id}
            >
              <div className={`task-icon status-${STATUS_META[task.status].tone}`}>
                {ACTIVE_STATES.includes(task.status) ? <LoaderCircle className="spin" size={16} /> : <BookOpen size={16} />}
              </div>
              <div className="task-copy">
                <strong>{task.title}</strong>
                <span>{translateUiText(`${task.completed_lessons}/${task.lesson_count} 节已完成 · ${task.status_detail}`, uiLanguage)}</span>
                <div className="mini-progress"><i style={{ width: `${task.progress * 100}%` }} /></div>
              </div>
            </button>
          ))}
          {!tasks.length && <div className="empty-list">还没有课程。添加一个公开课网址开始学习。</div>}
        </nav>
        <div className="sidebar-footer">
          <label className="language-picker">
            <Globe2 size={15} />
            <select value={uiLanguage} onChange={(event) => void changeUiLanguage(event.target.value as UiLanguage)}>
              <option value="zh-CN">中文</option>
              <option value="en">English</option>
              <option value="de">Deutsch</option>
            </select>
          </label>
          <button onClick={() => setSettingsDialog(true)}><Settings2 size={16} /> 智能能力设置</button>
          <span className={connected ? "connection-ok" : "connection-off"}>
            <i /> {connected ? "本地 Agent 已连接" : "正在连接本地 Agent"}
          </span>
        </div>
      </aside>

      <section className="workspace">
        {selectedTask ? (
          <>
            <header className="workspace-header">
              <div>
                <div className="header-meta"><StatusPill status={lessonStatus} /><span>{formatDate(selectedTask.updated_at, uiLanguage)}</span></div>
                <h1>{selectedTask.title}</h1>
                <p>{selectedSource ? `${lessonDisplayName(selectedSource)} · ${translateUiText(selectedSource.status_detail || "等待处理", uiLanguage)}` : translateUiText("请添加课程小节", uiLanguage)}</p>
              </div>
              <div className="header-actions">
                <button
                  className={`button api-settings-button ${providerUsable ? "configured" : "missing"}`}
                  onClick={() => setSettingsDialog(true)}
                  title={providerTestPassed ? "文本模型连接测试已通过" : "打开 API 与模型设置"}
                >
                  <Settings2 size={15} /> {providerUsable ? "API 可用" : providerConfigured ? "API 待验证" : "配置 API"}
                </button>
                <button className="button ghost" onClick={() => setTaskManageDialog(true)} disabled={Boolean(busy)}><MoreHorizontal size={15} /> 管理任务</button>
                <button className="button ghost" onClick={() => setPromptDialog(true)} disabled={!selectedSource}><PanelsTopLeft size={15} /> 查看提示词</button>
                <button className="button ghost" onClick={recheck} disabled={Boolean(busy) || !selectedSource}><RefreshCw size={15} /> 重新检查</button>
                {isActive ? (
                  <button className="button secondary" onClick={() => control("pause")} disabled={Boolean(busy)}><CirclePause size={16} /> 暂停</button>
                ) : lessonStatus === "PAUSED" ? (
                  <button className="button primary" onClick={() => control("resume")} disabled={Boolean(busy)}><CirclePlay size={16} /> 继续</button>
                ) : lessonStatus === "READY_FOR_QA" ? (
                  <button className="button secondary" onClick={regenerateSelectedTask} disabled={!providerUsable || Boolean(busy)}><RefreshCw size={15} /> 重新生成笔记</button>
                ) : (
                  <button className="button primary" onClick={() => control("run")} disabled={!canStart || Boolean(busy)}><CirclePlay size={16} /> 开始记录</button>
                )}
                {(isActive || selectedTask.status === "PAUSED") && (
                  <button className="icon-button danger" onClick={() => control("stop")} aria-label="停止"><Square size={15} /></button>
                )}
              </div>
            </header>
            <div className="course-progress"><i style={{ width: `${(selectedSource?.progress || 0) * 100}%` }} /></div>
            <div className="content-scroll">
              <section className="lesson-browser">
                <div className="lesson-browser-heading">
                  <div><span className="eyebrow">课程目录</span><strong>{translateUiText(`${selectedTask.completed_lessons}/${selectedTask.lesson_count} 节已完成`, uiLanguage)}</strong></div>
                  <button className="button ghost" onClick={() => setNewDialog(true)}><Plus size={14} /> 添加下一节</button>
                </div>
                <div className="lesson-tabs">
                  {sources.map((source) => (
                    <button
                      key={source.id}
                      className={selectedSource?.id === source.id ? "selected" : ""}
                      onClick={() => setSelectedSourceId(source.id)}
                    >
                      <span>{translateUiText("课程小节", uiLanguage)}</span>
                      <strong>{lessonDisplayName(source)}</strong>
                      <small>{STATUS_META[source.status].label} · {source.title || new URL(source.url).hostname}</small>
                      <i><em style={{ width: `${source.progress * 100}%` }} /></i>
                    </button>
                  ))}
                </div>
              </section>
              {capability && <CapabilityCard report={capability} />}
              {selectedSource && (
                <section className="source-strip">
                  <Globe2 size={16} />
                  <div><span>{lessonDisplayName(selectedSource)} · {prompts.find((item) => item.id === selectedSource.prompt_preset_id)?.name || selectedSource.prompt_preset_id}</span><strong>{selectedSource.title || selectedSource.url}</strong></div>
                  {selectedSource.duration_seconds && <small>{formatTime(selectedSource.duration_seconds)}</small>}
                  <a href={selectedSource.url} target="_blank" rel="noreferrer"><ExternalLink size={14} /></a>
                  <button className="icon-button" onClick={() => setLessonNameDialog(true)} title="重命名课程"><Pencil size={14} /></button>
                  <button className="icon-button danger" onClick={deleteSelectedLesson} title="删除本节"><Trash2 size={14} /></button>
                </section>
              )}
              <div className="section-heading">
                <div><span className="eyebrow">课程速学</span><h2>详细介绍与速学速记</h2></div>
                <button className="button ghost" onClick={exportNotes} disabled={!notes.length}><FileDown size={15} /> 导出速学笔记</button>
              </div>
              <div className="notes-list">
                {notes.map((note) => (
                  <article className="note-card" key={note.id}>
                    <div className="note-time"><span>{formatTime(note.start_seconds)}</span><i /><span>{formatTime(note.end_seconds)}</span></div>
                    <h3>{note.title}</h3>
                    <div className="markdown-body"><Markdown>{note.content}</Markdown></div>
                    <CitationList citations={note.citations} />
                  </article>
                ))}
                {!notes.length && (
                  <div className="empty-state">
                    <div><BookOpen size={24} /></div>
                    <h3>速学速记会在这里生成</h3>
                    <p>助手会先整理逐段知识，再把整节课汇总为详细内容介绍、知识地图和一页速记表。</p>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="welcome-state">
            <div className="welcome-orbit"><Sparkles /><i /><i /><i /></div>
            <span className="eyebrow">你的课程理解工作台</span>
            <h1>把公开课交给助手，<br />把注意力留给理解。</h1>
            <p>助手会定位课程视频、优先读取字幕，再将课程内容整理成详细介绍、知识地图和速学速记。</p>
            <button className="button primary large" onClick={() => setNewDialog(true)}><Plus size={18} /> 添加第一个公开课</button>
            <div className="welcome-features"><span><Gauge />先检查能力</span><span><BookOpen />课程优先笔记</span><span><MessageCircle />独立任务问答</span></div>
          </div>
        )}
      </section>

      <aside className="chat-panel">
        <header className="chat-header">
          <div><span className="eyebrow">课程问答</span><h2>向助手提问</h2></div>
          <button className="icon-button" onClick={() => setConversationManageDialog(true)} title="管理对话"><MoreHorizontal size={18} /></button>
        </header>
        {selectedTask && (
          <div className="chat-knowledge-policy">
            <Sparkles size={15} />
            <div><strong>课程优先 · 模型知识补充</strong><span>课程证据优先；未覆盖部分由当前模型知识补充，未经实时联网核实。</span></div>
          </div>
        )}
        <div className="conversation-tabs">
          {conversations.slice(0, 4).map((conversation) => (
            <button className={conversationId === conversation.id ? "selected" : ""} onClick={() => setConversationId(conversation.id)} key={conversation.id}>{conversation.title}</button>
          ))}
          {selectedTask && <button onClick={() => setConversationId(null)}><Plus size={13} /> 新对话</button>}
        </div>
        {selectedTask && !providerUsable && (
          <button className="chat-api-warning" onClick={() => setSettingsDialog(true)}>
            <AlertTriangle size={14} /> 请先配置并通过 API 连接测试
          </button>
        )}
        <div className="messages">
          {!selectedTask ? (
            <div className="chat-empty"><MessageCircle /><p>选择一个学习任务后开始提问。</p></div>
          ) : !messages.length ? (
            <div className="chat-empty"><Sparkles /><h3>从课程内容开始</h3><p>例如：“老师为什么这样定义？”或“总结这一节的推导过程。”</p></div>
          ) : (
            messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                <div className="message-role">{message.role === "user" ? "你" : "Study Assistant"}</div>
                <div className="markdown-body"><Markdown>{message.content}</Markdown></div>
                <CitationList citations={message.citations} />
              </article>
            ))
          )}
          {busy === "chat" && <div className="thinking"><LoaderCircle className="spin" /> 正在核对课程证据…</div>}
          <div ref={chatEnd} />
        </div>
        <form className="chat-composer" onSubmit={sendQuestion}>
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={!selectedTask ? "请先选择任务" : providerUsable ? "主要基于课程内容提问…" : "请先配置并测试 API"} disabled={!selectedTask || !providerUsable} rows={3} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} />
          <div><span>课程优先 · 模型知识补充</span><button type="submit" disabled={!question.trim() || busy === "chat" || !providerUsable}><ChevronRight size={18} /></button></div>
        </form>
      </aside>

      {(error || notice) && <div className={`toast ${error ? "error" : "success"}`}><AlertTriangle size={16} /><span>{error || notice}</span><button onClick={() => { setError(""); setNotice(""); }}><X size={14} /></button></div>}
      {newDialog && <NewTaskDialog tasks={tasks} onClose={() => setNewDialog(false)} onSubmit={createOrContinue} />}
      {settingsDialog && <SettingsDialog initial={providerSettings} semanticStatus={semanticStatus} onClose={() => setSettingsDialog(false)} onSaved={saveProviderSettings} />}
      {promptDialog && selectedSource && (
        <PromptDialog
          prompts={prompts}
          selected={selectedSource.prompt_preset_id}
          onSelect={updatePromptPreset}
          onClose={() => setPromptDialog(false)}
        />
      )}
      {taskManageDialog && selectedTask && (
        <TaskManageDialog
          task={selectedTask}
          onClose={() => setTaskManageDialog(false)}
          onRename={renameSelectedTask}
          onRegenerate={regenerateSelectedTask}
          onDelete={deleteSelectedTask}
        />
      )}
      {lessonNameDialog && selectedSource && (
        <LessonNameDialog
          source={selectedSource}
          uiLanguage={uiLanguage}
          onClose={() => setLessonNameDialog(false)}
          onSave={renameSelectedLesson}
        />
      )}
      {conversationManageDialog && selectedTask && (
        <ConversationManageDialog
          conversations={conversations}
          selectedId={conversationId}
          uiLanguage={uiLanguage}
          onOpen={setConversationId}
          onRename={renameConversation}
          onDelete={deleteConversation}
          onClear={clearConversations}
          onClose={() => setConversationManageDialog(false)}
        />
      )}
    </main>
  );
}

export default function App() {
  const windowKind = new URLSearchParams(window.location.search).get("window");
  if (windowKind === "splash") return <SplashScreen />;
  if (windowKind === "status") return <StatusWidget />;
  return <MainApp />;
}
