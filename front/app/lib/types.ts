// ─── User ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  password?: string;
}

// ─── CV ──────────────────────────────────────────────────────────────────────

export interface CVResponse {
  id: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  about: string;
  porfolio: string;
  linkedin: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateCVRequest {
  user_id: string;
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  about?: string;
  porfolio?: string;
  linkedin?: string;
}

export interface UpdateCVRequest {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  about?: string;
  porfolio?: string;
  linkedin?: string;
}

export interface FullCV {
  cv: CVResponse;
  experiences: ExperienceResponse[];
  skills: SkillResponse[];
  education: EducationResponse[];
  achievements: AchievementResponse[];
  programs: ProgramResponse[];
  languages: LanguageResponse[];
}

// ─── Experience ──────────────────────────────────────────────────────────────

export interface ExperienceResponse {
  id: string;
  title: string;
  company: string;
  start_date: string | null;
  end_date: string | null;
  description: string;
}

export interface ExperienceListResponse {
  experiences: ExperienceResponse[];
  total: number;
}

export interface AddExperienceRequest {
  user_id: string;
  title: string;
  company: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

export interface UpdateExperienceRequest {
  user_id: string;
  title?: string;
  company?: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

// ─── Skill ───────────────────────────────────────────────────────────────────

export interface SkillResponse {
  id: string;
  name: string;
  level: string;
  type: string;
}

export interface SkillListResponse {
  skills: SkillResponse[];
  total: number;
}

export interface AddSkillRequest {
  user_id: string;
  name: string;
  level?: string;
  type?: string;
}

// ─── Education ───────────────────────────────────────────────────────────────

export interface EducationResponse {
  id: string;
  degree: string;
  institution: string;
  start_date: string | null;
  end_date: string | null;
  description: string;
}

export interface EducationListResponse {
  education: EducationResponse[];
  total: number;
}

export interface AddEducationRequest {
  user_id: string;
  degree: string;
  institution: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

// ─── Chat ────────────────────────────────────────────────────────────────────

export interface ChatSession {
  session_id: string;
  title: string;
  target_job: string | null;
  created_at: string;
}

export interface ChatSessionListResponse {
  sessions: ChatSession[];
  total: number;
}

export interface ChatMessage {
  id: string;
  role: string;
  content: string;
  at_Created: string;
}

export interface ChatMessageListResponse {
  messages: ChatMessage[];
  total: number;
}

export interface CreateSessionRequest {
  user_id: string;
  target_job?: string;
}

export interface SendMessageRequest {
  user_id: string;
  content: string;
}

export interface SendMessageResponse {
  session_id: string;
  response: string;
  target_job: string | null;
  action_result?: Record<string, unknown>;
}

// ─── CV Edit (Chat) ─────────────────────────────────────────────────────────

export interface CVFieldUpdateRequest {
  user_id: string;
  field: string;
  value: string;
}

export interface CVEditResponse {
  success: boolean;
  message: string;
  new_id?: string;
}

// ─── CV Analysis ─────────────────────────────────────────────────────────────

export interface MetricDetail {
  name: string;
  score: number;
  max_score: number;
  status: string;
  message: string;
  suggestions: string[];
}

export interface MetricGroup {
  score: number;
  details: MetricDetail[];
}

export interface CVAnalysis {
  overall_score: number;
  completeness: MetricGroup;
  content: MetricGroup;
  ats_compatibility: MetricGroup;
  structure: MetricGroup;
  summary: string;
  top_improvements: string[];
}

// ─── Logs ────────────────────────────────────────────────────────────────────

export interface LogEntry {
  id: string;
  level: string;
  module: string;
  message: string;
  created_at: string;
}

export interface LogListResponse {
  logs: LogEntry[];
  total: number;
}

export interface LogStatsResponse {
  total: number;
  by_level: Record<string, number>;
  by_day: Record<string, number>;
}

export interface LogFilesResponse {
  files: string[];
}

// ─── Achievement ─────────────────────────────────────────────────────────────

export interface AchievementResponse {
  id: string;
  title: string;
  description: string;
}

export interface AddAchievementRequest {
  user_id: string;
  title: string;
  description?: string;
}

// ─── Program ─────────────────────────────────────────────────────────────────

export interface ProgramResponse {
  id: string;
  name: string;
}

export interface AddProgramRequest {
  user_id: string;
  name: string;
}

// ─── Language ────────────────────────────────────────────────────────────────

export interface LanguageResponse {
  id: string;
  name: string;
  level: string;
}

export interface AddLanguageRequest {
  user_id: string;
  name: string;
  level?: string;
}

// ─── Job Comparison & Adaptation ─────────────────────────────────────────────

export interface MatchingSkill {
  name: string;
  level: string;
  relevance: string;
}

export interface MissingSkill {
  name: string;
  importance: string;
  suggestion: string;
}

export interface JobMatchResult {
  match_score: number;
  matching_skills: MatchingSkill[];
  missing_skills: MissingSkill[];
  strengths: string[];
  weaknesses: string[];
  summary: string;
}

export interface AdaptedExperience {
  company: string;
  title: string;
  description: string;
}

export interface AdaptedSkill {
  name: string;
  level: string;
}

export interface CVAdaptationResult {
  adapted_about: string;
  adapted_experiences: AdaptedExperience[];
  adapted_skills: AdaptedSkill[];
  key_changes: string[];
  tips: string[];
}
