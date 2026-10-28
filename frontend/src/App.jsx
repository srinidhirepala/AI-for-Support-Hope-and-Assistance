import { useEffect, useRef, useState } from 'react'
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useSearchParams,
  useLocation,
  useNavigate,
} from 'react-router-dom'
import {
  BarChart3,
  BookOpenText,
  BrainCircuit,
  ChevronLeft,
  ChevronRight,
  HeartHandshake,
  Languages,
  LogOut,
  MessageSquareText,
  Mic,
  NotebookPen,
  ShieldAlert,
  Sparkles,
  Moon,
  UserRound,
  Volume2,
  Sun,
} from 'lucide-react'
import './App.css'

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')
const STORAGE_KEY = 'asha-auth'
const THEME_KEY = 'asha-theme'

const starterPrompts = [
  'I\'ve been feeling stressed lately.',
  'Can you help me organize my thoughts?',
  'I want to talk about how my day went.',
  'Can you guide me through a short breathing exercise?',
  'I\'d like to reflect on my mood today.',
]

const assessmentQuestions = [
  {
    key: 'mood',
    label: 'How are you feeling overall today?',
    options: ['Very low', 'Low', 'Okay', 'Good', 'Great'],
  },
  {
    key: 'stress',
    label: 'How stressed have you felt in the past week?',
    options: ['Not at all', 'A little', 'Moderately', 'Quite a bit', 'Very high'],
  },
  {
    key: 'sleep',
    label: 'How well did you sleep recently?',
    options: ['Very poorly', 'Poorly', 'Fairly', 'Well', 'Very well'],
  },
  {
    key: 'energy',
    label: 'How would you rate your energy lately?',
    options: ['Very low', 'Low', 'Average', 'High', 'Very high'],
  },
  {
    key: 'support',
    label: 'Do you feel supported by the people around you?',
    options: ['Not at all', 'A little', 'Somewhat', 'Mostly', 'Completely'],
  },
]

const languageOptions = ['English', 'Hindi', 'Telugu', 'Tamil']
const voiceLanguages = {
  English: 'en-IN',
  Hindi: 'hi-IN',
  Telugu: 'te-IN',
  Tamil: 'ta-IN',
}
const crisisResources = [
  { label: 'Emergency', value: '112', description: 'For immediate assistance in India' },
  { label: 'Tele-MANAS', value: '14416', description: 'Mental health support line' },
  { label: 'Local emergency services', value: 'Verify locally', description: 'Check current availability in your area' },
]

function apiRequest(path, options = {}, token) {
  const headers = { Accept: 'application/json', ...(options.headers || {}) }
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 40_000)
  if (options.body) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    signal: options.signal || controller.signal,
  }).catch((error) => {
    if (error.name === 'AbortError') {
      throw new Error('The request timed out. Please try again.')
    }
    throw new Error(
      `Could not reach ASHA at ${API_BASE_URL}. Check that the backend is running, VITE_API_URL is correct, and the backend allows this frontend origin (${window.location.origin}) in its CORS settings.`,
    )
  }).then(async (response) => {
    const contentType = response.headers.get('content-type') || ''
    const payload = contentType.includes('application/json') ? await response.json() : null

    if (!response.ok) {
      const detail = payload?.detail || payload?.error
      const message = Array.isArray(detail)
        ? detail.map((issue) => issue.msg).join(' ')
        : detail || 'The request could not be completed.'
      throw new Error(message)
    }

    return payload
  }).finally(() => window.clearTimeout(timeoutId))
}

function readStoredAuth() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const saved = raw ? JSON.parse(raw) : null
    return saved && typeof saved.token === 'string' && saved.user
      ? saved
      : { token: '', user: null }
  } catch {
    return { token: '', user: null }
  }
}

function App() {
  const [auth, setAuth] = useState(readStoredAuth)
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem(THEME_KEY) || 'light'
    } catch {
      return 'light'
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
    } catch {
      // Authentication remains available for this page session if storage is blocked.
    }
  }, [auth])

  return (
    <BrowserRouter>
      <AppLayout auth={auth} setAuth={setAuth} theme={theme} setTheme={setTheme} />
    </BrowserRouter>
  )
}

function AppLayout({ auth, setAuth, theme, setTheme }) {
  const location = useLocation()
  const currentPath = location.pathname
  const isLoggedIn = Boolean(auth.token && auth.user)

  return (
    <div className={`app-shell ${theme === 'dark' ? 'theme-dark' : 'theme-light'}`}>
      <button
        className="theme-toggle"
        type="button"
        onClick={() => {
          const nextTheme = theme === 'dark' ? 'light' : 'dark'
          setTheme(nextTheme)
          try {
            localStorage.setItem(THEME_KEY, nextTheme)
          } catch {
            // The theme remains available for this page session if storage is blocked.
          }
        }}
        aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      >
        {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        <span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
      </button>
      <aside className={`sidebar ${isLoggedIn ? 'visible' : 'hidden'}`}>
        <div className="brand-wrap">
          <div className="brand-mark">A</div>
          <div>
            <div className="brand-name">ASHA AI</div>
            <div className="brand-tag">A safe space to pause, reflect, and feel heard.</div>
          </div>
        </div>

        {isLoggedIn && (
          <>
            <nav className="sidebar-nav" aria-label="Main navigation">
              <NavLink to="/chat" icon={<MessageSquareText size={18} />} active={currentPath === '/chat'}>
                Chat
              </NavLink>
              <NavLink to="/dashboard" icon={<BarChart3 size={18} />} active={currentPath === '/dashboard'}>
                Dashboard
              </NavLink>
              <NavLink to="/history" icon={<BookOpenText size={18} />} active={currentPath === '/history'}>
                History
              </NavLink>
              <NavLink to="/assessment" icon={<NotebookPen size={18} />} active={currentPath === '/assessment'}>
                Assessment
              </NavLink>
              <NavLink to="/profile" icon={<UserRound size={18} />} active={currentPath === '/profile'}>
                Profile
              </NavLink>
              <NavLink to="/language" icon={<Languages size={18} />} active={currentPath === '/language'}>
                Language
              </NavLink>
              <NavLink to="/help" icon={<ShieldAlert size={18} />} active={currentPath === '/help'}>
                Help
              </NavLink>
            </nav>

            <div className="profile-card">
              <div className="avatar">{auth.user?.name?.[0]?.toUpperCase() || 'A'}</div>
              <div>
                <div className="profile-name">{auth.user?.name || 'ASHA user'}</div>
                <div className="profile-meta">{auth.user?.preferred_language || 'English'}</div>
              </div>
              <button
                className="ghost-button danger"
                onClick={() => setAuth({ token: '', user: null })}
                type="button"
              >
                <LogOut size={16} /> Logout
              </button>
            </div>
          </>
        )}
      </aside>

      <main className="main-panel">
        <Routes>
          <Route path="/" element={<LandingPage isLoggedIn={isLoggedIn} />} />
          <Route path="/login" element={<AuthPage mode="login" auth={auth} setAuth={setAuth} />} />
          <Route path="/register" element={<AuthPage mode="register" auth={auth} setAuth={setAuth} />} />
          <Route path="/assessment" element={<ProtectedRoute isLoggedIn={isLoggedIn}><AssessmentPage {...auth} /></ProtectedRoute>} />
          <Route path="/chat" element={<ProtectedRoute isLoggedIn={isLoggedIn}><ChatPage {...auth} /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute isLoggedIn={isLoggedIn}><HistoryPage {...auth} /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute isLoggedIn={isLoggedIn}><DashboardPage {...auth} /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute isLoggedIn={isLoggedIn}><ProfilePage {...auth} setAuth={setAuth} /></ProtectedRoute>} />
          <Route path="/language" element={<ProtectedRoute isLoggedIn={isLoggedIn}><LanguagePage {...auth} setAuth={setAuth} /></ProtectedRoute>} />
          <Route path="/help" element={<ProtectedRoute isLoggedIn={isLoggedIn}><HelpPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to={isLoggedIn ? '/chat' : '/'} replace />} />
        </Routes>
      </main>
    </div>
  )
}

function ProtectedRoute({ isLoggedIn, children }) {
  if (!isLoggedIn) return <Navigate to="/login" replace />
  return children
}

function NavLink({ to, icon, children, active }) {
  return (
    <Link to={to} className={`nav-link ${active ? 'active' : ''}`}>
      {icon}
      <span>{children}</span>
    </Link>
  )
}

function LandingPage({ isLoggedIn }) {
  const navigate = useNavigate()

  return (
    <div className="page landing-page">
      <div className="hero-panel">
        <div className="eyebrow">ASHA AI — Support, Hope and Assistance</div>
        <h1>A safe space to pause, reflect, and feel heard.</h1>
        <p>
          A supportive companion for everyday emotional check-ins, reflective conversations,
          and gentle guidance designed to help you slow down and reconnect with yourself.
        </p>
        <div className="hero-actions">
          {isLoggedIn ? (
            <button type="button" className="primary-button" onClick={() => navigate('/chat')}>
              Open ASHA
            </button>
          ) : (
            <>
              <button type="button" className="primary-button" onClick={() => navigate('/register')}>
                Create account
              </button>
              <button type="button" className="secondary-button" onClick={() => navigate('/login')}>
                Log in
              </button>
            </>
          )}
        </div>

        <div className="feature-grid">
          <FeatureCard icon={<HeartHandshake size={20} />} title="Warm support" text="Thoughtful, calm, non-judgmental conversation for everyday feelings." />
          <FeatureCard icon={<BrainCircuit size={20} />} title="Reflection" text="Daily self-check-ins and guided prompts to build emotional awareness." />
          <FeatureCard icon={<ShieldAlert size={20} />} title="Safety information" text="Emergency resources are easy to reach, and explicit safety checks can trigger the backend response." />
        </div>
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, text }) {
  return (
    <div className="feature-card">
      <div className="feature-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  )
}

function AuthPage({ mode, setAuth }) {
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', preferred_language: 'English' })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const isRegister = mode === 'register'

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!form.email || !form.password || (isRegister && !form.name)) {
      setError('Please complete all required fields.')
      return
    }

    setLoading(true)
    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login'
      const payload = isRegister
        ? form
        : { email: form.email, password: form.password }

      const response = await apiRequest(endpoint, { method: 'POST', body: JSON.stringify(payload) })

      if (isRegister) {
        const loginResponse = await apiRequest('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email: form.email, password: form.password }),
        })

        setAuth({ token: loginResponse.access_token, user: loginResponse.user })
        navigate('/assessment')
        return
      }

      setAuth({ token: response.access_token, user: response.user })
      navigate('/chat')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to complete this request.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page auth-page">
      <div className="panel auth-panel">
        <div className="panel-header">
          <div className="eyebrow">Welcome to ASHA</div>
          <h2>{isRegister ? 'Create your account' : 'Welcome back'}</h2>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {isRegister && (
            <label className="field">
              <span>Full name</span>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Your name"
              />
            </label>
          )}

          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="you@example.com"
            />
          </label>

          <label className="field">
            <span>Password</span>
            <div className="password-wrap">
              <input
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="Your password"
              />
              <button type="button" className="tiny-button" onClick={() => setShowPassword((prev) => !prev)}>
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </label>

          {isRegister && (
            <label className="field">
              <span>Preferred language</span>
              <select
                value={form.preferred_language}
                onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}
              >
                {languageOptions.map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            </label>
          )}

          {error && <div className="error-box">{error}</div>}

          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? 'Please wait...' : isRegister ? 'Create account' : 'Log in'}
          </button>
        </form>

        <p className="switch-link">
          {isRegister ? 'Already have an account?' : 'Need an account?'}{' '}
          <Link to={isRegister ? '/login' : '/register'}>{isRegister ? 'Log in' : 'Create one'}</Link>
        </p>
      </div>
    </div>
  )
}

function AssessmentPage({ token }) {
  const navigate = useNavigate()
  const [index, setIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  const question = assessmentQuestions[index]
  const progress = ((index + 1) / assessmentQuestions.length) * 100

  function updateAnswer(value) {
    setAnswers((prev) => ({ ...prev, [question.key]: value }))
  }

  function next() {
    if (!answers[question.key]) {
      setError('Please select an option to continue.')
      return
    }
    setError('')
    if (index < assessmentQuestions.length - 1) setIndex((value) => value + 1)
  }

  function previous() {
    setError('')
    if (index > 0) setIndex((value) => value - 1)
  }

  async function submitAssessment() {
    if (!answers[question.key]) {
      setError('Please answer the current question before continuing.')
      return
    }

    const score = Object.values(answers).reduce((sum, value) => sum + (['Very low', 'Low', 'Not at all', 'Poorly', 'Very poorly'].includes(value) ? 1 : 0), 0)
    try {
      await apiRequest('/assessments', {
        method: 'POST',
        body: JSON.stringify({
          assessment_type: 'initial',
          score,
          answers,
        }),
      }, token)
      setSubmitted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save your check-in.')
    }
  }

  if (submitted) {
    return (
      <div className="page assessment-page">
        <div className="panel confirmation-panel">
          <div className="eyebrow">Assessment complete</div>
          <h2>Your check-in summary</h2>
          <ul className="summary-list">
            {assessmentQuestions.map((item) => (
              <li key={item.key}>
                <strong>{item.label}</strong>
                <span>{answers[item.key]}</span>
              </li>
            ))}
          </ul>
          <div className="panel-actions">
            <button className="secondary-button" type="button" onClick={() => navigate('/chat')}>Go to chat</button>
            <button className="primary-button" type="button" onClick={() => setSubmitted(false)}>Review responses</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page assessment-page">
      <div className="panel">
        <div className="panel-header split-header">
          <div>
            <div className="eyebrow">Initial well-being check-in</div>
            <h2>Gentle self-assessment</h2>
          </div>
          <div className="badge">{index + 1}/{assessmentQuestions.length}</div>
        </div>

        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>

        <div className="question-panel">
          <h3>{question.label}</h3>
          <div className="options-grid">
            {question.options.map((option) => (
              <button
                key={option}
                type="button"
                className={`choice-button ${answers[question.key] === option ? 'selected' : ''}`}
                onClick={() => updateAnswer(option)}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        {error && <div className="error-box">{error}</div>}

        <div className="panel-actions">
          <button type="button" className="secondary-button" onClick={previous} disabled={index === 0}>
            <ChevronLeft size={16} /> Previous
          </button>
          {index === assessmentQuestions.length - 1 ? (
            <button type="button" className="primary-button" onClick={submitAssessment}>Finish</button>
          ) : (
            <button type="button" className="primary-button" onClick={next}>Next <ChevronRight size={16} /></button>
          )}
        </div>
      </div>
    </div>
  )
}

function ChatPage({ user, token }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const chatWindowRef = useRef(null)
  const recognitionRef = useRef(null)
  const sendingRef = useRef(false)
  const [conversation, setConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [composer, setComposer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [crisisResourcesVisible, setCrisisResourcesVisible] = useState(false)
  const [crisisClassifierUnavailable, setCrisisClassifierUnavailable] = useState(false)
  const [aiUnavailable, setAiUnavailable] = useState(false)
  const [geminiApiKeyConfigured, setGeminiApiKeyConfigured] = useState(false)
  const [geminiSdkAvailable, setGeminiSdkAvailable] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState('')
  const [speaking, setSpeaking] = useState(false)
  const [listening, setListening] = useState(false)

  useEffect(() => {
    let ignore = false

    async function init() {
      try {
        const health = await apiRequest('/health', { method: 'GET' })
        if (!ignore) {
          setCrisisClassifierUnavailable(
            health?.emergency_classifier_available === false,
          )
          setAiUnavailable(health?.gemini_configured === false)
          setGeminiApiKeyConfigured(health?.gemini_api_key_configured === true)
          setGeminiSdkAvailable(health?.gemini_sdk_available === true)
        }

        const list = await apiRequest('/conversations', { method: 'GET' }, token)
        const requestedId = Number(searchParams.get('conversation'))
        const selectedConversation = list.find((item) => item.id === requestedId)
        const latest = selectedConversation || list[0]

        if (latest) {
          const messageList = await apiRequest(`/conversations/${latest.id}/messages`, { method: 'GET' }, token)
          if (!ignore) {
            setConversation(latest)
            setMessages(messageList)
            setCrisisResourcesVisible(
              messageList.some((message) => message.risk_signal === 'potential_crisis'),
            )
          }
          return
        }

        if (list.length === 0) {
          const newConversation = await apiRequest('/conversations', {
            method: 'POST',
            body: JSON.stringify({ title: 'New conversation' }),
          }, token)
          if (!ignore) {
            setConversation(newConversation)
            setSearchParams({ conversation: String(newConversation.id) }, { replace: true })
          }
          return
        }
      } catch (err) {
        if (!ignore) setError(err instanceof Error ? err.message : 'Unable to load conversations.')
      }
    }

    init()
    return () => {
      ignore = true
    }
  }, [token, searchParams, setSearchParams])

  useEffect(() => () => {
    recognitionRef.current?.stop()
    window.speechSynthesis?.cancel()
  }, [])

  useEffect(() => {
    const chatWindow = chatWindowRef.current
    if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight
  }, [messages, loading])

  async function submitMessage() {
    const trimmed = composer.trim()
    if (!trimmed || !conversation || loading || sendingRef.current) return

    sendingRef.current = true
    setLoading(true)
    setError('')
    const userContent = trimmed
    setComposer('')
    const optimisticMessageId = Date.now()
    setMessages((prev) => [
      ...prev,
      {
        id: optimisticMessageId,
        conversation_id: conversation.id,
        sender: 'user',
        content: userContent,
        timestamp: new Date().toISOString(),
      },
    ])

    try {
      const response = await apiRequest('/chat', {
        method: 'POST',
        body: JSON.stringify({
          conversation_id: conversation.id,
          sender: 'user',
          content: userContent,
        }),
      }, token)

      setCrisisResourcesVisible(response.emergency?.risk_signal === 'potential_crisis')
      setCrisisClassifierUnavailable(response.emergency?.classifier_available === false)
      setAiUnavailable(false)
      const responseTimestamp = new Date().toISOString()
      setMessages((previous) => [
        ...previous.filter((message) => message.id !== optimisticMessageId),
        {
          ...response.user_message,
          timestamp: responseTimestamp,
          emotion: response.emotion
            ? { label: response.emotion, confidence: response.emotion_confidence }
            : null,
          risk_signal: response.emergency?.risk_signal,
        },
        { ...response.assistant_message, timestamp: responseTimestamp },
      ])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to send your message.'
      setError(message)
      setMessages((previous) =>
        previous.filter((item) => item.id !== optimisticMessageId),
      )
      setComposer((previous) => previous || userContent)
      if (/Gemini|AI chat/i.test(message)) setAiUnavailable(true)
    } finally {
      sendingRef.current = false
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submitMessage()
    }
  }

  function startVoiceInput() {
    if (listening) {
      recognitionRef.current?.stop()
      setVoiceStatus('Voice input stopped.')
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setVoiceStatus('Voice dictation is not supported in this browser. You can type your message instead.')
      return
    }

    const recognition = new SpeechRecognition()
    const language = user?.preferred_language || 'English'
    const voiceLanguage = voiceLanguages[language] || voiceLanguages.English
    recognition.lang = voiceLanguage
    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 3
    recognition.onstart = () => {
      setListening(true)
      setVoiceStatus('Listening. Speak when you are ready.')
    }
    recognition.onresult = (event) => {
      const finalTranscript = Array.from(event.results)
        .slice(event.resultIndex)
        .filter((result) => result.isFinal)
        .map((result) => result[0]?.transcript?.trim())
        .filter(Boolean)
        .join(' ')

      if (finalTranscript) {
        setComposer((previous) => `${previous}${previous ? ' ' : ''}${finalTranscript}`)
        setVoiceStatus('Voice note added to your message. Review it before sending.')
      }
    }
    recognition.onerror = (event) => {
      setListening(false)
      setVoiceStatus(
        event.error === 'not-allowed'
          ? 'Microphone permission was denied. You can type your message instead.'
          : `Voice input could not start (${event.error}). Please try typing instead.`,
      )
    }
    recognition.onend = () => setListening(false)
    recognitionRef.current = recognition
    recognition.start()
  }

  function toggleSpeech() {
    if (!('speechSynthesis' in window)) {
      setVoiceStatus('Audio playback is not supported in this browser.')
      return
    }

    if (speaking) {
      window.speechSynthesis.cancel()
      setSpeaking(false)
      return
    }

    const latestAssistantMessage = [...messages].reverse().find((message) => message.sender === 'assistant')
    if (!latestAssistantMessage) {
      setVoiceStatus('There is no ASHA response to play yet.')
      return
    }

    const language = user?.preferred_language || 'English'
    const voiceLanguage = voiceLanguages[language] || voiceLanguages.English
    const utterance = new SpeechSynthesisUtterance(latestAssistantMessage.content)
    utterance.lang = voiceLanguage
    const matchingVoice = window.speechSynthesis
      .getVoices()
      .find((voice) => voice.lang.toLowerCase().startsWith(voiceLanguage.slice(0, 2)))
    if (matchingVoice) utterance.voice = matchingVoice
    utterance.onstart = () => setSpeaking(true)
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => {
      setSpeaking(false)
      setVoiceStatus('Audio playback failed. You can read the response above.')
    }
    window.speechSynthesis.speak(utterance)
    setVoiceStatus('Playing the latest ASHA response.')
  }

  async function startNewChat() {
    try {
      const newConversation = await apiRequest('/conversations', {
        method: 'POST',
        body: JSON.stringify({ title: 'New conversation' }),
      }, token)
      setConversation(newConversation)
      setMessages([])
      setCrisisResourcesVisible(false)
      setCrisisClassifierUnavailable(false)
      setSearchParams({ conversation: String(newConversation.id) }, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to start a new conversation.')
    }
  }

  return (
    <div className="page chat-page">
      <div className="chat-header">
        <div>
          <div className="eyebrow">ASHA AI</div>
          <h2>A space to talk things through</h2>
          <p className="chat-subtitle">
            Share at your own pace. ASHA will listen and respond in {user?.preferred_language || 'English'}.
            Voice input and playback use your selected language when your browser supports it.
          </p>
          <div className="safe-space-note">
            <HeartHandshake size={16} />
            <span>You can start with one sentence. There is no pressure to explain everything at once.</span>
          </div>
        </div>
        <button className="secondary-button" type="button" onClick={startNewChat}>New chat</button>
      </div>

      <div className="suggestion-row">
        {starterPrompts.map((prompt) => (
          <button key={prompt} type="button" className="suggestion-pill" onClick={() => setComposer(prompt)}>
            {prompt}
          </button>
        ))}
      </div>

      <div
        className="chat-window"
        ref={chatWindowRef}
        role="log"
        aria-label="Conversation messages"
        aria-live="polite"
        aria-busy={loading}
      >
        {messages.length === 0 && !loading && (
          <div className="empty-state">
            <Sparkles size={28} />
            <h3>Start a gentle conversation</h3>
            <p>Share what feels comfortable. ASHA is here to listen and help you reflect, not diagnose.</p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`message-row ${message.sender === 'user' ? 'user' : 'assistant'}`}>
            <div className="message-bubble">
              <p>{message.content}</p>
              <span>{message.timestamp ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
              {message.emotion && (
                <small className="emotion-insight">
                  Estimated emotion: {message.emotion.label}
                  {typeof message.emotion.confidence === 'number'
                    ? ` · ${Math.round(message.emotion.confidence * 100)}% confidence`
                    : ''}
                </small>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-row assistant">
            <div className="message-bubble typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}

        {error && <div className="error-box" role="alert">{error}</div>}
        {crisisResourcesVisible && (
          <div className="notice-box" role="alert">
            The support response above is from ASHA's safety service. If you may be in immediate danger,
            contact local emergency services or someone you trust. In India, call 112 for emergency help
            or 14416 for Tele-MANAS; verify current availability.
          </div>
        )}
        {aiUnavailable && (
          <div className="notice-box chat-ai-unavailable" role="status">
            Gemini AI responses are unavailable, and ASHA will not substitute scripted replies.
            {!geminiApiKeyConfigured && ' Add GEMINI_API_KEY to backend\\.env.'}
            {!geminiSdkAvailable && ' Install the backend requirements to enable the Gemini SDK.'}
            {geminiApiKeyConfigured && geminiSdkAvailable && ' Check the key, Gemini quota, and backend network connection.'}
            {' '}Restart the backend after changing its configuration.
          </div>
        )}
        {!crisisResourcesVisible && crisisClassifierUnavailable && (
          <div className="notice-box" role="status">
            ASHA's automated crisis-classification model is not configured in this environment.
            Explicit safety checks remain active, but they cannot identify every crisis. If you feel
            unsafe, contact a trusted person or local emergency services; in India, call 112 or
            Tele-MANAS at 14416 and verify current availability.
          </div>
        )}
      </div>

      <div className="composer-box">
        <textarea
          value={composer}
          onChange={(e) => setComposer(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={3}
          aria-label="Write a message to ASHA"
          placeholder="Share what is on your mind..."
        />
        <div className="composer-actions">
          <button
            type="button"
            className="icon-button"
            aria-label={listening ? 'Stop voice input' : 'Voice input'}
            aria-pressed={listening}
            onClick={startVoiceInput}
          >
            <Mic size={18} />
          </button>
          <button type="button" className="icon-button" aria-label={speaking ? 'Stop audio playback' : 'Play latest response'} onClick={toggleSpeech}>
            <Volume2 size={18} />
          </button>
          <button type="button" className="primary-button" onClick={submitMessage} disabled={loading || !composer.trim()}>
            Send
          </button>
        </div>
        {voiceStatus && <div className="composer-status" role="status">{voiceStatus}</div>}
      </div>
    </div>
  )
}

function HistoryPage({ token }) {
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    apiRequest('/conversations', { method: 'GET' }, token)
      .then(setConversations)
      .catch((err) => setError(err instanceof Error ? err.message : 'Unable to load conversation history.'))
      .finally(() => setLoading(false))
  }, [token])

  return (
    <div className="page history-page">
      <div className="panel">
        <div className="panel-header split-header">
          <div>
            <div className="eyebrow">Conversation history</div>
            <h2>Recent reflections</h2>
          </div>
        </div>

        {loading ? (
          <div className="empty-state compact" role="status">Loading your conversations…</div>
        ) : error ? (
          <div className="error-box" role="alert">{error}</div>
        ) : conversations.length === 0 ? (
          <div className="empty-state compact">
            <BookOpenText size={24} />
            <p>No conversations yet. Start your first check-in in chat.</p>
          </div>
        ) : (
          <div className="history-list">
            {conversations.map((conversation) => (
              <div key={conversation.id} className="history-item">
                <div>
                  <h3>{conversation.title || `Conversation ${conversation.id}`}</h3>
                  <p>{conversation.started_at ? new Date(conversation.started_at).toLocaleString() : 'Started recently'}</p>
                </div>
                <Link to={`/chat?conversation=${conversation.id}`} className="secondary-button small-button">Open</Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function DashboardPage({ token }) {
  const [dashboard, setDashboard] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    apiRequest('/dashboard', { method: 'GET' }, token)
      .then(setDashboard)
      .catch((err) => setError(err instanceof Error ? err.message : 'Unable to load dashboard data.'))
  }, [token])

  if (error) return <div className="page"><div className="error-box" role="alert">{error}</div></div>
  if (!dashboard) return <div className="page" role="status">Loading…</div>
  const assessmentHistory = dashboard.assessment_history || []
  const moodHistory = dashboard.mood_history || []
  const latestMood = moodHistory[moodHistory.length - 1]?.emotion

  return (
    <div className="page dashboard-page">
      <div className="stats-grid">
        <StatCard label="Conversations" value={dashboard.total_conversations} />
        <StatCard label="Messages" value={dashboard.total_messages} />
        <StatCard label="Latest assessment" value={dashboard.latest_assessment ?? '—'} />
        <StatCard label="Risk status" value={dashboard.latest_risk_level || 'No signal'} />
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-header">
            <div className="eyebrow">Assessment progress</div>
            <h3>Your scores over time</h3>
          </div>
          {assessmentHistory.length ? (
            <ScoreChart data={assessmentHistory} />
          ) : (
            <div className="empty-state compact">Complete an assessment to see your progress here.</div>
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <div className="eyebrow">Mood history</div>
            <h3>Recent emotional signals</h3>
          </div>
          {moodHistory.length ? (
            <div className="mood-history">
              <div className="mood-current">
                <span>Latest signal</span>
                <strong>{formatMood(latestMood)}</strong>
              </div>
              <div className="emotion-history">
                {moodHistory.slice(-8).map((item, index) => (
                  <span className="emotion-chip" key={`${item.emotion}-${item.created_at}-${index}`}>
                    {formatMood(item.emotion)}
                  </span>
                ))}
              </div>
              <small>These are supportive signals, not a clinical measure.</small>
            </div>
          ) : (
            <div className="empty-state compact">No emotion estimates have been recorded yet.</div>
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <div className="eyebrow">Next small steps</div>
            <h3>What may help today</h3>
          </div>
          <ul className="prompt-list action-list">
            {getMoodActions(latestMood).map((action) => <li key={action}>{action}</li>)}
          </ul>
          <small className="dashboard-note">Choose one gentle step; you do not need to do everything.</small>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function formatMood(mood) {
  return mood
    ? mood.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
    : 'Not available'
}

function getMoodActions(mood) {
  const normalized = (mood || '').toLowerCase()
  if (/(sad|fear|grief|lonely)/.test(normalized)) {
    return ['Message or speak with someone you trust.', 'Try a grounding activity: name five things you can see.', 'Take one manageable care step, such as water, food, or rest.']
  }
  if (/(anger|stress|anxious|nervous|worry)/.test(normalized)) {
    return ['Try five slow breaths with a longer exhale.', 'Write down the one thing creating the most pressure.', 'Take a short pause before your next task.']
  }
  if (/(happy|joy|calm|content|curious)/.test(normalized)) {
    return ['Notice what supported this feeling and write it down.', 'Share a small positive moment with someone.', 'Choose one realistic intention for the rest of the day.']
  }
  return ['Check in with your body: water, food, movement, or rest.', 'Name one thing that feels manageable right now.', 'Use the chat to reflect on what support would feel useful.']
}

function ScoreChart({ data }) {
  const width = 560
  const height = 190
  const padding = 28
  const maximum = Math.max(5, ...data.map((item) => Number(item.score) || 0))
  const points = data.map((item, index) => {
    const x = data.length === 1 ? width / 2 : padding + (index * (width - padding * 2)) / (data.length - 1)
    const y = height - padding - ((Number(item.score) || 0) / maximum) * (height - padding * 2)
    return { ...item, x, y }
  })

  return (
    <div className="score-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Assessment scores over time">
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} className="chart-axis" />
        <polyline points={points.map((point) => `${point.x},${point.y}`).join(' ')} className="score-line" />
        {points.map((point, index) => (
          <g key={`${point.created_at}-${index}`}>
            <circle cx={point.x} cy={point.y} r="5" className="score-point" />
            <text x={point.x} y={point.y - 10} textAnchor="middle" className="score-label">{point.score}</text>
          </g>
        ))}
      </svg>
      <div className="chart-caption"><span>Earlier</span><span>Lower score = fewer low/strain answers</span><span>Recent</span></div>
      <small>Scores reflect this check-in questionnaire and are not a diagnosis.</small>
    </div>
  )
}

function ProfilePage({ user, token, setAuth }) {
  const [form, setForm] = useState({ name: user?.name || '', preferred_language: user?.preferred_language || 'English' })
  const [status, setStatus] = useState({ text: '', error: false })

  async function saveProfile(e) {
    e.preventDefault()
    try {
      const updated = await apiRequest('/users/me', { method: 'PATCH', body: JSON.stringify(form) }, token)
      setAuth((prev) => ({ ...prev, user: updated }))
      setStatus({ text: 'Profile updated successfully.', error: false })
    } catch (err) {
      setStatus({ text: err instanceof Error ? err.message : 'Unable to update profile.', error: true })
    }
  }

  return (
    <div className="page profile-page">
      <div className="panel">
        <div className="panel-header">
          <div className="eyebrow">Profile</div>
          <h2>Update your details</h2>
        </div>

        <form onSubmit={saveProfile} className="stacked-form">
          <label className="field">
            <span>Name</span>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>

          <label className="field">
            <span>Preferred language</span>
            <select value={form.preferred_language} onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}>
              {languageOptions.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </label>

          {status.text && <div className={status.error ? 'error-box' : 'success-box'} role={status.error ? 'alert' : 'status'}>{status.text}</div>}
          <button className="primary-button" type="submit">Save changes</button>
        </form>
      </div>
    </div>
  )
}

function LanguagePage({ user, token, setAuth }) {
  const [language, setLanguage] = useState(user?.preferred_language || 'English')
  const [status, setStatus] = useState({ text: '', error: false })

  async function updateLanguage() {
    try {
      const updated = await apiRequest('/users/me', { method: 'PATCH', body: JSON.stringify({ preferred_language: language }) }, token)
      setAuth((prev) => ({ ...prev, user: updated }))
      setStatus({ text: 'Language preference saved.', error: false })
    } catch (err) {
      setStatus({ text: err instanceof Error ? err.message : 'Unable to save language preference.', error: true })
    }
  }

  return (
    <div className="page language-page">
      <div className="panel">
        <div className="panel-header">
          <div className="eyebrow">Language settings</div>
          <h2>Interface language</h2>
        </div>

        <div className="stacked-form">
          <label className="field">
            <span>Select a language</span>
            <select value={language} onChange={(e) => setLanguage(e.target.value)}>
              {languageOptions.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </label>
          {status.text && <div className={status.error ? 'error-box' : 'success-box'} role={status.error ? 'alert' : 'status'}>{status.text}</div>}
          <button className="primary-button" type="button" onClick={updateLanguage}>Save preference</button>
        </div>
      </div>
    </div>
  )
}

function HelpPage() {
  return (
    <div className="page help-page">
      <div className="panel">
        <div className="panel-header">
          <div className="eyebrow">Crisis support</div>
          <h2>Resources and next steps</h2>
        </div>

        <div className="resource-grid">
          {crisisResources.map((resource) => (
            <div key={resource.label} className="resource-card">
              <strong>{resource.label}</strong>
              <div>{resource.value}</div>
              <small>{resource.description}</small>
            </div>
          ))}
        </div>

        <div className="notice-box">
          ASHA AI is not a human therapist and emotion predictions are estimates, not diagnoses.
          In immediate danger, contact emergency services or a trusted person right away.
        </div>
      </div>
    </div>
  )
}

export default App
