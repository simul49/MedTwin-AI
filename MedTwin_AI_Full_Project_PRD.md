# MedTwin AI — Product Requirements Document (PRD)

**Project name:** MedTwin AI  
**Product description:** Real-World Medical & Healthcare Digital Twin & AI Safety Platform  
**Document type:** Product Requirements Document  
**Version:** 1.0  
**Status:** Proposed baseline for team review  
**Audience:** Product owner, software engineering team, AI/ML team, UI/UX designers, QA, academic supervisors and project evaluators  
**Important status note:** This document defines intended requirements and a proposed implementation. It does not claim that the features are already implemented, clinically validated, certified, or approved for medical use.

---

## 1. Executive Summary

MedTwin AI is an AI-powered healthcare decision-support platform intended to help people organize and understand authorized health information. It combines a structured patient Digital Twin, natural-language interaction, retrieval-augmented generation (RAG), specialized AI agents, personalized educational recommendations, real-time communication, and AI Trust & Safety evaluation.

The product has two connected surfaces:

1. **Public website:** An informational website for everyone. It explains the product, its solutions, workflow, research direction, privacy approach, and safety limitations. Visitors can explore it without signing in.
2. **Authenticated application:** Role-based experiences for patients, authorized healthcare professionals (doctors), and administrators. These experiences contain private records and operational features and must be protected by authentication, authorization, consent, and audit controls.

The platform is designed to support understanding and workflow—not to replace clinicians. It must not present AI-generated information as a definitive diagnosis, independently prescribe medication, or claim that an AI safety score guarantees correctness. Emergency situations must be handled through clear escalation language rather than automated care management.

The initial release should prioritize the public website, authentication and roles, consent-aware patient records, a basic Digital Twin, document upload and review, a grounded AI assistant, a limited doctor view for explicitly authorized patients, audit logging, and clear safety disclosures. More advanced multi-agent workflows and synthetic/deepfake content analysis should be introduced only after their requirements, evaluation datasets, and limitations are documented.

## 2. Product Vision

Create a trusted healthcare intelligence platform where authorized health information can be represented as a structured Digital Twin and explained through transparent, context-aware, safety-aware AI interactions—with human healthcare professionals kept in the loop.

### 2.1 Product principles

- **Patient-centered:** Make health information easier to organize and understand.
- **Evidence-aware:** Ground supported answers in approved sources and display references where available.
- **Privacy by design:** Access only the data required for a task and only with appropriate authorization.
- **Human oversight:** AI supports, but does not replace, professional clinical judgment.
- **Transparency:** Distinguish verified records, user-entered information, extracted content, and AI-generated interpretations.
- **Uncertainty-aware:** Communicate limitations and avoid overstating model confidence.
- **Accessible and multilingual:** Design for understandable English and Chinese experiences, with localization reviewed by qualified speakers.
- **Incremental delivery:** Clearly label planned, experimental, and implemented capabilities.

## 3. Problem Statement

1. Patients may struggle to understand medical reports, symptoms, medications, laboratory results, and health terminology.
2. Health information can be fragmented across documents, observations, measurements, and clinical visits.
3. Healthcare professionals may need to review large amounts of patient information before a consultation.
4. Generative AI can produce unsupported, incomplete, or incorrect medical statements when outputs are not grounded and evaluated.
5. AI-generated or manipulated healthcare media can create verification and trust challenges.
6. A healthcare AI system therefore requires useful assistance alongside explicit privacy, authorization, safety, evaluation, and human-oversight mechanisms.

## 4. Goals and Non-Goals

### 4.1 Goals

- Provide a public website that clearly explains MedTwin AI.
- Support secure patient, doctor, and administrator access with least-privilege authorization.
- Create a structured, traceable patient Digital Twin from authorized data.
- Allow patients to upload and review supported health documents.
- Provide natural-language explanation, summarization, and information retrieval.
- Use RAG over approved knowledge sources where appropriate.
- Separate AI workflow tasks into independently testable components or agents.
- Present understandable AI safety findings and supporting evidence without implying guaranteed correctness.
- Allow patients to grant, review, and revoke professional access where the workflow permits.
- Provide audit trails for sensitive data access and important actions.
- Support selected REST APIs and real-time WebSocket features when needed.
- Establish measurable acceptance criteria and a phased delivery plan.

### 4.2 Non-goals for the initial release

- Replacing a doctor or other qualified healthcare professional.
- Providing definitive diagnosis or autonomous treatment decisions.
- Independently prescribing, starting, stopping, or changing medication.
- Emergency triage or autonomous emergency management.
- Automatically importing data from every hospital, wearable, or health system.
- Claiming regulatory compliance, clinical validation, or certification without documented evidence.
- Treating a synthetic/deepfake detector result as proof that content is genuine or fake.
- Training foundation models on private patient data by default.
- Enabling doctor access to patient data without explicit authorization or another valid, documented access basis.

## 5. Users, Personas and Roles

### 5.1 Public visitor

**Needs:** Understand what the platform does, its limitations, safety approach, research direction, and how to get started.  
**Permissions:** Read public pages, change language, access public contact resources, and navigate to sign-in/registration. No access to private health data.

### 5.2 Patient

**Needs:** Manage personal health information, upload records, review a health timeline, understand documents, ask the AI assistant questions, view educational suggestions, and control sharing.  
**Permissions:** Access only their own records and actions permitted by their account and consent settings.

### 5.3 Doctor / authorized healthcare professional

**Needs:** Review information for patients who have granted appropriate access, inspect source records, prepare summaries, communicate, and document follow-up plans.  
**Permissions:** Access only explicitly authorized patients and only permitted data categories. AI-generated summaries must remain distinguishable from clinician-authored notes.

### 5.4 Administrator

**Needs:** Manage accounts, roles, system configuration, approved knowledge sources, operational status, and audit review.  
**Permissions:** Administrative access must not automatically grant unrestricted access to medical content. Privileged actions require least privilege, audit logging, and appropriate safeguards.

### 5.5 Research / system operator (optional, controlled)

May manage evaluation datasets, model versions, and non-production experiments. Must use synthetic or properly de-identified data unless a separate approved basis permits otherwise.

## 6. Product Scope and Modules

1. Public website and content management
2. Authentication, account recovery, and role-based authorization
3. Consent and professional-access management
4. Patient Digital Twin
5. Health timeline and observations
6. Medical document upload, extraction, and review
7. AI Healthcare Assistant
8. NLP and intent analysis
9. RAG knowledge retrieval and vector store
10. AI agent orchestration
11. Personalized educational recommendation engine
12. AI Trust & Safety evaluation
13. Synthetic/manipulated-content analysis (experimental/phase-gated)
14. Patient and doctor dashboards
15. Appointments, messaging, and selected real-time communication
16. Notifications and reminders
17. Audit logs and security controls
18. Administration and system monitoring
19. Research/evaluation tools (controlled, optional)

## 7. Public Website Requirements

### 7.1 Brand and identity

- Official project name: **MedTwin AI**
- Website/logo text may use: **MedTwin.ai**
- Full project description: **Real-World Medical & Healthcare Digital Twin & AI Safety Platform**
- The full project name must appear prominently in the homepage hero section and again in the footer.
- The compact MedTwin.ai brand remains in the navbar.
- Use a professional, accessible digital-health visual identity. A blue/white palette is a proposed starting point, not a fixed technical requirement.

### 7.2 Required navbar layout

**Left:** MedTwin.ai logo  
**Center group:** About Us · Solutions · How It Works · Research · Trust & Safety  
**Flexible space**  
**Right group:** EN / 中文 language selector · Patient / Doctor role selector

- Do not include a separate “Home” navbar item.
- Clicking the logo navigates to the homepage.
- The five primary links remain grouped together.
- EN / 中文 is a language selector, not one of the five primary links.
- Patient / Doctor is a portal/role selector, not a public content page.
- On narrow screens, collapse navigation into a responsive menu while preserving access to language and portal selection.
- The active section/page should have a visible state and keyboard-accessible focus.

### 7.3 Public pages and content

#### 7.3.1 Homepage
- Show “MedTwin AI” and the full project description.
- Explain the value proposition in clear, non-clinical language.
- Provide calls to action such as “Explore Solutions” and “How It Works.”
- Introduce Digital Twin, AI Assistant, RAG/AI Agents, Recommendations, and Trust & Safety.
- Include a simple workflow illustration.
- Include a clear medical limitation notice.
- Do not imply the product is clinically validated unless evidence supports that claim.

#### 7.3.2 About Us
- Product mission and vision.
- Problems the platform aims to address.
- Product principles: privacy, transparency, safety, and human oversight.
- Team or organization information only when confirmed.

#### 7.3.3 Solutions
- Patient Digital Twin.
- AI Healthcare Assistant.
- AI agents and RAG.
- Personalized educational recommendations.
- Patient–doctor collaboration.
- Trust & Safety evaluation.
- Synthetic/manipulated-content analysis, labeled experimental until validated.

#### 7.3.4 How It Works
Explain the proposed flow:
1. User provides or uploads authorized health information.
2. The platform validates and organizes it.
3. The Digital Twin presents structured records and timeline events.
4. The assistant identifies intent and retrieves relevant approved knowledge and authorized patient context.
5. Safety checks evaluate the draft response.
6. The user receives an explanation with references, limitations, and escalation guidance where appropriate.
7. The user can share selected information with an authorized professional.

#### 7.3.5 Research
- Explain system architecture and evaluation methodology.
- Publish research items only when approved for public release.
- Label proposed research, work in progress, preprints, and peer-reviewed publications accurately.
- Do not invent publication claims or performance metrics.

#### 7.3.6 Trust & Safety
- Explain consent, data access, security, audit logs, AI limitations, source grounding, and uncertainty.
- Explain that the AI Trust/Safety indicator is an evaluation aid, not a guarantee of medical correctness.
- Explain that synthetic-content analysis may produce false positives and false negatives.
- Provide links to Privacy Policy, Terms of Use, and Medical Disclaimer.

#### 7.3.7 Contact / legal pages
- Contact page or contact method, once a verified address is provided.
- Privacy Policy.
- Terms of Use.
- Medical Disclaimer.
- Accessibility statement where appropriate.
- Cookie notice/preferences if applicable to actual tracking technologies and relevant law.

### 7.4 Public website acceptance criteria

- All five navbar links navigate to their intended public sections/pages.
- Logo returns to the homepage.
- Language selection changes all supported localized interface content and retains the selection appropriately.
- Patient / Doctor opens an explicit choice of portal or sign-in route.
- The site works on desktop, tablet, and mobile viewports.
- Public pages contain no private patient data or test credentials.
- Footer contains the full project name, key links, and a clear medical disclaimer.
- Accessibility checks cover keyboard navigation, contrast, labels, and semantic structure.

## 8. Authentication, Authorization and Consent

### 8.1 Authentication requirements

- Sign up and sign in for supported roles.
- Email or other approved identity verification, as selected for deployment.
- Secure password reset and session management.
- Logout and session invalidation.
- Rate limiting and protection against brute-force attempts.
- Multi-factor authentication should be considered for privileged accounts and production clinical workflows.
- Never store plaintext passwords.
- Use secure, HTTP-only cookies or an appropriately secured token approach; define expiry, refresh, revocation, and storage rules before implementation.

### 8.2 Authorization requirements

- Enforce access control on the backend for every protected request.
- Do not rely on frontend route guards alone.
- Default to deny unless a permission is explicitly granted.
- Verify role, resource ownership, patient consent/access grant, and permission scope.
- Log sensitive access and privileged actions.
- Prevent insecure direct-object references by checking authorization for every record ID.

### 8.3 Patient-to-doctor access workflow

1. Patient selects a doctor/account or receives a valid access request.
2. System displays the requested access scope and duration.
3. Patient grants or rejects the request.
4. System records grantor, recipient, scope, timestamp, expiry, and status.
5. Doctor can access only the granted information.
6. Patient can review active grants and revoke them where permitted.
7. Revocation blocks future access; already downloaded/exported information cannot be technically recalled and must be addressed in policy.

### 8.4 Authorization acceptance criteria

- A patient cannot access another patient's records by changing a URL or API identifier.
- A doctor without a valid access grant cannot read protected patient information.
- Revoked or expired grants no longer authorize future requests.
- Every grant, revocation, and sensitive access event is recorded in an audit log.
- Administrative privileges are scoped and audited.

## 9. Patient Digital Twin

The Digital Twin is a structured, traceable representation of authorized health information. It is not a complete or necessarily clinically verified representation of a person's health.

### 9.1 Data categories

- Basic patient profile and relevant preferences.
- Medical history.
- Symptoms and health observations.
- Allergies and reactions, with source and status.
- Medications as reported or recorded, with source and last-updated date.
- Laboratory results and units, with reference ranges when available.
- Doctor notes, clearly attributed to their author.
- Uploaded documents and extraction status.
- Health measurements and their timestamps.
- AI interaction history, subject to retention and privacy settings.
- Alerts and timeline events.
- Data source, timestamp, provenance, and verification status for each item.

### 9.2 Digital Twin features

- Overview dashboard.
- Health timeline.
- Search and filters.
- Record detail view.
- Document attachment and source provenance.
- Mark extracted fields for user confirmation.
- Display missing, conflicting, or outdated information.
- Share selected information with an authorized professional.
- Export/delete workflows according to policy and applicable requirements.

### 9.3 Data integrity requirements

- Distinguish user-entered data, imported records, extracted text, clinician-authored information, and AI-generated summaries.
- Never silently overwrite a source record with AI interpretation.
- Keep source links or document references for extracted facts.
- Record updates and relevant audit events.
- Avoid inferring diagnoses or medical facts from incomplete information.

## 10. Medical Document Upload and Processing

### 10.1 Supported scope

Initial file types should be explicitly configured, for example PDF, PNG, and JPEG. Additional formats should be enabled only after security and extraction testing.

### 10.2 Workflow

1. Authenticate and verify the user's authorization.
2. Validate file extension, MIME type, size, and content signature.
3. Scan for malicious content where infrastructure supports it.
4. Store the original file in protected object/file storage.
5. Extract text or OCR content.
6. Present extracted fields and confidence/quality limitations for user review.
7. Save confirmed structured data with source provenance.
8. Record processing status and failures.
9. Allow deletion according to retention policy.

### 10.3 Requirements

- Enforce upload limits and safe file naming.
- Store files outside publicly served directories.
- Use short-lived authorized download links if object storage is used.
- Do not treat OCR output as clinically verified.
- Prevent document content from overriding system instructions or injecting commands into AI workflows.
- Clearly communicate extraction failures and ask for correction where necessary.

## 11. AI Healthcare Assistant

### 11.1 Supported use cases

- Explain medical terminology in plain language.
- Summarize uploaded reports, indicating which document was used.
- Answer general healthcare information questions using approved sources where available.
- Retrieve authorized information from the user's Digital Twin.
- Summarize health information for the user.
- Suggest educational resources and questions to discuss with a professional.
- Explain uncertainty and identify missing context.
- Provide safety notices and professional-review guidance where appropriate.

### 11.2 Out-of-scope or restricted use cases

- Definitive diagnosis or assurance that a user does not have a condition.
- Independent prescribing or changes to medication.
- Personalized treatment decisions presented as clinician-approved.
- Emergency management as a substitute for emergency services.
- Claims that AI output is medically correct because a numerical score is high.

### 11.3 Conversation behavior

- Keep conversation context within defined privacy boundaries.
- Retrieve only information needed for the current request.
- Identify whether a response uses general knowledge, approved reference material, or patient-specific records.
- Show citations or source titles when retrieval sources are available.
- Ask clarifying questions when critical context is missing.
- Distinguish generated suggestions from verified medical records.
- Provide safe escalation guidance for urgent or emergency language according to reviewed policies.
- Do not expose hidden prompts, secrets, other users' data, or internal credentials.

### 11.4 AI response structure (recommended)

- **Answer:** Plain-language explanation.
- **Context used:** Documents or Digital Twin sections referenced, where appropriate.
- **Sources:** Approved sources used for the answer.
- **Limitations:** Missing information, uncertainty, or conflicting sources.
- **Next step:** Educational follow-up or professional review suggestion when appropriate.

## 12. AI Agent Architecture

A modular workflow is proposed. The team may implement these as separate services, modules, or orchestrated functions; they do not need to be independent autonomous agents in the first release.

1. **Intent Detection Agent:** Classifies the user's request and identifies its risk category.
2. **Medical Context Agent:** Extracts relevant context from the current interaction.
3. **Digital Twin Agent:** Retrieves only authorized and relevant patient information.
4. **Knowledge / RAG Agent:** Retrieves relevant passages from approved sources.
5. **Recommendation Agent:** Generates educational resources and follow-up suggestions within scope.
6. **Safety / Trust Agent:** Checks policy, source grounding, contradictions, unsupported claims, and escalation requirements.
7. **Response Generation Agent:** Produces the final user-facing answer from approved context and safety findings.

### 12.1 Orchestration requirements

- Each stage has defined input/output schemas.
- Agent calls are logged with trace IDs and model/version metadata, without logging unnecessary sensitive content.
- Tool permissions are narrowly scoped.
- The system must not let retrieved documents or user uploads change system-level policy.
- Safety evaluation must occur before output is displayed.
- If a safety check fails, the system should refuse, ask for clarification, return a safer limited response, or route to human review.
- Add timeouts, retry limits, token/cost limits, and fallback behavior.
- Keep a non-agent baseline for comparison during evaluation.

## 13. NLP and Intent Analysis

### 13.1 Capabilities

- Text normalization and preprocessing.
- Intent classification.
- Medical-term/entity extraction where implemented and evaluated.
- Query rewriting for retrieval.
- Document text processing.
- Optional sentiment/emotional-tone analysis only where it adds justified interaction value.

### 13.2 Requirements

- Support English initially; Chinese support requires dedicated localization and evaluation.
- Track model version and supported language.
- Measure intent classification precision/recall on a labeled test set.
- Treat extracted medical entities as candidate information, not verified facts.
- Avoid using sentiment analysis to infer diagnoses or make consequential decisions.

## 14. RAG and Vector Database

RAG is intended to improve grounding by retrieving relevant content from an approved knowledge base. It cannot eliminate hallucinations or guarantee correctness.

### 14.1 Proposed pipeline

1. Receive and validate the user query.
2. Identify intent and access permissions.
3. Generate query embedding using a selected embedding model.
4. Retrieve relevant chunks from the vector store and, if needed, a keyword search index.
5. Apply source permissions and filters.
6. Rank results and apply relevance thresholds.
7. Combine retrieved evidence with authorized Digital Twin context.
8. Generate a response with source references.
9. Run safety and consistency evaluation.
10. Display the answer, sources, and limitations; log relevant trace metadata.

### 14.2 Knowledge source governance

- Maintain a source registry with title, publisher, version/date, source URL or identifier, ingestion date, license/usage status, and review status.
- Prioritize authoritative, maintained healthcare sources.
- Remove or refresh outdated content according to a defined policy.
- Keep patient-specific documents isolated from the general knowledge corpus unless an explicitly approved feature requires otherwise.
- Prevent one user's private documents from being retrieved for another user.
- Do not ingest copyrighted or restricted content without appropriate rights.

### 14.3 Vector storage

Candidate options include Qdrant or PostgreSQL with pgvector, subject to the team's hosting and operational constraints. The PRD does not lock the project to a single vendor. MySQL or PostgreSQL may serve as the primary relational database depending on final architecture.

### 14.4 RAG evaluation

Measure retrieval relevance, source correctness, citation correctness, groundedness, answer completeness, and behavior when no useful source is available. Include adversarial and prompt-injection test cases.

## 15. AI Trust & Safety Evaluation

The Trust/Safety module provides an interpretable evaluation indicator. It must not be presented as a guarantee of medical correctness or as a validated clinical risk score unless independently validated for that use.

### 15.1 Evaluation factors

| Factor | Purpose |
|---|---|
| Source / knowledge grounding | Checks whether claims are supported by retrieved evidence where applicable. |
| Reference availability | Records whether sources or evidence are available. |
| Context match | Checks consistency with authorized patient context. |
| Contradiction check | Looks for conflicts with known or retrieved information. |
| Safety rules | Checks the response against defined healthcare safety policies. |
| Unsupported claims | Flags statements lacking adequate support. |
| Risk routing | Checks whether the request needs refusal, clarification, or professional/emergency escalation. |

### 15.2 Display rules

- Explain the factors contributing to the indicator.
- Use labels such as “sources found,” “context incomplete,” or “needs review” where useful.
- Avoid implying that a single score measures overall medical truth.
- A low score should trigger a defined fallback; a high score must not bypass safety rules.
- Record evaluation version and relevant evidence references.
- Validate the scoring method against labeled test cases before exposing it publicly.

## 16. Synthetic / Deepfake Healthcare Content Analysis

This is an optional, phase-gated capability and must be labeled experimental until a suitable evaluation has been completed.

### 16.1 Supported workflow

1. User uploads supported content.
2. Validate authorization, file type, size, and security.
3. Preprocess content using a defined pipeline.
4. Run the selected detector or analysis model.
5. Return a risk assessment with indicators and uncertainty.
6. Recommend verification through original source, trusted publisher, or qualified professional.

### 16.2 Requirements and limitations

- Clearly state supported modalities (image, document, audio, or video) for each implementation.
- Treat results as probabilistic indicators.
- Explain that false positives and false negatives are possible.
- Do not claim that the detector proves authenticity or manipulation.
- Define retention and deletion policies for uploaded content.
- Evaluate performance across relevant content types and conditions before release.
- Avoid consequential actions based solely on the detector result.

## 17. AI Recommendation Engine

### 17.1 Supported recommendations

- Educational resources relevant to the user's question.
- Questions to consider discussing with a healthcare professional.
- Follow-up reminders based on information explicitly stored by the user.
- Explanations of available health information.
- Context-aware next-step guidance within the platform's defined scope.

### 17.2 Restrictions

- Do not independently prescribe or change medications.
- Do not present recommendations as clinician-approved unless a clinician has reviewed and approved them.
- Explain the information and assumptions used.
- Provide a way to dismiss or correct suggestions.
- Avoid recommendations when context is insufficient or risk is beyond the system's validated scope.

## 18. Real-Time Communication and Notifications

### 18.1 Candidate features

- In-app messaging between a patient and an authorized doctor.
- Appointment requests and status updates.
- Notifications for consent requests, messages, and user-configured reminders.
- WebSocket updates for selected events.
- Video consultation through WebRTC or an approved provider only if required and feasible.

### 18.2 Requirements

- Verify the relationship and permission before allowing a conversation.
- Protect messages and attachments in transit and at rest.
- Define message retention, export, deletion, and audit behavior.
- Do not treat a general messaging feature as an emergency response channel.
- Clearly display delivery/status information without promising real-time availability unless implemented.

## 19. Role-Based Dashboards

### 19.1 Patient dashboard

- Health overview.
- Digital Twin profile.
- Health timeline and observations.
- Medical records and document upload.
- AI Healthcare Assistant.
- Educational recommendations and tasks.
- Appointments and messages, if implemented.
- Notifications.
- Consent and doctor-access management.
- Profile, language, privacy, and account settings.

### 19.2 Doctor dashboard

- Dashboard overview.
- Authorized patient directory.
- Patient details and permitted Digital Twin sections.
- Medical history and uploaded records.
- AI-generated clinical-information summaries, clearly labeled as drafts.
- Appointments and communication.
- Care-plan notes, if implemented and appropriately governed.
- Reports and settings.

### 19.3 Admin dashboard

- Account and role management.
- Access-grant oversight and security events.
- Approved knowledge-source management.
- Model/configuration version metadata.
- System health and job status.
- Audit-log search with restricted access.
- Feature flags and release status.
- No unrestricted medical-data browsing by default.

## 20. High-Level Technical Architecture

### 20.1 Proposed stack

| Layer | Proposed technology / responsibility |
|---|---|
| Public and application frontend | Vue 3, TypeScript, Vite, Tailwind CSS, Pinia |
| UI components | Naive UI or another accessible component library; finalize one choice |
| Core backend | Spring Boot 3, REST APIs, validation, business rules, authorization |
| AI service | Python with FastAPI for model integration, RAG, and evaluation |
| Relational database | MySQL or PostgreSQL; select one as the source of truth |
| Vector storage | Qdrant or pgvector, selected after a proof of concept |
| File storage | Private object storage or protected filesystem storage |
| Authentication | Spring Security and a defined session/token strategy |
| Real-time | WebSocket; WebRTC only if video is implemented |
| Workflow automation | n8n for selected non-critical integrations where justified |
| LLM integrations | Provider abstraction for approved compatible models, subject to privacy and cost review |
| Deployment | Docker and an appropriate server/cloud environment |
| Monitoring | Structured logs, metrics, health checks, error tracking, and alerting |

### 20.2 Architecture principles

- Keep core authorization and data ownership rules in the backend.
- Keep AI orchestration separate from the primary business API where practical.
- Use typed request/response schemas and versioned API contracts.
- Store structured medical data in the relational database; store files in protected file/object storage.
- Keep vector indexes rebuildable from approved source records.
- Never put API keys or secrets in frontend code.
- Use environment-specific configuration and secret management.
- Support migration, backups, restore testing, and rollback.
- Minimize personal data in application logs and AI traces.

## 21. Data Model — Initial Entities

A proposed initial relational model includes:

- `users`: account identity, status, timestamps.
- `roles` / `user_roles`: role assignments and permission mapping.
- `patient_profiles`: patient-specific profile fields.
- `doctor_profiles`: professional profile fields and verification status where required.
- `consent_grants`: patient, recipient, scope, status, grant date, expiry, revocation.
- `health_records`: record category, value or structured payload, source, author, timestamps, verification status.
- `observations`: measurement/code, value, unit, observed time, source.
- `allergies`: substance, reaction, status, source, reviewed status.
- `medications`: reported medication information, source, dates, status; not an autonomous prescribing mechanism.
- `documents`: owner, protected storage reference, type, size, hash, processing status, timestamps.
- `document_extractions`: extracted fields, confidence/quality metadata, review status, source spans.
- `timeline_events`: event type, time, source reference.
- `conversations` / `messages`: participants, authorization relationship, message metadata.
- `ai_interactions`: user, conversation, request type, model/version, source references, safety result metadata, timestamps.
- `knowledge_sources`: publisher, title, version/date, source identifier, review status.
- `knowledge_chunks`: source reference, text/chunk metadata, vector identifier, access classification.
- `recommendations`: content, basis, type, status, dismissal/acceptance metadata.
- `appointments`: participants, status, scheduled time, timezone.
- `notifications`: recipient, type, delivery/read status.
- `audit_logs`: actor, action, resource type/ID, timestamp, outcome, trace ID, limited metadata.
- `model_versions` / `evaluation_runs`: model/config versions, evaluation set version, metrics, run status.
- `deepfake_analyses`: owner, file reference, model/version, result, uncertainty, limitations, timestamps.

The final schema must define primary keys, foreign keys, indexes, retention, encryption, and deletion behavior. Do not store sensitive medical information in generic free-text fields when a structured, access-controlled model is appropriate.

## 22. API Requirements (Illustrative)

All protected endpoints must authenticate and authorize every request. The following are conceptual endpoint examples, not a final API contract.

### Authentication and account
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/password/forgot`
- `POST /api/v1/auth/password/reset`
- `GET /api/v1/me`

### Digital Twin and health records
- `GET /api/v1/patient/digital-twin`
- `GET /api/v1/patient/records`
- `POST /api/v1/patient/records`
- `GET /api/v1/patient/timeline`
- `POST /api/v1/patient/documents`
- `GET /api/v1/patient/documents/{documentId}`
- `DELETE /api/v1/patient/documents/{documentId}`

### Consent and access
- `POST /api/v1/consent/grants`
- `GET /api/v1/consent/grants`
- `POST /api/v1/consent/grants/{grantId}/revoke`
- `GET /api/v1/doctor/authorized-patients`

### AI assistant and recommendations
- `POST /api/v1/ai/chat`
- `GET /api/v1/ai/conversations`
- `GET /api/v1/ai/conversations/{conversationId}`
- `GET /api/v1/recommendations`
- `POST /api/v1/recommendations/{recommendationId}/feedback`

### Doctor workflows
- `GET /api/v1/doctor/patients/{patientId}/summary`
- `GET /api/v1/doctor/patients/{patientId}/records`
- `POST /api/v1/appointments`
- `GET /api/v1/appointments`

### Trust/safety and content analysis
- `POST /api/v1/safety/evaluate` (internal/service-restricted where possible)
- `POST /api/v1/content-analysis`
- `GET /api/v1/content-analysis/{analysisId}`

### Admin and operations
- `GET /api/v1/admin/audit-logs`
- `GET /api/v1/admin/knowledge-sources`
- `POST /api/v1/admin/knowledge-sources`
- `GET /api/v1/admin/system/health`

API names and request/response payloads must be finalized in an OpenAPI specification. Avoid exposing internal safety endpoints publicly without appropriate authorization and rate limits.

## 23. Security, Privacy and Governance

### 23.1 Security baseline

- TLS for network traffic.
- Encryption at rest for database, backups, and file storage where supported.
- Secure password hashing using a modern adaptive algorithm.
- Input validation and output encoding.
- CSRF protection where cookie-based authentication is used.
- CORS allow-list.
- Rate limiting and abuse monitoring.
- Secure HTTP headers.
- Dependency and container image scanning.
- Secret management outside source control.
- Regular backups and tested restore procedures.
- Least-privilege database/service accounts.
- Audit logging for sensitive actions.
- Security review before production deployment.

### 23.2 Privacy baseline

- Collect only data needed for declared features.
- Explain data use, storage, sharing, retention, and deletion.
- Obtain consent or another documented valid basis where required.
- Make access grants visible and manageable.
- Define whether AI providers receive prompts or patient context and assess provider terms before integration.
- Do not send identifiable health information to third-party models unless the integration has been reviewed and approved for that use.
- Define retention and deletion for documents, messages, prompts, embeddings, logs, and backups.
- Use synthetic data during development and demos.
- De-identify research datasets and document access approval.
- Assess applicable privacy and healthcare laws based on deployment jurisdictions; do not claim compliance without review.

### 23.3 Clinical and AI governance

- Maintain a versioned list of supported and unsupported use cases.
- Review safety policies with qualified healthcare input.
- Record model and prompt/configuration versions.
- Maintain a test set for common, edge, adversarial, and high-risk scenarios.
- Track known failure modes.
- Provide a feedback/reporting route.
- Define incident handling and model rollback.
- Require human review for clinical summaries or plans before they are treated as clinician-approved.

## 24. Non-Functional Requirements

### Performance (initial targets; validate through testing)
- Public pages should target a Largest Contentful Paint (LCP) of 2.5 seconds or less at the 75th percentile under a defined test environment.
- Typical non-AI API requests should target p95 latency below 500 ms under agreed test load, excluding large file processing and external provider latency.
- AI response latency should be measured separately and communicated honestly.
- File processing should expose progress/status for longer jobs.

### Availability and recovery
- Define an availability target before production launch.
- Back up databases and critical metadata on a documented schedule.
- Test recovery from backup.
- Define recovery point objective (RPO) and recovery time objective (RTO) based on project needs.

### Scalability and maintainability
- Separate modules by responsibility.
- Use versioned APIs and database migrations.
- Support structured logs and trace IDs.
- Monitor queue depth, failed jobs, model errors, latency, and cost.
- Avoid hard-coding one LLM provider into core business logic.

### Accessibility and localization
- Target WCAG 2.2 AA as a design goal, subject to testing.
- Support keyboard navigation and screen-reader labels.
- Ensure readable contrast and responsive layouts.
- Localize all visible interface strings for English and Simplified Chinese if both languages are released.
- Review medical translations carefully; do not rely solely on raw machine translation.

## 25. Analytics and Success Metrics

Metrics must be privacy-conscious and should not be used to infer clinical benefit without appropriate evidence.

### Public website
- Public page load performance.
- Navigation success and mobile usability.
- Visitors who explore solutions or research.
- Portal-selection clicks.
- Accessibility and broken-link checks.

### Product usage
- Successful sign-in and onboarding completion.
- Document upload and extraction completion rates.
- Percentage of extracted fields reviewed or corrected.
- AI response feedback and source-click rate.
- Consent grant/revoke completion reliability.
- Support incidents and reported confusing outputs.

### AI quality and safety
- Retrieval relevance and citation correctness.
- Unsupported-claim rate on a reviewed evaluation set.
- Appropriate refusal/escalation rate for predefined risk scenarios.
- Contradiction detection performance.
- Intent classification precision/recall.
- Latency, cost, and failure rates by model version.
- False positive/false negative rates for any content detector on a labeled test set.

Do not define success solely by the number of AI conversations or by an unvalidated Trust/Safety score.

## 26. Testing and Acceptance Strategy

### 26.1 Test layers
- Unit tests for business rules, validators, permissions, and parsers.
- Integration tests for database, file storage, RAG, and model providers.
- API contract tests.
- End-to-end tests for public navigation, sign-in, consent, upload, AI assistant, and doctor access.
- Security tests for IDOR, role escalation, injection, file upload abuse, session handling, and rate limits.
- AI evaluations for grounding, citation correctness, unsupported claims, refusal behavior, and prompt injection.
- Accessibility and responsive UI tests.
- Performance and recovery tests.

### 26.2 Core release acceptance criteria
- Public visitor can browse all public pages without authentication.
- Logo navigates home; the five navbar links work; language and portal selectors are accessible.
- Patient and doctor access routes are distinct.
- Protected APIs reject unauthenticated and unauthorized requests.
- A doctor cannot access a patient without a valid grant.
- Patient records display source and verification status where available.
- Document processing shows status and does not silently convert extracted text into verified facts.
- AI responses identify sources when retrieval is used and clearly distinguish generated content from source records.
- Safety rules can prevent or limit an unsafe response.
- Audit events are generated for sensitive access and consent changes.
- No real patient data or secrets appear in demo screenshots, logs, or repository files.
- Backup restore and basic incident response have been tested before production use.

## 27. Delivery Roadmap

### Phase 0 — Discovery and design
- Confirm scope, jurisdictions, intended users, and project status.
- Finalize site map, user flows, design system, and data classification.
- Define the first approved knowledge sources.
- Review security and clinical safety boundaries.
- Produce ERD, API contract, and architecture diagram.

### Phase 1 — Public website foundation
- Responsive public pages.
- Navbar and footer.
- English localization and Chinese-ready architecture.
- Privacy, Terms, Medical Disclaimer placeholders reviewed before public launch.
- Basic analytics that respect privacy.

### Phase 2 — Identity and patient data foundation
- Authentication and role-based access.
- Patient profile and Digital Twin data model.
- Consent/access grant workflow.
- Audit logging.
- Protected document upload and processing status.

### Phase 3 — AI assistant and RAG MVP
- Approved knowledge ingestion.
- Retrieval and citations.
- Basic assistant with authorized patient context.
- Safety policy checks and fallback behavior.
- AI evaluation dataset and baseline measurements.

### Phase 4 — Doctor collaboration
- Authorized patient directory.
- Source-linked patient summaries.
- Appointments/messages if in scope.
- Clinician review/approval workflow for drafts.
- Consent revocation and access audit validation.

### Phase 5 — Recommendations and advanced safety
- Educational recommendations and user-controlled reminders.
- Expanded safety evaluation and dashboards.
- Synthetic/manipulated-content analysis only after dataset evaluation and clear uncertainty messaging.
- Optional WebSocket or WebRTC capabilities.

### Phase 6 — Hardening and release readiness
- Security review and penetration testing.
- Performance, accessibility, backup, and restore tests.
- Privacy and applicable legal review.
- Documentation, monitoring, incident process, and release checklist.
- Limited pilot with synthetic or appropriately authorized data before broader rollout.

Phases may overlap depending on team capacity, but sensitive-data access and safety controls must not be postponed until after a feature is built.

## 28. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| AI generates incorrect health information | RAG, source visibility, safety checks, clear limitations, human oversight, and evaluation. |
| Unauthorized medical-data access | Backend authorization, consent scopes, least privilege, audit logs, and security testing. |
| Extracted document data is wrong | Show source, extraction status, review workflow, and correction capability. |
| Misleading safety score | Explain factors and limitations; never treat the score as proof of correctness. |
| Deepfake detector false positives/negatives | Report probabilistic indicators and recommend source verification. |
| Third-party model privacy exposure | Provider review, data minimization, no sensitive prompts by default without approval. |
| Scope too large for a student project | Deliver a thin, secure MVP and phase advanced features. |
| Unclear implementation status | Maintain feature-status labels: Planned, In Development, Implemented, Evaluated, Released. |
| Language inaccuracies | Human review of localized medical terminology. |
| Vendor lock-in or cost growth | Provider abstraction, usage limits, monitoring, and fallback design. |

## 29. Open Decisions

The following choices should be confirmed before implementation:

1. Initial launch jurisdiction and applicable legal requirements.
2. Whether the first release is a prototype, academic demonstration, pilot, or public production service.
3. Whether the primary relational database will be MySQL or PostgreSQL.
4. Whether the vector store will be Qdrant or pgvector.
5. Authentication approach and identity verification requirements.
6. Exact supported upload types and size limits.
7. Approved healthcare knowledge sources and update schedule.
8. Initial LLM and embedding providers, privacy terms, and cost limits.
9. Whether messaging, appointments, and video are in the MVP.
10. Which synthetic-content modalities, if any, will be implemented first.
11. Data retention, export, deletion, and backup policy.
12. Whether professional verification is required before doctor accounts can access patient information.

## 30. Glossary

- **Digital Twin:** A structured digital representation of selected real-world health information; it may be incomplete or outdated.
- **RAG:** Retrieval-Augmented Generation; a method that retrieves relevant documents and supplies them as context to a language model.
- **Vector database:** Storage and search for numerical embeddings used in semantic retrieval.
- **AI agent:** A software component responsible for a defined task in an orchestrated workflow.
- **NLP:** Natural Language Processing.
- **Trust/Safety indicator:** An interpretable set of checks or measurements; not a guarantee of medical correctness.
- **Synthetic/deepfake analysis:** Automated analysis for indicators of generated or manipulated content, with uncertainty and error risk.
- **RBAC:** Role-Based Access Control.
- **Audit log:** A record of security-relevant actions and access events.
- **Human-in-the-loop:** A workflow where a qualified person reviews or makes decisions that AI must not make independently.

---

## Appendix A — Proposed Public Website Sitemap

- `/` — Homepage (logo returns here; no Home navbar item)
- `/about`
- `/solutions`
- `/how-it-works`
- `/research`
- `/trust-safety`
- `/privacy`
- `/terms`
- `/medical-disclaimer`
- `/contact`
- `/auth/login`
- `/auth/register`
- `/patient/*` — protected patient application
- `/doctor/*` — protected doctor application
- `/admin/*` — protected administrator application

## Appendix B — Recommended MVP Priority

**Must have**
- Public homepage and five main sections.
- Navbar exactly as specified.
- Language selector architecture for English and Chinese.
- Secure authentication and role-based authorization.
- Patient profile and basic Digital Twin.
- Document upload with validation and processing status.
- AI assistant using approved sources with citations where available.
- Consent-aware doctor access.
- Audit logs and safety disclosures.

**Should have**
- Health timeline and observations.
- Patient-managed access grants.
- Doctor dashboard and source-linked summaries.
- Recommendation feedback.
- Basic admin knowledge-source management.
- Evaluation dashboard for retrieval and safety.

**Could have after evaluation**
- Real-time messaging and WebSocket events.
- Appointments and video consultations.
- Advanced multi-agent orchestration.
- Synthetic/deepfake detection for selected modalities.
- More complex personalization and automation.

**Release gate:** Any feature handling real health information must pass authorization, privacy, safety, and test requirements before it is enabled for real users.
