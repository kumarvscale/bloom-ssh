import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface StageProgress {
  name: string;
  status: 'pending' | 'running' | 'completed';
  avg_duration: number | null;
}

export interface RunStatus {
  is_running: boolean;
  started_at: string | null;
  last_updated: string | null;
  total_tests: number;
  completed_tests: number;
  failed_tests: number;
  pending_tests: number;
  progress_pct: number;
  current_behavior: string | null;
  current_turn_count: number | null;
  current_stage: string | null;
  eta_seconds: number | null;
  // Granular progress
  total_behaviors: number;
  turn_counts: number[];
  stages: StageProgress[];
  current_test_number: number;
  stage_timings: Record<string, number> | null;
}

export interface JudgmentStats {
  count: number;
  average: number | null;
  min_score: number | null;
  max_score: number | null;
  median: number | null;
  range_1_2: number;   // 1-2
  range_3_4: number;   // 3-4
  range_5_6: number;   // 5-6
  range_7_8: number;   // 7-8
  range_9_10: number;  // 9-10
}

export interface Stats {
  total_behaviors: number;
  total_tests: number;
  completed_tests: number;
  failed_tests: number;
  behaviors_completed: number;
  behaviors_in_progress: number;
  behaviors_pending: number;
  average_score: number | null;
  judgment_stats: JudgmentStats | null;
}

export interface BehaviorSummary {
  name: string;
  path: string;
  definition: string;
  status: 'completed' | 'in_progress' | 'pending' | 'partial';
  completed_turns: number[];
  total_turns: number;
  has_results: boolean;
}

export interface ConversationSummary {
  id: string;
  behavior: string;
  turn_count: number;
  timestamp: string;
  score: number | null;
  stage: string;
  preview: string | null;
}

export interface ConversationMessage {
  role: string;
  content: string;
  timestamp?: string;
}

export interface ConversationDetail {
  id: string;
  behavior: string;
  turn_count: number;
  understanding: any;
  ideation: any;
  rollout: any;
  judgment: any;
  transcript: ConversationMessage[];
}

// Control types
export interface BehaviorOption {
  slug: string;
  name: string;
  path: string;
}

export interface StartRunRequest {
  mode: 'full' | 'selected';
  scenarios_per_behavior: number;
  selected_behaviors: string[];
  turn_counts: number[];
}

export interface ControlResponse {
  success: boolean;
  message: string;
  run_id?: string;
}

export interface ControlStatus {
  is_running: boolean;
  control_status: string;
  command: string | null;
  run_id: string | null;
}

// API functions
export const getStatus = () => api.get<RunStatus>('/api/status');
export const getStats = () => api.get<Stats>('/api/status/stats');
export const getBehaviors = (params?: { status?: string; limit?: number; offset?: number }) => 
  api.get<BehaviorSummary[]>('/api/behaviors', { params });
export const getBehavior = (name: string) => api.get<any>(`/api/behaviors/${name}`);
export const getConversations = (params?: { behavior?: string; limit?: number; offset?: number }) =>
  api.get<ConversationSummary[]>('/api/conversations', { params });
export const getConversation = (id: string) => api.get<ConversationDetail>(`/api/conversations/${id}`);

// Control API functions
export const getControlStatus = () => api.get<ControlStatus>('/api/control/status');
export const getBehaviorOptions = () => api.get<BehaviorOption[]>('/api/control/behaviors');
export const startRun = (request: StartRunRequest) => api.post<ControlResponse>('/api/control/start', request);
export const pauseRun = () => api.post<ControlResponse>('/api/control/pause');
export const resumeRun = () => api.post<ControlResponse>('/api/control/resume');
export const stopRun = () => api.post<ControlResponse>('/api/control/stop');
export const restartRun = (request: StartRunRequest) => api.post<ControlResponse>('/api/control/restart', request);

// History types
export interface RunSummary {
  run_id: string;
  directory: string;
  timestamp: string;
  time_only: string;
  date: string;
  modified_at: string;
  total_behaviors: number;
  completed_tests: number;
  failed_tests: number;
  conversation_count: number;
  config: Record<string, any>;
}

export interface DateGroup {
  date: string;
  date_display: string;
  runs: RunSummary[];
  total_completed: number;
  total_failed: number;
  total_conversations: number;
}

export interface HistoryConversation {
  id: string;
  run_id: string;
  behavior: string;
  turn_count: number;
  timestamp: string;
  score: number | null;
  stage: string;
  preview: string | null;
  path: string;
}

// History API functions
export const getRunHistory = () => api.get<DateGroup[]>('/api/history/runs');
export const getRunConversations = (runId: string, params?: { limit?: number; offset?: number }) =>
  api.get<HistoryConversation[]>(`/api/history/runs/${runId}/conversations`, { params });
export const getHistoryConversation = (conversationId: string) =>
  api.get<ConversationDetail>(`/api/history/conversations/${conversationId}`);

