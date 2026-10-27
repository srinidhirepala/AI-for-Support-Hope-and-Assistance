# ASHA AI

ASHA AI is a FastAPI and React application for supportive well-being check-ins and reflective conversations. ASHA is an AI assistant, not a therapist or diagnostic service.

## Run locally on Windows

Use two PowerShell terminals.

### 1. Start the backend

```powershell
Set-Location "C:\Users\Gnaneshwari\AI-for-Support-Hope-and-Assistance\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --env-file .env --host 127.0.0.1 --port 8000
```

The backend loads `backend\.env` when it exists. For local development, it defaults to SQLite at `backend\asha.db` and creates tables when the application starts. A `SECRET_KEY` is generated for that process if one is not configured; set a private, stable `SECRET_KEY` in `backend\.env` to keep login sessions valid across restarts.

To enable genuine Gemini chat, create an API key in [Google AI Studio](https://aistudio.google.com/apikey) and set it only in `backend\.env`:

```dotenv
GEMINI_API_KEY=your-private-key
```

Restart the backend after changing the key. The backend uses Google's `google-genai` SDK and the `gemini-3.8-flash` model by default; optionally set `GEMINI_MODEL` in `backend\.env` to another model enabled for your key. The key is never sent to the frontend. If the key is missing, invalid, or over quota, chat shows an actionable error and does not return a scripted substitute. Existing explicit crisis safety responses remain available.

The optional trained crisis classifier loads only from `models\emergency\distilroberta_emergency` at the repository root. That directory must contain the fine-tuned Hugging Face `config.json`, model weights (`model.safetensors` or `pytorch_model.bin`), and matching tokenizer assets (`tokenizer_config.json` plus `tokenizer.json` or the model's vocabulary/merges files). If those trained artifacts are absent, ASHA reports the classifier as unavailable and retains its separate explicit-language safety guardrail; the guardrail is not a substitute for a functioning classifier or professional help.

### 2. Start the frontend

```powershell
Set-Location "C:\Users\Gnaneshwari\AI-for-Support-Hope-and-Assistance\frontend"
npm install
npm run dev
```

Vite is configured to use `http://localhost:5176` and will fail instead of silently choosing another port if 5176 is occupied. The backend allows local development origins on ports 5173–5176; the standard frontend origin is `http://localhost:5176`. The frontend uses `http://127.0.0.1:8000` by default. To use a different backend URL, set `VITE_API_URL` in `frontend\.env.local` before starting Vite:

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

### Local URLs

- Frontend: <http://localhost:5176>
- Backend health: <http://127.0.0.1:8000/health>
- Interactive API docs: <http://127.0.0.1:8000/docs>

Register an account from the landing page, then log in with the same email and password. Passwords are hashed on the backend; the browser stores only the authentication token and public profile.

## Tests and builds

From `backend`:

```powershell
python -m pytest tests
```

From `frontend`:

```powershell
npm run lint
npm run build
```
