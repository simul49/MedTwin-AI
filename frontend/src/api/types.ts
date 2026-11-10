export type Role = 'PATIENT' | 'DOCTOR' | 'ADMIN';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  phone: string;
  avatarColor: string;
  initials: string;
  language: string;
  isActive: boolean;
  isVerified: boolean;
  createdAt: string | null;
  lastLoginAt: string | null;
  patientProfile?: {
    dateOfBirth: string | null;
    age?: number | null;
    gender: string;
    bloodType: string;
    heightCm: number | null;
    weightKg: number | null;
    city: string;
    emergencyContact: string;
    summary: string;
  };
  doctorProfile?: {
    specialization: string;
    licenseNumber: string;
    hospital: string;
    department: string;
    bio: string;
    verificationStatus: string;
  };
  grantedRoles?: string[];
}

export interface HealthRecord {
  id: string;
  category: string;
  title: string;
  summary: string;
  payload: Record<string, unknown> | null;
  sourceType: string;
  verificationStatus: string;
  sourceDocumentId: string | null;
  authorId: string | null;
  recordedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  isAiGenerated: boolean;
}

export interface Observation {
  id: string;
  code: string;
  label: string;
  value: number | null;
  valueText: string;
  displayValue: string;
  unit: string;
  referenceRange: string;
  flag: string;
  observedAt: string | null;
  sourceType: string;
}

export interface Allergy {
  id: string;
  substance: string;
  reaction: string;
  severity: string;
  status: string;
  sourceType: string;
  reviewedAt: string | null;
  createdAt: string | null;
}

export interface Medication {
  id: string;
  name: string;
  dose: string;
  frequency: string;
  route: string;
  status: string;
  startedAt: string | null;
  endedAt: string | null;
  sourceType: string;
}

export interface DocumentExtraction {
  id: string;
  fieldName: string;
  label: string;
  value: string;
  confidence: number | null;
  reviewStatus: string;
  evidence: string;
}

export interface DocumentRecord {
  id: string;
  name: string;
  mimeType: string;
  sizeBytes: number;
  category: string;
  processingStatus: string;
  processingError: string;
  pageCount: number | null;
  createdAt: string | null;
  processedAt: string | null;
  hasExtractedText: boolean;
  extractions?: DocumentExtraction[];
}

export interface TimelineEvent {
  id: string;
  eventType: string;
  title: string;
  description: string;
  occurredAt: string | null;
  sourceType: string;
  sourceId: string | null;
}

export interface DigitalTwin {
  patient: User;
  profile: User['patientProfile'];
  counts: {
    records: number;
    observations: number;
    allergies: number;
    medications: number;
    documents: number;
    timeline: number;
  };
  records: HealthRecord[];
  observations: Observation[];
  allergies: Allergy[];
  medications: Medication[];
  timeline: TimelineEvent[];
  freshness: { lastUpdated: string | null; unverifiedCount: number; missingSections: string[] };
  consents: ConsentGrant[];
}

export interface ConsentGrant {
  id: string;
  patientId: string;
  doctorId: string;
  doctor: { id: string; name: string; email: string; initials: string; avatarColor: string; specialization: string } | null;
  patient: { id: string; name: string; email: string; initials: string; avatarColor: string } | null;
  scope: string[];
  purpose: string;
  status: string;
  isEffective: boolean;
  grantedAt: string | null;
  expiresAt: string | null;
  revokedAt: string | null;
  createdAt: string | null;
}

export interface SafetyFactor {
  key: string;
  label: string;
  status: 'pass' | 'warn' | 'fail' | 'info';
  score: number;
  weight: number;
  detail: string;
}

export interface Safety {
  score: number;
  version: string;
  labels: string[];
  factors: SafetyFactor[];
  disclaimer: string;
}

export interface ChatSource {
  ref: number;
  chunkId: string;
  title: string;
  sourceTitle: string;
  publisher: string;
  url: string;
  score: number;
  excerpt: string;
}

export interface ChatResponse {
  interactionId: string;
  traceId: string;
  answer: string;
  intent: string;
  riskCategory: string;
  contextUsed: string[];
  sources: ChatSource[];
  limitations: string[];
  nextStep: string;
  needsClarification: boolean;
  clarification: string;
  safety: Safety;
  model: { name: string; version: string; mode: string; generationMode: string; latencyMs: number };
}

export interface ChatMessage {
  id: string;
  role: 'USER' | 'AI' | 'DOCTOR' | 'SYSTEM';
  body: string;
  senderId: string | null;
  senderName?: string;
  createdAt: string | null;
  readAt: string | null;
  metadata?: Record<string, unknown>;
}

export interface Conversation {
  id: string;
  title: string;
  channel: string;
  counterpart: {
    id: string;
    name: string;
    initials: string;
    avatarColor: string;
    specialization?: string;
  } | null;
  lastMessage: string;
  lastMessageAt: string | null;
  unread: number;
  updatedAt: string | null;
}

export interface Appointment {
  id: string;
  patientId: string;
  doctorId: string | null;
  patientName: string;
  doctorName: string;
  scheduledAt: string | null;
  durationMin: number;
  timezone: string;
  reason: string;
  status: string;
  notes: string;
  createdAt: string | null;
}

export interface NotificationItem {
  id: string;
  type: string;
  title: string;
  body: string;
  link: string;
  isRead: boolean;
  createdAt: string | null;
}

export interface Recommendation {
  id: string;
  type: string;
  title: string;
  body: string;
  basis: Record<string, unknown>;
  basisText?: string;
  status: string;
  createdAt: string | null;
}

export interface DoctorPatient {
  id: string;
  name: string;
  email: string;
  initials: string;
  avatarColor: string;
  age: number | null;
  gender: string;
  scope: string[];
  expiresAt: string | null;
  openFlags: number;
  recordCount: number;
  lastActivity: string | null;
}

export interface AuditEntry {
  id: string;
  actorId: string | null;
  actorEmail: string;
  action: string;
  resourceType: string;
  resourceId: string;
  outcome: string;
  ipAddress: string;
  traceId: string;
  metadata: Record<string, unknown>;
  createdAt: string | null;
}

export interface KnowledgeSource {
  id: string;
  title: string;
  publisher: string;
  version: string;
  sourceUrl: string;
  category: string;
  licenseStatus: string;
  reviewStatus: string;
  ingestedAt: string | null;
  chunkCount: number;
  createdAt: string | null;
}

export interface FeatureFlag {
  id: string;
  key: string;
  label: string;
  description: string;
  isEnabled: boolean;
  status: string;
  updatedAt: string | null;
}

export interface SystemHealth {
  database: string;
  aiProvider: { name: string; version: string; mode: string };
  counts: Record<string, number>;
  models: { id: string; name: string; version: string; provider: string; kind: string; isActive: boolean }[];
  generatedAt: string | null;
}
