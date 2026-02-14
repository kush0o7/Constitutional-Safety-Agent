export type ChatMessage = {
  role: 'user' | 'assistant' | 'system';
  content: string;
};

export type RuleViolation = {
  rule: string;
  violated: boolean;
  reason: string;
};

export type RuleLogEntry = {
  rule: string;
  status: 'applied' | 'violated' | 'not_triggered';
  detail: string;
};

export type ChatResponse = {
  draft: string;
  violations: RuleViolation[];
  final_answer: string;
  confidence: number;
  rule_applied_log: RuleLogEntry[];
};

export type HistoryItem = {
  id: string;
  prompt: string;
  response: ChatResponse;
  createdAt: string;
};

export type EvalSummary = {
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  failed_ids: string[];
  violations_by_rule: Record<string, number>;
};

export type EvalResult = {
  id: string;
  expected_outcome: string;
  actual_outcome: string;
  expected_violated_rules: string[];
  actual_violated_rules: string[];
  passed: boolean;
  confidence: number;
  final_answer: string;
};

export type LatestEvalReportResponse = {
  generated_at: string;
  summary: EvalSummary;
  results: EvalResult[];
  source_file: string;
};
