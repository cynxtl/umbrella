export interface LocationItem {
  name: string;
  region?: string;
  country: string;
  country_code?: string;
  lat?: number;
  lon?: number;
  timezone_offset?: number;
  display_name: string;
}

export interface PlanContext {
  location?: string | null;
  location_details?: LocationItem | null;
  activity_type: string;
  start_time: string;
  end_time: string;
  flexibility_hours: number;
  preference: string;
  caution_adjustment: number;
}

export interface ForecastSlot {
  time: string;
  hour_24?: number;
  rain_probability: number;
  temperature: number;
  description: string;
  wind_speed?: number;
  humidity?: number;
}

export interface PlanDetail {
  start_time: string;
  end_time: string;
  label: string;
  peak_pop: number;
  mean_pop: number;
  risk_level: string;
  conditions: string;
  temp_range?: string;
}

export interface PlanComparisonData {
  has_better_alternative: boolean;
  original_plan: PlanDetail;
  recommended_plan: PlanDetail;
  risk_reduction_pp: number;
  why_this_plan: string;
  candidates_evaluated: number;
  candidates?: Array<Record<string, any>>;
}

export interface ExecutionStep {
  step: number;
  title: string;
  tool_or_node: string;
  status: string;
  duration_ms: number;
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
}

export interface AssistantData {
  session_id: string;
  message: string;
  intent: string;
  plan_context: PlanContext;
  recommendation: string;
  personalized_recommendation: string;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH';
  rain_probability: number;
  temperature: number;
  conditions: string;
  peak_rain_time: string;
  wind_speed: number;
  forecast_timeline: ForecastSlot[];
  plan_comparison?: PlanComparisonData;
  execution_trace?: ExecutionStep[];
  roles?: Record<string, any>;
  llm_available?: boolean;
  demo_mode?: boolean;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  data?: AssistantData;
}
