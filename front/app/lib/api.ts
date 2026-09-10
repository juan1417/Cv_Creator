import type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
  CVResponse,
  CreateCVRequest,
  UpdateCVRequest,
  FullCV,
  ExperienceResponse,
  ExperienceListResponse,
  AddExperienceRequest,
  UpdateExperienceRequest,
  SkillResponse,
  SkillListResponse,
  AddSkillRequest,
  EducationResponse,
  EducationListResponse,
  AddEducationRequest,
  ChatSession,
  ChatSessionListResponse,
  ChatMessageListResponse,
  CreateSessionRequest,
  SendMessageRequest,
  SendMessageResponse,
  CVFieldUpdateRequest,
  CVEditResponse,
  CVAnalysis,
  LogListResponse,
  LogStatsResponse,
  LogFilesResponse,
  AchievementResponse,
  AddAchievementRequest,
  ProgramResponse,
  AddProgramRequest,
  LanguageResponse,
  AddLanguageRequest,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  init?: RequestInit,
  timeoutMs = 60_000,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...init?.headers },
      signal: controller.signal,
      ...init,
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`API error ${res.status}: ${body}`);
    }
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timeout);
  }
}

function jsonBody<T>(data: T): string {
  return JSON.stringify(data);
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export async function validateSession(
  email: string,
  password: string,
): Promise<{ message: string }> {
  const params = new URLSearchParams({ email, password });
  return request(`/validate_session?${params}`);
}

export async function getUserByEmail(
  email: string,
): Promise<User> {
  const params = new URLSearchParams({ email });
  return request(`/get_user_by_email?${params}`);
}

// ─── Users ───────────────────────────────────────────────────────────────────

export async function createUser(data: CreateUserRequest): Promise<User> {
  return request("/api/users", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function getUser(userId: string): Promise<User> {
  return request(`/api/users/${userId}`);
}

export async function getUserById(email: string): Promise<User> {
  return request(`/api/users/by-email/${email}`);
}

export async function updateUser(
  userId: string,
  data: UpdateUserRequest,
): Promise<User> {
  return request(`/api/users/${userId}`, {
    method: "PUT",
    body: jsonBody(data),
  });
}

export async function deleteUser(
  userId: string,
): Promise<{ message: string }> {
  return request(`/api/users/${userId}`, { method: "DELETE" });
}

// ─── CV ──────────────────────────────────────────────────────────────────────

export async function createCV(data: CreateCVRequest): Promise<CVResponse> {
  return request("/api/cv", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function getFullCV(userId: string): Promise<FullCV> {
  return request(`/api/cv/${userId}`);
}

export async function updateCV(
  userId: string,
  data: UpdateCVRequest,
): Promise<CVResponse> {
  return request(`/api/cv/${userId}`, {
    method: "PUT",
    body: jsonBody(data),
  });
}

export async function deleteCV(
  userId: string,
): Promise<{ message: string }> {
  return request(`/api/cv/${userId}`, { method: "DELETE" });
}

// ─── Experiences ─────────────────────────────────────────────────────────────

export async function getExperiences(
  userId: string,
): Promise<ExperienceListResponse> {
  return request(`/api/experiences/${userId}`);
}

export async function getExperience(
  experienceId: string,
): Promise<ExperienceResponse> {
  return request(`/api/experiences/detail/${experienceId}`);
}

// ─── Skills ──────────────────────────────────────────────────────────────────

export async function getSkills(
  userId: string,
): Promise<SkillListResponse> {
  return request(`/api/skills/${userId}`);
}

export async function getSkill(skillId: string): Promise<SkillResponse> {
  return request(`/api/skills/detail/${skillId}`);
}

// ─── Education ───────────────────────────────────────────────────────────────

export async function getEducation(
  userId: string,
): Promise<EducationListResponse> {
  return request(`/api/education/${userId}`);
}

export async function getEducationDetail(
  educationId: string,
): Promise<EducationResponse> {
  return request(`/api/education/detail/${educationId}`);
}

// ─── Chat ────────────────────────────────────────────────────────────────────

export async function createChatSession(
  data: CreateSessionRequest,
): Promise<ChatSession> {
  return request("/api/chat/sessions", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function sendMessage(
  sessionId: string,
  data: SendMessageRequest,
): Promise<SendMessageResponse> {
  return request(`/api/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function listSessions(
  userId: string,
): Promise<ChatSessionListResponse> {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/api/chat/sessions?${params}`);
}

export async function getSessionMessages(
  sessionId: string,
  userId: string,
): Promise<ChatMessageListResponse> {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/api/chat/sessions/${sessionId}/messages?${params}`);
}

export async function deleteSession(
  sessionId: string,
  userId: string,
): Promise<{ message: string }> {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/api/chat/sessions/${sessionId}?${params}`, {
    method: "DELETE",
  });
}

// ─── CV Analysis ─────────────────────────────────────────────────────────────

export async function analyzeCV(userId: string): Promise<CVAnalysis> {
  const params = new URLSearchParams({ user_id: userId });
  // El análisis llama a la IA: le damos más margen que al resto (120s)
  return request(`/api/chat/cv-analysis?${params}`, undefined, 120_000);
}

// ─── CV Edit (Chat) ─────────────────────────────────────────────────────────

export async function updateCVField(
  data: CVFieldUpdateRequest,
): Promise<CVEditResponse> {
  return request("/api/chat/cv/field", {
    method: "PUT",
    body: jsonBody(data),
  });
}

export async function addExperience(
  data: AddExperienceRequest,
): Promise<CVEditResponse> {
  return request("/api/chat/cv/experience", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function updateExperience(
  experienceId: string,
  data: UpdateExperienceRequest,
): Promise<CVEditResponse> {
  return request(`/api/chat/cv/experience/${experienceId}`, {
    method: "PUT",
    body: jsonBody(data),
  });
}

export async function deleteExperience(
  experienceId: string,
  userId: string,
): Promise<CVEditResponse> {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/api/chat/cv/experience/${experienceId}?${params}`, {
    method: "DELETE",
  });
}

export async function addSkill(
  data: AddSkillRequest,
): Promise<CVEditResponse> {
  return request("/api/chat/cv/skill", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function deleteSkill(
  skillId: string,
  userId: string,
): Promise<CVEditResponse> {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/api/chat/cv/skill/${skillId}?${params}`, {
    method: "DELETE",
  });
}

export async function addEducation(
  data: AddEducationRequest,
): Promise<CVEditResponse> {
  return request("/api/chat/cv/education", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function deleteEducation(
  educationId: string,
  userId: string,
): Promise<CVEditResponse> {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/api/chat/cv/education/${educationId}?${params}`, {
    method: "DELETE",
  });
}

// ─── Logs ────────────────────────────────────────────────────────────────────

export async function getLogs(params?: {
  level?: string;
  module?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
}): Promise<LogListResponse> {
  const search = new URLSearchParams();
  if (params?.level) search.set("level", params.level);
  if (params?.module) search.set("module", params.module);
  if (params?.start_date) search.set("start_date", params.start_date);
  if (params?.end_date) search.set("end_date", params.end_date);
  if (params?.limit != null) search.set("limit", String(params.limit));
  const qs = search.toString();
  return request(`/api/logs${qs ? `?${qs}` : ""}`);
}

export async function getLogStats(): Promise<LogStatsResponse> {
  return request("/api/logs/stats");
}

export async function getLogFiles(): Promise<LogFilesResponse> {
  return request("/api/logs/files");
}

export async function getLogFile(filename: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/logs/files/${filename}`);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.text();
}

export async function getUserLogs(
  userId: string,
  limit?: number,
): Promise<LogListResponse> {
  const params = new URLSearchParams();
  if (limit != null) params.set("limit", String(limit));
  const qs = params.toString();
  return request(`/api/logs/${userId}${qs ? `?${qs}` : ""}`);
}

// ─── Skill Catalog ─────────────────────────────────────────────────────

export interface SkillCatalogItem {
  id: string;
  name: string;
  category: string;
  is_custom: boolean;
}

export async function searchSkillCatalog(
  query: string,
): Promise<{ results: SkillCatalogItem[] }> {
  const params = new URLSearchParams({ q: query });
  return request(`/api/skills-catalog/search?${params}`);
}

export async function getSkillCatalogByCategory(): Promise<{
  categories: Record<string, SkillCatalogItem[]>;
}> {
  return request("/api/skills-catalog/by-category");
}

export async function addCustomSkillCatalog(
  name: string,
  category?: string,
): Promise<{ skill: SkillCatalogItem }> {
  const params = new URLSearchParams({ name });
  if (category) params.set("category", category);
  return request(`/api/skills-catalog/custom?${params}`, {
    method: "POST",
  });
}

// ─── Achievements ────────────────────────────────────────────────────────────

export async function addAchievement(
  data: AddAchievementRequest,
): Promise<AchievementResponse> {
  return request("/api/achievements", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function deleteAchievement(
  achievementId: string,
  userId: string,
): Promise<{ message: string }> {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/api/achievements/${achievementId}?${params}`, {
    method: "DELETE",
  });
}

// ─── Programs ────────────────────────────────────────────────────────────────

export async function addProgram(
  data: AddProgramRequest,
): Promise<ProgramResponse> {
  return request("/api/programs", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function deleteProgram(
  programId: string,
  userId: string,
): Promise<{ message: string }> {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/api/programs/${programId}?${params}`, {
    method: "DELETE",
  });
}

// ─── Languages ───────────────────────────────────────────────────────────────

export async function addLanguage(
  data: AddLanguageRequest,
): Promise<LanguageResponse> {
  return request("/api/languages", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function deleteLanguage(
  languageId: string,
  userId: string,
): Promise<{ message: string }> {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/api/languages/${languageId}?${params}`, {
    method: "DELETE",
  });
}
