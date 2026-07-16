import axios from 'axios';

const api = axios.create({
  baseURL: 'https://leadflowai-6fex.onrender.com/api',
  headers: { 'Content-Type': 'application/json' },
});

export interface LeadCreate {
  name: string;
  email: string;
  job_title?: string;
  company_name?: string;
  company_website?: string;
  company_size?: string;
  industry?: string;
  message?: string;
}

export interface LeadResponse {
  id: string;
  created_at: string;
  name: string;
  email: string;
  job_title: string | null;
  company_name: string | null;
  company_website: string | null;
  company_size: string | null;
  industry: string | null;
  message: string | null;
  score: number | null;
  score_reason: string | null;
  classification: string | null;
  classification_reason: string | null;
  status: string;
  approval_status: string;
  draft_email_subject: string | null;
  draft_email_body: string | null;
  routing_action: string | null;
  routing_reason: string | null;
}

export interface LeadDetailResponse extends LeadResponse {
  enriched_industry: string | null;
  enriched_company_size: string | null;
  estimated_revenue: string | null;
  enriched_website: string | null;
  buying_signals: any;
  decision_maker_status: boolean | null;
  market_segment: string | null;
  industry_score: number | null;
  company_size_score: number | null;
  role_score: number | null;
  buying_intent_score: number | null;
  error_message: string | null;
  sent_email_subject: string | null;
  sent_email_body: string | null;
  sent_at: string | null;
  edited_email_subject: string | null;
  edited_email_body: string | null;
  approval_comment: string | null;

  // Fix for Vercel build
  email_status: string | null;
}

export interface ProcessResponse {
  lead_id: string;
  status: string;
  classification: string | null;
  score: number | null;
  score_reason: string | null;
  classification_reason: string | null;
  routing_action: string | null;
  draft_email_subject: string | null;
  draft_email_body: string | null;
  email_status: string | null;
  message: string;
}

export interface DashboardStats {
  total_leads: number;
  hot_leads: number;
  nurture_leads: number;
  disqualified_leads: number;
  average_score: number;
  approval_rate: number;
  email_draft_count: number;
  pending_approval_count: number;
  approved_count: number;
  sent_count: number;
}

export interface ApprovalRequest {
  action: 'approve' | 'reject' | 'edit';
  comment?: string;
  edited_email_subject?: string;
  edited_email_body?: string;
}

export interface GovernanceStats {
  total_audit_events: number;
  approval_requests: number;
  approved_emails: number;
  rejected_emails: number;
  sent_emails: number;
  governance_violations: number;
  injection_attempts_blocked: number;
  fairness_tests_passed: number;
  fairness_tests_failed: number;
  total_fairness_tests: number;
  total_injection_tests: number;
}

export interface EvaluationResult {
  test_name: string;
  status: string;
  details: string;
  score: number | null;
  classification: string | null;
  expected: string;
  actual: string;
}

// Lead API
export const leadApi = {
  create: (data: LeadCreate) => api.post<LeadResponse>('/leads/', data),
  process: (data: LeadCreate) => api.post<ProcessResponse>('/leads/process', data),
  list: (params?: { skip?: number; limit?: number; status?: string; classification?: string }) =>
    api.get<LeadResponse[]>('/leads/', { params }),
  get: (id: string) => api.get<LeadDetailResponse>(`/leads/${id}`),
  approve: (id: string, data: ApprovalRequest) => api.post(`/leads/${id}/approve`, data),
  send: (id: string) => api.post(`/leads/${id}/send`),
  getLogs: (id: string) => api.get(`/leads/${id}/logs`),
};

// Dashboard API
export const dashboardApi = {
  stats: () => api.get<DashboardStats>('/leads/dashboard/stats'),
};

// Test API
export const testApi = {
  runFairness: () => api.post('/leads/test/fairness'),
  getFairness: () => api.get('/leads/test/fairness'),
  runInjection: () => api.post('/leads/test/injection'),
  getInjection: () => api.get('/leads/test/injection'),
};

// Governance & Evaluation API
export const governanceApi = {
  stats: () => api.get<GovernanceStats>('/leads/dashboard/governance'),
};

export const evaluationApi = {
  results: () => api.get<EvaluationResult[]>('/leads/evaluation'),
};

// Audit API
export const auditApi = {
  list: (params?: { skip?: number; limit?: number; event_type?: string }) =>
    api.get('/leads/audit/logs', { params }),
};

export default api;