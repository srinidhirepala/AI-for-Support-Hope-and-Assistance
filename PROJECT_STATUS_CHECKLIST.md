# ASHA AI Project Status Checklist

## Overall status

- [x] Core MVP architecture is implemented.
- [x] React frontend and FastAPI backend are connected.
- [x] SQLite persistence is working for local development.
- [x] Authentication, assessments, conversations, chat, dashboard, safety handling, memory support, translation endpoint, voice features, and theme support exist.
- [ ] Production-ready multilingual chat pipeline is complete.
- [ ] The trained emergency classifier is available and active in the runtime environment.
- [ ] Full browser end-to-end testing is complete.
- [ ] Production deployment, migrations, monitoring, and operational hardening are complete.

### Approximate completion

| Area | Estimate | Notes |
|---|---:|---|
| Core MVP functionality | 80-85% | Main user flow is implemented and tested. |
| UI and user flow | 85-90% | Main screens, responsive styling, dashboard, and themes exist. |
| AI/ML functionality | 60-70% | Some models are optional or unavailable at runtime. |
| Production readiness | 55-65% | Deployment, migrations, monitoring, and E2E testing remain. |

These are engineering estimates, not formal project metrics.

---

## 1. System architecture

### Completed

- [x] React and Vite frontend exists.
- [x] FastAPI backend exists.
- [x] SQLAlchemy database layer exists.
- [x] SQLite local-development database is initialized at startup.
- [x] Frontend and backend communicate through authenticated REST endpoints.
- [x] Environment configuration is loaded from backend configuration files and process variables.
- [x] Local CORS support is configured for documented frontend ports.
- [x] AI/ML services are separated into chat, emotion, emergency, memory, and translation modules.

### To do

- [ ] Define a production deployment architecture.
- [ ] Separate development, test, and production configuration.
- [ ] Add production database migrations.
- [ ] Add service monitoring and structured operational metrics.
- [ ] Add deployment documentation and recovery procedures.

---

## 2. Authentication and user management

### Completed

- [x] User registration.
- [x] Duplicate-email validation.
- [x] Password hashing with bcrypt.
- [x] Login with JWT access tokens.
- [x] Protected frontend routes.
- [x] `GET /users/me`.
- [x] `PATCH /users/me`.
- [x] Preferred-language storage.
- [x] Logout.
- [x] Conversation ownership checks.
- [x] Password and input validation.

### To do

- [ ] Configure a stable private `SECRET_KEY` outside source control.
- [ ] Add refresh-token support if long-lived sessions are required.
- [ ] Add password reset.
- [ ] Add email verification if required.
- [ ] Add account deletion and user-data deletion.
- [ ] Add rate limiting for authentication endpoints.
- [ ] Add security review for production deployment.

---

## 3. Assessment module

### Completed

- [x] Assessment page exists.
- [x] Questions cover mood, stress, sleep, energy, and social support.
- [x] Required answers are validated in the frontend.
- [x] A simple score is calculated.
- [x] Answers and score are sent to `POST /assessments`.
- [x] Answers are stored as JSON text in `self_assessments`.
- [x] Assessment records can be retrieved through `GET /assessments`.
- [x] Latest assessment score appears on the dashboard.
- [x] Assessment history is returned by `/dashboard`.
- [x] Assessment progress is visualized in the frontend.
- [x] The UI states that the score is not a diagnosis.

### To do

- [ ] Review and document the scoring formula.
- [ ] Decide whether the score is only a wellbeing check-in or based on a validated instrument.
- [ ] Add daily, weekly, stress, sleep, or wellbeing check-in types if required.
- [ ] Add date labels and clearer time ranges to the chart.
- [ ] Add weekly/monthly filters.
- [ ] Add breakdowns for mood, stress, sleep, energy, and support.
- [ ] Add assessment export if required.
- [ ] Connect assessment trends to personalized, non-clinical suggestions.

---

## 4. Conversation and chat module

### Completed

- [x] Conversation creation.
- [x] Conversation listing.
- [x] Conversation ownership validation.
- [x] Message history retrieval.
- [x] User message persistence.
- [x] Assistant message persistence.
- [x] Recent conversation history is passed to Gemini.
- [x] Gemini receives the preferred language.
- [x] Gemini response mode is returned.
- [x] Gemini provider errors are sanitized before reaching users.
- [x] Provider errors are logged without exposing API keys or provider bodies.
- [x] Transient Gemini requests have retry handling.
- [x] The frontend shows loading and error states.
- [x] Normal chat does not silently substitute scripted replies when Gemini is unavailable.
- [x] New-chat creation is supported.
- [x] Optimistic user-message rendering is supported.

### To do

- [ ] Complete the IndicTrans2 integration inside the `/chat` flow.
- [ ] Decide whether Gemini should receive the original language or a translated internal representation.
- [ ] Translate assistant responses back to the user's selected language where required.
- [ ] Add a provider/model health check that validates an actual Gemini request.
- [ ] Add user-visible retry behavior for temporary 503 failures.
- [ ] Add request rate limiting and abuse protection.
- [ ] Add conversation deletion and export if required.
- [ ] Add automated end-to-end chat tests.

---

## 5. Gemini integration

### Completed

- [x] Google GenAI SDK integration exists.
- [x] API key is read from backend configuration.
- [x] API key is not sent to the frontend.
- [x] Configurable `GEMINI_MODEL` is supported.
- [x] The project currently uses `gemini-3.6-flash` as the configured/default model.
- [x] Conversation history is included in requests.
- [x] System instructions describe supportive, non-diagnostic behavior.
- [x] Preferred language is included in system instructions.
- [x] Authorization, quota, model, timeout, network, and provider-server errors are mapped.
- [x] Gemini tests cover request construction and provider error handling.

### To do

- [ ] Confirm that the configured Gemini model is enabled for the deployed API key.
- [ ] Confirm quota and billing configuration.
- [ ] Add a controlled integration test using a non-production test key.
- [ ] Add observability for latency, retries, and failure categories.
- [ ] Add a provider fallback strategy only if product requirements allow it.
- [ ] Document model changes and preview/stable model compatibility.

---

## 6. Translation and multilingual support

### Completed

- [x] Translation service exists.
- [x] IndicTrans2 is attempted first.
- [x] Google Translate fallback exists.
- [x] English, Hindi, Telugu, and Tamil are supported by the translation service.
- [x] Authenticated `POST /translate` exists.
- [x] Translation dependencies are documented separately.
- [x] Preferred language is stored on the user profile.
- [x] Gemini is instructed to respond in the selected language.

### To do

- [ ] Connect translation directly to the normal `/chat` request path.
- [ ] Define and implement the complete multilingual flow:
  - [ ] Receive speech or typed text in the user's language.
  - [ ] Preserve the original user message.
  - [ ] Translate internally when required.
  - [ ] Generate the response.
  - [ ] Translate the response back when required.
  - [ ] Display the response in the user's selected language.
- [ ] Add real IndicTrans2 tests for English-to-Telugu and Telugu-to-English.
- [ ] Verify IndicTrans2 model downloads and Windows dependencies.
- [ ] Make translation failures visible and actionable.
- [ ] Decide whether translation should be automatic or user-controlled.
- [ ] Add multilingual crisis phrase coverage.

### Current limitation

The standalone `/translate` endpoint uses IndicTrans2, but the current chat flow
does not automatically call it. Browser speech recognition also produces the
initial transcript, and translation cannot reliably correct a transcript that
was already misrecognized.

---

## 7. Speech input and output

### Completed

- [x] Browser speech recognition is supported where available.
- [x] English, Hindi, Telugu, and Tamil voice language codes are configured.
- [x] Telugu uses `te-IN`.
- [x] Continuous recognition is enabled.
- [x] Multiple final transcript segments are collected.
- [x] Microphone permission errors are shown.
- [x] Browser speech synthesis is supported where available.
- [x] Latest assistant response can be played aloud.
- [x] Voice input can be reviewed before sending.

### To do

- [ ] Test Chrome speech recognition for each supported language.
- [ ] Add a dedicated speech-to-text backend if browser accuracy is insufficient.
- [ ] Add recording duration and stop controls if needed.
- [ ] Add clearer interim-transcript display.
- [ ] Add pronunciation/noise guidance.
- [ ] Add automated browser tests for voice control states.
- [ ] Document browser compatibility and microphone requirements.

### Current limitation

Speech recognition is controlled by the browser. IndicTrans2 does not perform
speech recognition and cannot reliably repair an incorrect browser transcript.

---

## 8. Emotion detection

### Completed

- [x] Emotion detector module exists.
- [x] The configured model is `SamLowe/roberta-base-go_emotions`.
- [x] The top emotion is stored with the user message when available.
- [x] Emotion confidence is stored.
- [x] Emotion data is returned in message responses.
- [x] Recent mood history is returned by `/dashboard`.
- [x] The dashboard displays recent emotional signals.
- [x] The UI describes emotion estimates as non-clinical signals.

### To do

- [ ] Verify model availability in the actual runtime environment.
- [ ] Confirm model download and startup behavior on a clean installation.
- [ ] Add multilingual emotion detection or a translation strategy.
- [ ] Add confidence thresholds and uncertainty handling.
- [ ] Add tests for representative user messages.
- [ ] Avoid presenting model labels as definitive emotional truth.
- [ ] Add a user explanation and control for emotion analysis.

### Current limitation

If Transformers or the model is unavailable, the application continues without
emotion estimates.

---

## 9. Crisis detection and safety

### Completed

- [x] Explicit crisis phrase guardrail exists.
- [x] Emergency risk assessment is stored.
- [x] Crisis responses bypass Gemini.
- [x] Crisis response includes trusted-person and professional-support guidance.
- [x] India emergency number `112` is shown.
- [x] Tele-MANAS number `14416` is shown.
- [x] Frontend displays crisis-support notices.
- [x] Safety responses remain available when Gemini is unavailable.
- [x] Crisis detector tests cover guardrail behavior.

### To do

- [ ] Fix and deploy the trained emergency classifier.
- [ ] Place valid model and tokenizer files at the expected path.
- [ ] Resolve the current runtime `HFValidationError`.
- [ ] Evaluate classifier precision, recall, false positives, and false negatives.
- [ ] Add multilingual crisis phrases.
- [ ] Add controlled safety test cases.
- [ ] Review crisis wording with a qualified safety professional.
- [ ] Add region-aware emergency resources.
- [ ] Add a clear escalation and incident-review process.

### Current runtime status

The explicit phrase guardrail is active, but the logs show:

```text
Emergency classifier unavailable (HFValidationError)
```

Therefore the trained ML classifier is not currently active.

---

## 10. Semantic memory

### Completed

- [x] Sentence Transformer embedding support exists.
- [x] `all-MiniLM-L6-v2` is configured.
- [x] User messages can be embedded.
- [x] Embeddings are stored in `message_embeddings`.
- [x] Similar earlier reflections can be retrieved.
- [x] Relevant memories are passed to Gemini.
- [x] Memory retrieval is skipped for potential crisis messages.

### To do

- [ ] Verify the embedding model is available in the runtime environment.
- [ ] Add memory opt-in/opt-out.
- [ ] Add memory viewing and deletion controls.
- [ ] Add retention limits for sensitive reflections.
- [ ] Add privacy documentation and consent language.
- [ ] Replace Python full-scan similarity with FAISS or pgvector at scale.
- [ ] Add performance tests for larger histories.
- [ ] Add tests for memory relevance and user isolation.

### Current limitation

Embeddings are stored as JSON and compared in Python. This is suitable for a
prototype but is not an efficient large-scale vector-search implementation.

---

## 11. Dashboard and progress visualization

### Completed

- [x] Conversation count is displayed.
- [x] Message count is displayed.
- [x] Latest assessment score is displayed.
- [x] Latest risk status is displayed.
- [x] Assessment history is returned by the backend.
- [x] Assessment progress line chart exists.
- [x] Mood history is returned by the backend.
- [x] Recent emotion chips are displayed.
- [x] Latest mood signal is displayed.
- [x] Mood-based supportive actions are displayed.
- [x] Dashboard language avoids clinical claims.

### To do

- [ ] Add chart date labels.
- [ ] Add selectable time ranges.
- [ ] Add mood frequency visualization.
- [ ] Add separate stress, sleep, energy, and support trends.
- [ ] Add explanation of score direction and limits.
- [ ] Add export/download if required.
- [ ] Add empty-state examples that explain how to generate data.

---

## 12. UI and user experience

### Completed

- [x] Landing page.
- [x] Login and registration pages.
- [x] Protected application navigation.
- [x] Assessment page.
- [x] Chat page.
- [x] History page.
- [x] Dashboard page.
- [x] Profile page.
- [x] Language page.
- [x] Help and resource page.
- [x] Responsive layout.
- [x] Soothing light palette.
- [x] Persistent light/dark theme toggle.
- [x] Distinct light and dark color systems.
- [x] Supportive safe-space copy.
- [x] Reduced-motion support.
- [x] Keyboard focus styles.
- [x] Loading and error states for major flows.

### To do

- [ ] Add guided breathing interaction.
- [ ] Add optional grounding exercise cards.
- [ ] Add welcoming illustrations or calm visual motifs.
- [ ] Improve mobile navigation and mobile chat composition.
- [ ] Add font-size and contrast preferences.
- [ ] Perform keyboard-only accessibility testing.
- [ ] Perform screen-reader testing.
- [ ] Test dark mode on every route.
- [ ] Add visual regression checks.

---

## 13. Database and persistence

### Completed

- [x] SQLAlchemy models exist for users.
- [x] Conversations are persisted.
- [x] Messages are persisted.
- [x] Emotion results are persisted.
- [x] Risk assessments are persisted.
- [x] Self-assessments are persisted.
- [x] Message embeddings are persisted.
- [x] Local database initialization runs at application startup.
- [x] A small compatibility migration block exists for local schema changes.

### To do

- [ ] Replace `create_all()`-only evolution with Alembic migrations.
- [ ] Add migration rollback procedures.
- [ ] Add production database configuration.
- [ ] Add database backup and restore procedures.
- [ ] Add indexes for common user/conversation queries.
- [ ] Review data retention and deletion requirements.
- [ ] Add database integrity and concurrency tests.

---

## 14. API and backend quality

### Completed

- [x] API endpoints have validation through Pydantic schemas.
- [x] Protected endpoints use JWT authentication.
- [x] Ownership checks are applied to user data.
- [x] CORS is configured for local development.
- [x] Provider errors are sanitized.
- [x] Health endpoints exist.
- [x] API tests cover registration, login, CORS, assessments, chat, dashboard, and failures.

### To do

- [ ] Add OpenAPI examples for major requests.
- [ ] Add consistent error codes and error response schemas.
- [ ] Add request IDs and structured logs.
- [ ] Add rate limits.
- [ ] Add payload-size and abuse controls.
- [ ] Add API versioning if the public contract will evolve.
- [ ] Add integration tests for translation and model availability.

---

## 15. Testing and verification

### Completed

- [x] Backend test suite exists.
- [x] Chat-service tests cover Gemini request construction.
- [x] Chat-service tests cover provider errors.
- [x] API tests cover authentication and core contracts.
- [x] Detector tests cover unavailable-model behavior.
- [x] Frontend lint passes.
- [x] Frontend production build passes.

Previously verified:

```text
Backend: 34 tests passed
Frontend lint: passed
Frontend build: passed
```

### To do

- [ ] Add browser end-to-end tests.
- [ ] Add real translation integration tests.
- [ ] Add controlled Gemini integration tests.
- [ ] Add speech-control browser tests.
- [ ] Add crisis-flow end-to-end tests.
- [ ] Add classifier evaluation tests using a held-out dataset.
- [ ] Add memory relevance and performance tests.
- [ ] Add accessibility tests.
- [ ] Add load and latency tests.
- [ ] Add clean-install verification.

---

## 16. Production readiness

### Completed

- [x] Secrets are intended to remain outside committed source files.
- [x] Gemini keys are not exposed to the frontend.
- [x] Sanitized user-facing provider errors exist.
- [x] Local run instructions exist.

### To do

- [ ] Configure a stable production secret key.
- [ ] Use a production database.
- [ ] Configure HTTPS.
- [ ] Restrict CORS to deployed frontend origins.
- [ ] Add rate limiting and abuse monitoring.
- [ ] Add structured logs and alerting.
- [ ] Add backups and disaster recovery.
- [ ] Add privacy policy and informed-consent language.
- [ ] Review sensitive-data handling and retention.
- [ ] Review safety behavior with qualified domain experts.
- [ ] Establish deployment and rollback procedures.

---

## Recommended implementation order

### Priority 1: Functional completeness

- [ ] Integrate IndicTrans2 into the actual chat flow.
- [ ] Validate Telugu, Hindi, Tamil, and English chat end to end.
- [ ] Fix and activate the emergency classifier.
- [ ] Verify emotion and embedding models on a clean runtime.

### Priority 2: Safety and trust

- [ ] Review crisis language and escalation behavior.
- [ ] Add multilingual crisis coverage.
- [ ] Add privacy, consent, memory controls, and deletion.
- [ ] Improve uncertainty wording for emotion and risk results.

### Priority 3: User experience

- [ ] Add guided breathing and grounding exercises.
- [ ] Improve mobile and accessibility behavior.
- [ ] Add dashboard filters and clearer trend explanations.
- [ ] Add complete dark-mode visual review.

### Priority 4: Production readiness

- [ ] Add Alembic migrations.
- [ ] Configure production infrastructure.
- [ ] Add monitoring, backups, rate limits, and HTTPS.
- [ ] Add browser E2E, integration, performance, and accessibility tests.

---

## Verification checklist for a complete user journey

- [ ] Start backend successfully.
- [ ] Confirm `/health` reports Gemini key and SDK availability.
- [ ] Confirm emotion model status.
- [ ] Confirm emergency classifier status.
- [ ] Confirm embedding model status.
- [ ] Start frontend successfully.
- [ ] Register a new user.
- [ ] Log in.
- [ ] Complete an assessment.
- [ ] Confirm assessment appears on the dashboard.
- [ ] Create a conversation.
- [ ] Send a normal English message.
- [ ] Send a normal Telugu message.
- [ ] Verify the selected-language response.
- [ ] Verify emotion data when the model is available.
- [ ] Verify memory retrieval on a follow-up message.
- [ ] Verify crisis guardrail behavior in a controlled test.
- [ ] Verify dashboard mood and assessment updates.
- [ ] Verify light/dark theme persistence.
- [ ] Verify voice input and audio playback in a supported browser.
- [ ] Verify mobile layout.
- [ ] Verify keyboard navigation.

