export type TaskStatus =
  | "IDLE"
  | "CHECKING"
  | "WATCHING"
  | "TRANSCRIBING"
  | "NOTE_TAKING"
  | "NEEDS_USER"
  | "PAUSED"
  | "READY_FOR_QA"
  | "UNSUPPORTED"
  | "FAILED"
  | "STOPPED";

export type CapabilityStatus = "READY" | "LIMITED" | "NEEDS_USER" | "UNSUPPORTED";

export interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  language: string;
  progress: number;
  status_detail: string;
  created_at: string;
  updated_at: string;
  lesson_count: number;
  completed_lessons: number;
}

export interface Source {
  id: string;
  task_id: string;
  url: string;
  title: string;
  custom_title: string;
  platform: string;
  duration_seconds: number | null;
  lesson_index: number;
  status: TaskStatus;
  progress: number;
  status_detail: string;
  prompt_preset_id: "quick" | "standard" | "deep";
  prompt_version: string;
  output_language: "auto" | "zh-CN" | "en" | "de";
  created_at: string;
}

export interface CapabilityReport {
  id: string;
  task_id: string;
  source_id: string;
  status: CapabilityStatus;
  page_accessible: boolean;
  video_detected: boolean;
  captions_available: boolean;
  audio_available: boolean;
  drm_detected: boolean;
  login_required: boolean;
  text_model_available: boolean;
  transcription_available: boolean;
  duration_seconds: number | null;
  estimated_minutes: number | null;
  reasons: string[];
  suggestions: string[];
  details: Record<string, unknown>;
  created_at: string;
}

export interface NoteBlock {
  id: string;
  task_id: string;
  source_id: string | null;
  kind: string;
  title: string;
  content: string;
  start_seconds: number | null;
  end_seconds: number | null;
  citations: Citation[];
  prompt_preset_id: string;
  prompt_version: string;
  output_language: string;
  created_at: string;
}

export interface Citation {
  source_type: "course" | "external";
  title: string;
  url: string | null;
  start_seconds: number | null;
  end_seconds: number | null;
  excerpt: string;
  source_id?: string | null;
  lesson_index?: number | null;
}

export interface PromptPreset {
  id: "quick" | "standard" | "deep";
  name: string;
  description: string;
  module_instruction: string;
  overview_instruction: string;
  system_prompt: string;
  max_tokens: number;
  version: string;
  read_only: true;
}

export interface LessonCandidate {
  url: string;
  title: string;
}

export type UiLanguage = "zh-CN" | "en" | "de";

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface Conversation {
  id: string;
  task_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface AgentConnection {
  baseUrl: string;
  token: string;
  launchError?: string | null;
}

export interface ProviderSettings {
  api_base_url: string;
  api_key?: string;
  text_model: string;
  reasoning_effort: "low" | "high" | "max";
  local_whisper_model: "small" | "medium" | "large-v3";
  has_api_key?: boolean;
}

export interface SemanticStatus {
  state: "NOT_READY" | "DOWNLOADING" | "PREPARING" | "INDEXING" | "READY" | "FAILED";
  model: string;
  model_revision: string;
  runtime_available: boolean;
  model_downloaded: boolean;
  progress: number;
  indexed_sources: number;
  pending_sources: number;
  indexed_chunks: number;
  message: string;
}
