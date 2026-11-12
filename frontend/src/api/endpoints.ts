import { api, refreshCsrf } from './client';
import type {
  Appointment,
  AuditEntry,
  ChatMessage,
  ChatResponse,
  ConsentGrant,
  Conversation,
  DigitalTwin,
  DocumentRecord,
  DoctorPatient,
  FeatureFlag,
  HealthRecord,
  KnowledgeSource,
  NotificationItem,
  Recommendation,
  Safety,
  SystemHealth,
  TimelineEvent,
  User,
} from './types';

export interface ListResult<T> {
  results: T[];
}

const list = <T>(path: string) => api.get<ListResult<T>>(path);

// --- auth -------------------------------------------------------------------
export const auth = {
  csrf: () => refreshCsrf(),
  login: (email: string, password: string) =>
    api.post<User>('/auth/login/', { email, password }).then(async (user) => {
      await refreshCsrf(); // the backend rotates the token on login
      return user;
    }),
  register: (payload: Record<string, unknown>) => api.post<User>('/auth/register/', payload),
  logout: () => api.post<{ ok: boolean }>('/auth/logout/'),
  me: () => api.get<User>('/me/'),
  updateMe: (payload: Record<string, unknown>) => api.patch<User>('/me/', payload),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<{ ok: boolean }>('/auth/password/change/', { currentPassword, newPassword }),
  forgotPassword: (email: string) =>
    api.post<{ ok: boolean; devToken?: string }>('/auth/password/forgot/', { email }),
  resetPassword: (token: string, password: string) =>
    api.post<{ ok: boolean }>('/auth/password/reset/', { token, password }),
  doctors: () => list<{ id: string; name: string; specialization: string; hospital: string }>('/doctors/'),
};

// --- patient / digital twin --------------------------------------------------
export const patient = {
  digitalTwin: () => api.get<DigitalTwin>('/patient/digital-twin/'),
  records: (params: { category?: string; q?: string } = {}) => {
    const query = new URLSearchParams();
    if (params.category) query.set('category', params.category);
    if (params.q) query.set('q', params.q);
    const suffix = query.toString() ? `?${query}` : '';
    return list<HealthRecord>(`/patient/records/${suffix}`);
  },
  createRecord: (payload: Record<string, unknown>) => api.post<HealthRecord>('/patient/records/', payload),
  updateRecord: (id: string, payload: Record<string, unknown>) =>
    api.patch<HealthRecord>(`/patient/records/${id}/`, payload),
  deleteRecord: (id: string) => api.del<void>(`/patient/records/${id}/`),
  timeline: (type?: string) => list<TimelineEvent>(`/patient/timeline/${type ? `?type=${type}` : ''}`),
  observations: () => list<import('./types').Observation>('/patient/observations/'),
  allergies: () => list<import('./types').Allergy>('/patient/allergies/'),
  createAllergy: (payload: Record<string, unknown>) =>
    api.post<import('./types').Allergy>('/patient/allergies/', payload),
  updateAllergy: (id: string, payload: Record<string, unknown>) =>
    api.patch<import('./types').Allergy>(`/patient/allergies/${id}/`, payload),
  deleteAllergy: (id: string) => api.del<void>(`/patient/allergies/${id}/`),
  medications: () => list<import('./types').Medication>('/patient/medications/'),
  createMedication: (payload: Record<string, unknown>) =>
    api.post<import('./types').Medication>('/patient/medications/', payload),
  updateMedication: (id: string, payload: Record<string, unknown>) =>
    api.patch<import('./types').Medication>(`/patient/medications/${id}/`, payload),
  deleteMedication: (id: string) => api.del<void>(`/patient/medications/${id}/`),
  documents: () => list<DocumentRecord>('/patient/documents/'),
  uploadDocument: (file: File, category: string) => {
    const form = new FormData();
    form.append('file', file);
    form.append('category', category);
    return api.upload<DocumentRecord>('/patient/documents/', form);
  },
  document: (id: string) => api.get<DocumentRecord>(`/patient/documents/${id}/`),
  deleteDocument: (id: string) => api.del<void>(`/patient/documents/${id}/`),
  reviewExtraction: (documentId: string, extractionId: string, status: string, value?: string) =>
    api.post(`/patient/documents/${documentId}/extractions/${extractionId}/review/`, { status, value }),
  exportData: () => api.get<Record<string, unknown>>('/patient/export/'),
  deleteData: () => api.del<{ ok: boolean }>('/patient/data/'),
};

// --- consent -----------------------------------------------------------------
export const consent = {
  list: () => api.get<ListResult<ConsentGrant> & { scopeOptions: string[] }>('/consent/grants/'),
  grant: (payload: { doctorId: string; scope: string[]; purpose?: string; durationDays?: number }) =>
    api.post<ConsentGrant>('/consent/grants/new/', payload),
  request: (payload: { patientId: string; scope: string[]; purpose?: string; durationDays?: number }) =>
    api.post<ConsentGrant>('/consent/requests/', payload),
  decide: (id: string, decision: 'GRANT' | 'REJECT', payload: Record<string, unknown> = {}) =>
    api.post<ConsentGrant>(`/consent/grants/${id}/decision/`, { decision, ...payload }),
  revoke: (id: string) => api.post<ConsentGrant>(`/consent/grants/${id}/revoke/`),
};

// --- AI ----------------------------------------------------------------------
export const ai = {
  chat: (message: string, conversationId?: string) =>
    api.post<ChatResponse>('/ai/chat/', { message, conversationId }),
  publicChat: (message: string, language?: string) =>
    api.post<{
      answer: string;
      intent: string;
      sources: { ref: number; title: string; sourceTitle: string; url: string }[];
      limitations: string[];
      nextStep: string;
      safety: Safety;
      model: { name: string; version: string; mode: string; generationMode: string; latencyMs: number };
    }>('/ai/public-chat/', { message, language }),
  conversations: () =>
    api.get<{ results: { id: string; title: string; updatedAt: string | null; messageCount: number }[] }>(
      '/ai/conversations/',
    ),
  conversation: (id: string) =>
    api.get<{ id: string; title: string | null; messages: ChatMessage[] }>(`/ai/conversations/${id}/`),
  deleteConversation: (id: string) => api.del<void>(`/ai/conversations/${id}/`),
  history: () => api.get<ListResult<Record<string, unknown>>>('/ai/history/'),
  recommendations: () => list<Recommendation>('/recommendations/'),
  recommendationFeedback: (id: string, status: 'ACCEPTED' | 'DISMISSED') =>
    api.post(`/recommendations/${id}/feedback/`, { status }),
  evaluateSafety: (answer: string) => api.post<Safety>('/safety/evaluate/', { answer }),
  analyseContent: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.upload<Record<string, unknown>>('/content-analysis/', form);
  },
};

// --- messaging, appointments, notifications ----------------------------------
export const connect = {
  conversations: () => list<Conversation>('/conversations/'),
  startConversation: (doctorId: string) => api.post<Conversation>('/conversations/', { doctorId }),
  messages: (id: string) =>
    api.get<{ id: string; title: string | null; messages: ChatMessage[] }>(`/conversations/${id}/`),
  sendMessage: (id: string, body: string) => api.post<ChatMessage>(`/conversations/${id}/`, { body }),
  appointments: () => list<Appointment>('/appointments/'),
  createAppointment: (payload: { doctorId: string; scheduledAt: string; reason?: string; durationMin?: number }) =>
    api.post<Appointment>('/appointments/', payload),
  updateAppointment: (id: string, payload: { status?: string; notes?: string; scheduledAt?: string }) =>
    api.patch<Appointment>(`/appointments/${id}/`, payload),
  notifications: () => api.get<{ unread: number; results: NotificationItem[] }>('/notifications/'),
  markRead: (id: string) => api.post(`/notifications/${id}/read/`),
  markAllRead: () => api.post('/notifications/read-all/'),
};

// --- doctor ------------------------------------------------------------------
export const doctor = {
  patients: () => list<DoctorPatient>('/doctor/authorized-patients/'),
  summary: (patientId: string) =>
    api.get<{
      patient: { id: string; name: string; email: string; initials: string };
      scope: string[];
      profile: Record<string, unknown>;
      records: HealthRecord[];
      observations: import('./types').Observation[];
      allergies: import('./types').Allergy[];
      medications: import('./types').Medication[];
      documents: DocumentRecord[];
      timeline: TimelineEvent[];
      draftSummary: HealthRecord | null;
    }>(`/doctor/patients/${patientId}/summary/`),
  createDraftSummary: (patientId: string) =>
    api.post<HealthRecord>(`/doctor/patients/${patientId}/summary/`, {}),
  records: (patientId: string) => list<HealthRecord>(`/doctor/patients/${patientId}/records/`),
  documents: (patientId: string) => list<DocumentRecord>(`/doctor/patients/${patientId}/documents/`),
  timeline: (patientId: string) => list<TimelineEvent>(`/doctor/patients/${patientId}/timeline/`),
  documentFile: (documentId: string) => `/patient/documents/${documentId}/file/`,
};

// --- admin -------------------------------------------------------------------
export const admin = {
  users: (params: { role?: string; q?: string } = {}) => {
    const query = new URLSearchParams();
    if (params.role) query.set('role', params.role);
    if (params.q) query.set('q', params.q);
    const suffix = query.toString() ? `?${query}` : '';
    return list<User>(`/admin/users/${suffix}`);
  },
  updateUser: (id: string, payload: Record<string, unknown>) => api.patch<User>(`/admin/users/${id}/`, payload),
  auditLogs: (params: { action?: string; outcome?: string; actor?: string } = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => value && query.set(key, value));
    const suffix = query.toString() ? `?${query}` : '';
    return list<AuditEntry>(`/admin/audit-logs/${suffix}`);
  },
  consentGrants: () => list<ConsentGrant>('/admin/consent-grants/'),
  knowledgeSources: () => list<KnowledgeSource>('/admin/knowledge-sources/'),
  createKnowledgeSource: (payload: Record<string, unknown>) =>
    api.post<KnowledgeSource>('/admin/knowledge-sources/', payload),
  updateKnowledgeSource: (id: string, payload: Record<string, unknown>) =>
    api.patch<KnowledgeSource>(`/admin/knowledge-sources/${id}/`, payload),
  deleteKnowledgeSource: (id: string) => api.del<void>(`/admin/knowledge-sources/${id}/`),
  systemHealth: () => api.get<SystemHealth>('/admin/system/health/'),
  featureFlags: () => list<FeatureFlag>('/admin/feature-flags/'),
  updateFeatureFlag: (id: string, payload: { isEnabled?: boolean; status?: string }) =>
    api.patch<FeatureFlag>(`/admin/feature-flags/${id}/`, payload),
};

export const health = () => api.get<{ service: string; database: string; aiProvider: Record<string, string> }>('/health/');
