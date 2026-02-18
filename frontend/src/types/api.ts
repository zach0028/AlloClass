export interface CategoryResponse {
  id: string;
  name: string;
  description: string;
  position: number;
}

export interface AxisResponse {
  id: string;
  name: string;
  description: string;
  position: number;
  categories: CategoryResponse[];
}

export interface ConfigResponse {
  id: string;
  name: string;
  description: string;
  template_source: string | null;
  created_at: string;
  updated_at: string;
  axes: AxisResponse[];
}

export interface AxisResultDetail {
  axis_id: string;
  axis_name: string;
  category_id: string;
  category_name: string;
  confidence: number;
  vote_count?: number;
  all_votes?: string[];
}

export interface ChallengerDetail {
  axis_id: string | null;
  axis_name: string;
  alternative_category: string;
  argument: string;
  agrees_with_original?: boolean;
  original_confidence: number;
}

export interface ClassificationResponse {
  id: string;
  config_id: string;
  input_text: string;
  results: AxisResultDetail[];
  overall_confidence: number;
  was_challenged: boolean;
  challenger_response: ChallengerDetail[] | null;
  model_used: string;
  tokens_used: number;
  processing_time_ms: number;
  created_at: string;
}

export interface ClassificationListResponse {
  items: ClassificationResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface KPIResponse {
  total_classifications: number;
  average_confidence: number;
  challenge_rate: number;
  feedback_count: number;
}

export interface ConfidenceBucket {
  range_start: number;
  range_end: number;
  count: number;
}

export interface MatrixAxis {
  name: string;
  categories: string[];
}

export interface MatrixCell {
  x_category: string;
  y_category: string;
  count: number;
  avg_confidence: number;
}

export interface ClassificationMatrixResponse {
  axes: MatrixAxis[];
  x_axis: string;
  y_axis: string;
  cells: MatrixCell[];
  total: number;
}

export interface ScenarioResponse {
  id: string;
  name: string;
  description: string;
  icon: string;
  strategy: string;
  difficulty_bias: string;
}

export interface DripFeedStatusResponse {
  is_running: boolean;
  generated_count: number;
  total_count: number;
  interval_seconds: number;
  scenario_id: string | null;
}

export interface GeneratedTicketResponse {
  id: string;
  input_text: string;
  overall_confidence: number;
  was_challenged: boolean;
  created_at?: string;
}

export interface ChatMessageResponse {
  id: string;
  config_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  intent: string | null;
  created_at: string;
}

export interface ConversationResponse {
  id: string;
  config_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message: string | null;
}
