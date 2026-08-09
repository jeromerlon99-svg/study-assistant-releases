import type {
  AgentConnection,
  CapabilityReport,
  Conversation,
  Message,
  LessonCandidate,
  NoteBlock,
  PromptPreset,
  ProviderSettings,
  SemanticStatus,
  Source,
  Task,
} from "./types";

let connection: AgentConnection = {
  baseUrl: import.meta.env.VITE_AGENT_URL || "http://127.0.0.1:8765",
  token: import.meta.env.VITE_AGENT_TOKEN || "",
  launchError: null,
};

export async function initializeConnection(): Promise<AgentConnection> {
  if (window.__TAURI_INTERNALS__) {
    const { invoke } = await import("@tauri-apps/api/core");
    connection = await invoke<AgentConnection>("agent_connection");
  }
  return connection;
}

export async function waitForAgent(timeoutMs = 30_000): Promise<void> {
  if (connection.launchError) throw new Error(connection.launchError);
  const deadline = Date.now() + timeoutMs;
  let lastError: unknown = null;
  while (Date.now() < deadline) {
    try {
      await request<Record<string, unknown>>("/health");
      return;
    } catch (error) {
      lastError = error;
      await new Promise((resolve) => window.setTimeout(resolve, 250));
    }
  }
  throw lastError instanceof Error
    ? lastError
    : new Error("本地 Agent 在 30 秒内未能启动，请查看运行日志。");
}

function headers(hasBody = false): HeadersInit {
  const result: Record<string, string> = {};
  if (hasBody) result["Content-Type"] = "application/json";
  if (connection.token) result["X-Study-Assistant-Token"] = connection.token;
  return result;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${connection.baseUrl}${path}`, {
    ...init,
    headers: { ...headers(Boolean(init.body)), ...(init.headers || {}) },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    const message =
      typeof detail === "string" ? detail : detail?.message || `请求失败（${response.status}）`;
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => request<Record<string, unknown>>("/health"),
  listTasks: () => request<Task[]>("/tasks"),
  createTask: (payload: {
    title: string;
    language: string;
  }) => request<Task>("/tasks", { method: "POST", body: JSON.stringify(payload) }),
  updateTask: (id: string, payload: Partial<Pick<Task, "title">>) =>
    request<Task>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteTask: (id: string) =>
    request<{ task_id: string; deleted: boolean }>(`/tasks/${id}`, { method: "DELETE" }),
  addSource: (taskId: string, url: string) =>
    request<Source>(`/tasks/${taskId}/sources`, {
      method: "POST",
      body: JSON.stringify({ url }),
    }),
  addLesson: (
    taskId: string,
    payload: {
      url: string;
      custom_title?: string;
      prompt_preset_id: "quick" | "standard" | "deep";
      output_language: "auto" | "zh-CN" | "en" | "de";
    },
  ) => request<Source>(`/tasks/${taskId}/lessons`, { method: "POST", body: JSON.stringify(payload) }),
  updateLesson: (
    taskId: string,
    sourceId: string,
    payload: Partial<Pick<Source, "custom_title" | "prompt_preset_id" | "output_language">>,
  ) => request<Source>(`/tasks/${taskId}/lessons/${sourceId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  }),
  deleteLesson: (taskId: string, sourceId: string) =>
    request<{ source_id: string; deleted: boolean }>(`/tasks/${taskId}/lessons/${sourceId}`, {
      method: "DELETE",
    }),
  listSources: (taskId: string) => request<Source[]>(`/tasks/${taskId}/sources`),
  check: (taskId: string, sourceId?: string | null) =>
    request<CapabilityReport>(`/tasks/${taskId}/check${sourceId ? `?source_id=${sourceId}` : ""}`, { method: "POST" }),
  capability: (taskId: string, sourceId?: string | null) =>
    request<CapabilityReport | null>(`/tasks/${taskId}/capability${sourceId ? `?source_id=${sourceId}` : ""}`),
  control: (taskId: string, action: "run" | "pause" | "resume" | "stop", sourceId?: string | null) =>
    request<{ status: string; message: string }>(`/tasks/${taskId}/${action}${sourceId && action === "run" ? `?source_id=${sourceId}` : ""}`, {
      method: "POST",
    }),
  regenerate: (taskId: string, sourceId?: string | null) =>
    request<{ status: string; message: string }>(`/tasks/${taskId}/regenerate${sourceId ? `?source_id=${sourceId}` : ""}`, {
      method: "POST",
    }),
  notes: (taskId: string, sourceId?: string | null) => request<NoteBlock[]>(`/tasks/${taskId}/notes${sourceId ? `?source_id=${sourceId}` : ""}`),
  conversations: (taskId: string) =>
    request<Conversation[]>(`/tasks/${taskId}/conversations`),
  updateConversation: (taskId: string, conversationId: string, title: string) =>
    request<Conversation>(`/tasks/${taskId}/conversations/${conversationId}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }),
  deleteConversation: (taskId: string, conversationId: string) =>
    request<{ conversation_id: string; deleted: boolean }>(
      `/tasks/${taskId}/conversations/${conversationId}`,
      { method: "DELETE" },
    ),
  clearConversations: (taskId: string) =>
    request<{ deleted: number }>(`/tasks/${taskId}/conversations`, { method: "DELETE" }),
  messages: (conversationId: string) =>
    request<Message[]>(`/conversations/${conversationId}/messages`),
  chat: (
    taskId: string,
    payload: {
      question: string;
      conversation_id: string | null;
    },
  ) =>
    request<{
      conversation_id: string;
      message_id: string;
      answer: string;
      citations: Message["citations"];
      course_evidence_found: boolean;
      retrieval_queries: string[];
      course_evidence_count: number;
    }>(`/tasks/${taskId}/chat`, { method: "POST", body: JSON.stringify(payload) }),
  export: (taskId: string, sourceId?: string | null) =>
    request<{ path: string }>(`/tasks/${taskId}/export${sourceId ? `?source_id=${sourceId}` : ""}`, { method: "POST" }),
  prompts: (locale: string) => request<PromptPreset[]>(`/note-prompts?locale=${encodeURIComponent(locale)}`),
  discoverLessons: (url: string) =>
    request<LessonCandidate[]>(`/lessons/discover?url=${encodeURIComponent(url)}`),
  preferences: () => request<{ ui_language: "zh-CN" | "en" | "de" }>("/preferences"),
  savePreferences: (ui_language: "zh-CN" | "en" | "de") =>
    request<{ ui_language: "zh-CN" | "en" | "de" }>("/preferences", {
      method: "PUT",
      body: JSON.stringify({ ui_language }),
    }),
  settings: () => request<ProviderSettings>("/settings"),
  semanticStatus: () => request<SemanticStatus>("/semantic/status"),
  saveSettings: (payload: ProviderSettings) =>
    request<ProviderSettings>("/settings", { method: "PUT", body: JSON.stringify(payload) }),
  testSettings: () =>
    request<{
      text: boolean;
      transcription_configured: boolean;
      message: string;
    }>("/settings/self-test", { method: "POST" }),
};

export function eventUrl(): string {
  const query = connection.token ? `?token=${encodeURIComponent(connection.token)}` : "";
  return `${connection.baseUrl}/events${query}`;
}
