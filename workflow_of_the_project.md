# ASHA AI - Workflow of the Project

## 1. Project purpose

ASHA AI is a supportive well-being check-in and reflective conversation
application. It is not a therapist, doctor, diagnostic service, or replacement
for professional or emergency support.

The project has two applications:

- `backend`: FastAPI API, authentication, database access, Gemini integration,
  emotion detection, crisis detection, and semantic memory.
- `frontend`: React and Vite user interface for registration, chat,
  assessments, history, dashboard, profile, language, and help pages.

## 2. Startup workflow

### Backend

The backend starts from `backend/app/main.py`.

1. FastAPI creates the application.
2. The lifespan handler calls `initialize_database()`.
3. SQLAlchemy creates missing tables in the configured database.
4. The default database is `backend/asha.db`.
5. Environment values are loaded from `backend/.env`, the repository `.env`,
   and process environment variables.
6. The application allows local frontend origins on ports 5173 through 5176.
7. The emotion model, emergency model, and embedding model are attempted at
   module import time.
8. The API becomes available at `http://127.0.0.1:8000`.

Useful backend endpoints:

- `GET /`: basic application status.
- `GET /health`: configuration and optional-model status.
- `GET /healthz`: basic health response.
- `GET /docs`: FastAPI interactive API documentation.

### Frontend

The frontend starts from `frontend/src/main.jsx` and
`frontend/src/App.jsx`.

1. Vite serves the application on `http://localhost:5176`.
2. The API base URL defaults to `http://127.0.0.1:8000`.
3. `VITE_API_URL` can override the backend URL through
   `frontend/.env.local`.
4. Authentication state is read from browser `localStorage` under
   `asha-auth`.
5. Protected routes redirect unauthenticated users to the landing or login
   pages.

## 3. Registration and login workflow

1. The user submits the registration form.
2. The frontend calls `POST /auth/register`.
3. The backend validates the name, email, password length, and preferred
   language.
4. The password is hashed with bcrypt and only the hash is stored.
5. The frontend immediately calls `POST /auth/login`.
6. The backend creates a JWT containing the user's email.
7. The frontend stores the JWT and public user profile in local storage.
8. Future protected requests send the JWT in the `Authorization` header.

Authentication endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `GET /users/me`
- `PATCH /users/me`

The backend generates a temporary `SECRET_KEY` when one is not configured.
Therefore, tokens become invalid after a restart unless a stable private
`SECRET_KEY` is placed in `backend/.env`.

## 4. Assessment workflow

The registration flow sends the user to `/assessment`.

The frontend asks about:

- Overall mood
- Stress
- Sleep
- Energy
- Social support

When submitted:

1. The frontend calculates a simple score.
2. It calls `POST /assessments`.
3. The backend stores the answers as JSON text in `self_assessments`.
4. The user can continue to `/chat`.

The assessment is a self-check-in. It is not a clinical screening or
diagnosis.

## 5. Conversation workflow

When the chat page opens:

1. The frontend calls `GET /health`.
2. It checks whether Gemini is configured.
3. It checks whether the emergency classifier is available.
4. It loads the user's conversations with `GET /conversations`.
5. It loads messages for the selected conversation.
6. If no conversation exists, it creates one with `POST /conversations`.

Conversation endpoints:

- `GET /conversations`
- `POST /conversations`
- `GET /conversations/{conversation_id}/messages`

Every conversation is checked against the current user's ID before messages
are returned or created.

## 6. Complete message workflow

The main request is `POST /chat`.

### Step 1: Validate ownership

The backend verifies that the conversation exists and belongs to the logged-in
user. If not, it returns `404`.

### Step 2: Load recent context

The backend loads up to the previous 20 messages and converts them into
conversation history for Gemini.

### Step 3: Store the user message

The new user message is stored in the `messages` table.

### Step 4: Detect emotion

The optional Hugging Face emotion model attempts to estimate the top emotion.
The result is stored in `emotion_results`.

If the model is unavailable, the application continues without an emotion
result.

### Step 5: Detect crisis risk

The backend calls `detect_emergency()`.

It uses:

1. An explicit phrase guardrail for language such as "hurt myself",
   "kill myself", "want to die", and "suicidal".
2. An optional fine-tuned DistilRoBERTa classifier from
   `models/emergency/distilroberta_emergency`.

The output includes:

- Risk signal
- Confidence
- Detection source
- Classifier availability

### Step 6A: Crisis response

If the risk signal is `potential_crisis`:

1. Gemini is not called.
2. A predefined safety response is returned.
3. The frontend displays crisis resources.
4. The response directs the user toward trusted people, professionals, local
   emergency services, `112`, and Tele-MANAS `14416` in India.

### Step 6B: Normal AI response

If no crisis signal is found:

1. The backend retrieves up to five semantically similar earlier user
   messages.
2. The current message, recent history, estimated emotion, memories, and
   preferred language are passed to Gemini.
3. Gemini is instructed to respond warmly and avoid diagnosis, medication
   advice, certainty about emotions, or pretending to replace professional
   care.
4. The assistant response is stored in `messages`.

### Step 7: Store semantic memory

The user message is converted into an embedding using
`all-MiniLM-L6-v2`. The embedding is stored in `message_embeddings` as JSON.
Future messages are compared with these embeddings in Python to find relevant
earlier reflections.

### Step 8: Return the response

The backend returns:

- The stored user message
- Emotion result
- Emergency result
- Response mode
- Relevant memories
- Assistant message

The frontend replaces its optimistic message with the persisted user message
and displays the assistant response.

## 7. Gemini API-key workflow

The Gemini configuration is handled by
`backend/app/services/chat_service.py`.

The backend reads:

```dotenv
GEMINI_API_KEY=your-private-key
GEMINI_MODEL=gemini-3.6-flash
```

The key should be stored only in `backend/.env`. It must not be put in
frontend code, `frontend/.env.local`, Git, screenshots, logs, or chat
messages.

The backend loads the key when Python imports the chat service. Therefore:

1. Add or correct the key in `backend/.env`.
2. Stop the backend.
3. Restart Uvicorn.
4. Open `GET /health`.
5. Confirm that `gemini_api_key_configured` and `gemini_configured` are true.
6. Send a normal chat message.

The frontend does not receive the key. It only receives boolean health
information and sanitized error messages.

### API-key failure meanings

- `gemini_api_key_configured: false`: the backend did not find a non-empty
  key.
- `gemini_sdk_available: false`: `google-genai` is not installed or could not
  be imported.
- `gemini_configured: false`: the key or SDK is unavailable.
- HTTP 503 with an authorization message: the key is invalid, disabled, or
  does not have Gemini access.
- HTTP 503 with a quota message: the project quota or rate limit was reached.
- HTTP 502 saying the model is unavailable: `GEMINI_MODEL` is not available
  for the configured project/key.
- HTTP 504: the provider or network timed out.
- A browser "could not reach ASHA" message: the backend URL, backend process,
  port, or CORS configuration is wrong rather than necessarily an API-key
  problem.

The frontend deliberately does not substitute a scripted normal response when
Gemini is unavailable. Explicit crisis responses remain available because
they do not require Gemini.

## 8. What is working in the codebase

Based on the implementation and existing tests, these areas are implemented:

- FastAPI application startup and health endpoints.
- SQLite database initialization.
- User registration and duplicate-email handling.
- Password hashing and login.
- JWT-protected routes.
- User profile and language updates.
- Conversation creation and ownership checks.
- Message history retrieval.
- Assessment creation and retrieval.
- Dashboard summary queries.
- CORS support for the documented local frontend ports.
- Explicit crisis-language safety guardrail.
- Safe crisis response path that bypasses Gemini.
- Gemini request construction with conversation history and language.
- Sanitized provider error messages and logging.
- Frontend routing and protected pages.
- Frontend chat, history, assessment, dashboard, profile, language, and help
  screens.
- Browser speech recognition and speech synthesis where the browser supports
  them.

## 9. Optional or environment-dependent areas

These features may not work until dependencies and model files are available:

- Emotion detection requires the Transformers package and model download.
- The emergency ML classifier requires the trained model directory and its
  tokenizer/model files.
- Semantic memory requires Sentence Transformers and its model download.
- Normal AI chat requires a valid Gemini API key, installed SDK, enabled
  model, quota, and backend network access.
- Voice input depends on browser speech-recognition support and microphone
  permissions.
- Text-to-speech depends on browser speech-synthesis support.

The application is designed to continue running when optional ML models are
unavailable, but this reduces functionality and should be shown to the user.

## 10. Known issues and likely problems

### Highest-probability current issue: Gemini configuration

The repository does not contain a committed `.env` file, which is correct for
secret protection. If `backend/.env` does not exist locally, or if the key is
blank/expired/invalid, normal chat will fail.

The expected file is:

```text
backend/.env
```

The expected setting is:

```dotenv
GEMINI_API_KEY=the-key-value
```

Do not include quotes unless they are intentionally handled by the dotenv
parser, do not add spaces before the key name, and restart the backend after
editing the file.

### Model-name compatibility

The configured default is `gemini-3.6-flash`. If the Google project does not
make that model available, the API returns a model-unavailable error. Set
`GEMINI_MODEL` to a model actually enabled for the key.

### Standalone Gemini test mismatch

The root `test_gemini.py` uses `client.interactions.create()`, while the main
application uses `client.models.generate_content()`. A failure in that
standalone script is not necessarily identical to a failure in the
application path. The most reliable application check is the backend
`/health` response followed by a real `POST /chat`.

### Optional model availability

If the crisis model directory is missing, automated crisis classification is
unavailable. The explicit phrase guardrail still operates, but it cannot
identify every possible crisis expression.

If the emotion model is unavailable, the chat still works but no emotion
estimate is attached.

### Local database and migrations

The project uses `create_all()` and a small hand-written migration block.
This is suitable for local development, but it is not a complete production
migration strategy. Existing SQLite data should be backed up before schema
changes.

### Secret-key persistence

Without a stable `SECRET_KEY`, all login tokens are invalidated whenever the
backend restarts.

### Runtime cost

Several ML models are loaded at import time. Initial startup can be slow and
may require model downloads. The embedding implementation also scans and
compares stored embeddings in Python, so it may become slow as a user's
history grows.

## 11. Recommended verification order

1. Start the backend.
2. Open `http://127.0.0.1:8000/health`.
3. Confirm:
   - `status` is `healthy`.
   - `gemini_api_key_configured` is true.
   - `gemini_sdk_available` is true.
   - `gemini_configured` is true.
4. If key configuration is false, check only `backend/.env`; never place the
   key in the frontend.
5. If configuration is true but chat fails, inspect the exact sanitized error:
   authorization, quota, model, timeout, or network.
6. Start the frontend at `http://localhost:5176`.
7. Register, log in, create a conversation, and send a normal message.
8. Send a test message containing explicit crisis language only in a controlled
   test environment; verify that the safety response is returned without a
   Gemini call.
9. Run backend tests from `backend`:

   ```powershell
   python -m pytest tests
   ```

10. Run frontend checks from `frontend`:

   ```powershell
   npm run lint
   npm run build
   ```

## 12. Overall status summary

The core application structure is present and wired end to end. The likely
blocker for ordinary chat is Gemini configuration or provider access, not the
React-to-FastAPI request structure. The application intentionally refuses to
fake normal AI responses when Gemini is unavailable. Authentication,
conversation storage, assessments, dashboard queries, frontend navigation,
and explicit crisis safety handling are implemented separately and can work
even when Gemini is not configured.
