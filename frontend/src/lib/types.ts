export interface Source {
  title: string;
  url: string;
}

export interface ResearchReport {
  company_overview: string;
  products_and_services: string[];
  target_customers: string[];
  business_signals: string[];
  risks_and_challenges: string[];
  discovery_questions: string[];
  outreach_strategy: string[];
  unknowns: string[];
  sources: Source[];
}

export type SessionStatus = "created" | "running" | "completed" | "failed";

export interface SessionRead {
  id: string;
  company_name: string;
  website: string | null;
  objective: string;
  status: SessionStatus;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface SessionDetail extends SessionRead {
  report: ResearchReport | null;
}

export interface WorkflowEvent {
  id: number;
  node: string;
  status: string;
  message: string | null;
  data: Record<string, unknown> | null;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatResponse {
  answer: string;
  history: ChatMessage[];
}
