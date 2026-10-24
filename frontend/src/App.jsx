import { useEffect, useMemo, useRef, useState } from 'react'
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
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
  MoonStar,
  NotebookPen,
  ShieldAlert,
  Sparkles,
  UserRound,
  Volume2,
} from 'lucide-react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const STORAGE_KEY = 'asha-auth'

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
const crisisResources = [
  { label: 'Emergency', value: '112', description: 'For immediate assistance in India' },
  { label: 'Tele-MANAS', value: '14416', description: 'Mental health support line' },
  { label: 'Local emergency services', value: 'Verify locally', description: 'Check current availability in your area' },
]

function apiRequest(path, options = {}, token) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (token) headers.Authorization = `Bearer ${token}`

  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  }).then(async (response) => {
    const contentType = response.headers.get('content-type') || ''
    const payload = contentType.includes('application/json') ? await response.json() : null

    if (!response.ok) {
      const message = payload?.detail || payload?.error || 'Something went wrong.'
      throw new Error(message)
    }

    return payload
  })
}

function App() {
  const [auth, setAuth] = useState(() => {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : { token: '', user: null }
  })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
  }, [auth])

  return (
    <BrowserRouter>
      <AppLayout auth={auth} setAuth={setAuth} />
    </BrowserRouter>
  )
}

function AppLayout({ auth, setAuth }) {
  const location = useLocation()
  const currentPath = location.pathname
  const isLoggedIn = Boolean(auth.token && auth.user)

  return (
    <div className="app-shell">
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
          <FeatureCard icon={<ShieldAlert size={20} />} title="Safety-aware" text="Crisis support is prioritized with clear emergency resources when needed." />
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
      setError(err.message)
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

function AssessmentPage({ user, token }) {
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
      setError(err.message)
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
  const navigate = useNavigate()
  const messagesEndRef = useRef(null)
  const [conversation, setConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [composer, setComposer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    async function init() {
      try {
        const list = await apiRequest('/conversations', { method: 'GET' }, token)
        if (list.length === 0) {
          const newConversation = await apiRequest('/conversations', {
            method: 'POST',
            body: JSON.stringify({ title: 'New conversation' }),
          }, token)
          if (!ignore) setConversation(newConversation)
          return
        }
        const latest = list[0]
        if (!ignore) {
          setConversation(latest)
          const messageList = await apiRequest(`/conversations/${latest.id}/messages`, { method: 'GET' }, token)
          setMessages(messageList)
        }
      } catch (err) {
        if (!ignore) setError(err.message)
      }
    }

    init()
    return () => {
      ignore = true
    }
  }, [token])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function submitMessage() {
    const trimmed = composer.trim()
    if (!trimmed || !conversation || loading) return

    setLoading(true)
    setError('')
    const userContent = trimmed
    setComposer('')
    setMessages((prev) => [...prev, { id: Date.now(), conversation_id: conversation.id, sender: 'user', content: userContent }])

    try {
      const response = await apiRequest('/chat', {
        method: 'POST',
        body: JSON.stringify({
          conversation_id: conversation.id,
          sender: 'user',
          content: userContent,
        }),
      }, token)

      setMessages((prev) => [...prev, { ...response.assistant_message, timestamp: new Date().toISOString() }])
      const refreshed = await apiRequest(`/conversations/${conversation.id}/messages`, { method: 'GET' }, token)
      setMessages(refreshed)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submitMessage()
    }
  }

  async function startNewChat() {
    try {
      const newConversation = await apiRequest('/conversations', {
        method: 'POST',
        body: JSON.stringify({ title: 'New conversation' }),
      }, token)
      setConversation(newConversation)
      setMessages([])
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page chat-page">
      <div className="chat-header">
        <div>
          <div className="eyebrow">ASHA AI</div>
          <h2>How are you feeling today?</h2>
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

      <div className="chat-window">
        {messages.length === 0 && !loading && (
          <div className="empty-state">
            <Sparkles size={28} />
            <h3>Start a gentle conversation</h3>
            <p>ASHA is here to listen and help you reflect, not diagnose.</p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`message-row ${message.sender === 'user' ? 'user' : 'assistant'}`}>
            <div className="message-bubble">
              <p>{message.content}</p>
              <span>{new Date(message.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
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

        {error && <div className="error-box">{error}</div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="composer-box">
        <textarea
          value={composer}
          onChange={(e) => setComposer(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={3}
          placeholder="Share what is on your mind..."
        />
        <div className="composer-actions">
          <button type="button" className="icon-button" aria-label="Voice input">
            <Mic size={18} />
          </button>
          <button type="button" className="icon-button" aria-label="Text to speech">
            <Volume2 size={18} />
          </button>
          <button type="button" className="primary-button" onClick={submitMessage} disabled={loading || !composer.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

function HistoryPage({ token }) {
  const [conversations, setConversations] = useState([])

  useEffect(() => {
    apiRequest('/conversations', { method: 'GET' }, token)
      .then(setConversations)
      .catch(() => setConversations([]))
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

        {conversations.length === 0 ? (
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
                <Link to="/chat" className="secondary-button small-button">Open</Link>
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

  useEffect(() => {
    apiRequest('/dashboard', { method: 'GET' }, token)
      .then(setDashboard)
      .catch(() => setDashboard({ total_conversations: 0, total_messages: 0, latest_assessment: 0, recent_emotions: [], latest_risk_level: 'no_crisis_signal' }))
  }, [token])

  if (!dashboard) return <div className="page">Loading…</div>

  const moodBars = ['Very low', 'Low', 'Okay', 'Good', 'Great']

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
            <div className="eyebrow">Mood history</div>
            <h3>Latest emotional signals</h3>
          </div>
          <div className="bar-chart">
            {moodBars.map((label, index) => {
              const height = 20 + index * 18
              const active = dashboard.recent_emotions?.includes(label) || index === 2
              return (
                <div key={label} className="bar-group">
                  <div className="bar" style={{ height: `${height}%`, opacity: active ? 1 : 0.35 }} />
                  <span>{label}</span>
                </div>
              )
            })}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div className="eyebrow">Reflection</div>
            <h3>Supportive prompts</h3>
          </div>
          <ul className="prompt-list">
            <li>What felt manageable about today?</li>
            <li>What created the most mental load this week?</li>
            <li>What is one small act of care you can give yourself?</li>
          </ul>
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

function ProfilePage({ user, token, setAuth }) {
  const [form, setForm] = useState({ name: user?.name || '', preferred_language: user?.preferred_language || 'English' })
  const [status, setStatus] = useState('')

  async function saveProfile(e) {
    e.preventDefault()
    try {
      const updated = await apiRequest('/users/me', { method: 'PATCH', body: JSON.stringify(form) }, token)
      setAuth((prev) => ({ ...prev, user: updated }))
      setStatus('Profile updated successfully.')
    } catch (err) {
      setStatus(err.message)
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

          {status && <div className="success-box">{status}</div>}
          <button className="primary-button" type="submit">Save changes</button>
        </form>
      </div>
    </div>
  )
}

function LanguagePage({ user, token, setAuth }) {
  const [language, setLanguage] = useState(user?.preferred_language || 'English')
  const [status, setStatus] = useState('')

  async function updateLanguage() {
    try {
      const updated = await apiRequest('/users/me', { method: 'PATCH', body: JSON.stringify({ preferred_language: language }) }, token)
      setAuth((prev) => ({ ...prev, user: updated }))
      setStatus('Language preference saved.')
    } catch (err) {
      setStatus(err.message)
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
          {status && <div className="success-box">{status}</div>}
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
