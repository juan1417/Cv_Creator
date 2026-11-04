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
  JobMatchResult,
  CVAdaptationResult,
  ExportRequest,
  ATSReportResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string | null;

  constructor(status: number, body: string) {
    super(`API error ${status}: ${body}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = extractDetail(body);
  }
}

/** Extrae el `detail` que FastAPI devuelve en el cuerpo del error. */
function extractDetail(body: string): string | null {
  try {
    const parsed: unknown = JSON.parse(body);
    if (
      typeof parsed === "object" &&
      parsed !== null &&
      typeof (parsed as { detail?: unknown }).detail === "string"
    ) {
      return (parsed as { detail: string }).detail;
    }
  } catch {
    // Cuerpo no JSON (HTML de un proxy, etc.): se queda sin detail.
  }
  return null;
}

/** Un 404 significa que el recurso ya no existe. */
export function isNotFoundError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

/** Mensaje apto para el usuario: el `detail` de FastAPI o uno genérico. */
export function apiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError && error.detail) return error.detail;
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

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
      throw new ApiError(res.status, body);
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

export async function analyzeCV(
  userId: string,
  jobDescription?: string,
): Promise<CVAnalysis> {
  const trimmed = jobDescription?.trim();
  const body = trimmed ? JSON.stringify({ job_description: trimmed }) : undefined;
  return request(
    `/api/chat/cv-analysis?user_id=${userId}`,
    body !== undefined
      ? { method: "POST", body, headers: { "Content-Type": "application/json" } }
      : { method: "POST" },
    120_000,
  );
}

// ─── CV Export & ATS Report ──────────────────────────────────────────────────

function _downloadFilename(disposition: string | null, fallback: string): string {
  if (!disposition) return fallback;
  const match = /filename="?([^";]+)"?/.exec(disposition);
  return match?.[1] ?? fallback;
}

export async function exportCV(
  req: ExportRequest,
  timeoutMs = 120_000,
): Promise<void> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_BASE}/api/cv/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal: controller.signal,
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`API error ${res.status}: ${body}`);
    }
    const blob = await res.blob();
    const filename = _downloadFilename(
      res.headers.get("Content-Disposition"),
      `CV.${req.format}`,
    );
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  } finally {
    clearTimeout(timeout);
  }
}

export async function atsReport(
  userId: string,
  jobDescription?: string,
): Promise<ATSReportResponse> {
  return request(
    "/api/cv/ats-report",
    {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        job_description: jobDescription ?? null,
      }),
    },
    120_000,
  );
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

// ─── Job Comparison & Adaptation ─────────────────────────────────────────────

export async function compareCVJob(
  userId: string,
  jobDescription: string,
): Promise<JobMatchResult> {
  return request(
    "/api/cv/compare-job",
    {
      method: "POST",
      body: jsonBody({ user_id: userId, job_description: jobDescription }),
    },
    120_000,
  );
}

export async function adaptCVForJob(
  userId: string,
  jobDescription: string,
  missingSkills: Array<{ name: string; importance: string }>,
): Promise<CVAdaptationResult> {
  return request(
    "/api/cv/adapt-job",
    {
      method: "POST",
      body: jsonBody({
        user_id: userId,
        job_description: jobDescription,
        missing_skills: missingSkills,
      }),
    },
    120_000,
  );
}
