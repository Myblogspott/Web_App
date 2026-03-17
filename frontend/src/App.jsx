import { useState, useRef, useEffect } from 'react'

const AGENT_URL = import.meta.env.VITE_AGENT_URL || '/api'

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  async function handleSubmit(e) {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || loading) return

    setInput('')

    // Conversation memory: send prior messages so the agent can refer to the past (OpenAI/LangChain pattern)
    const history = messages.map((m) => ({ role: m.role, content: m.content ?? '' }))

    // Add user message
    const userMessage = { role: 'user', content: trimmed }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      const controller = new AbortController()
      // Agent may make many MCP + LLM calls; allow up to 3 minutes
      const timeout = setTimeout(() => controller.abort(), 180000)
      const res = await fetch(`${AGENT_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history }),
        signal: controller.signal,
      })
      clearTimeout(timeout)

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        const detail = data.detail || (await res.text()) || `HTTP ${res.status}`
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
      }

      const data = await res.json()
      const assistantContent = data.response ?? ''
      setMessages((prev) => [...prev, { role: 'assistant', content: assistantContent }])
    } catch (err) {
      const errMsg = err.name === 'AbortError' ? 'Request timed out. The agent may need more time for many searches.' : (err.message || 'Request failed')
      setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${errMsg}`, isError: true }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-layout">
      <header className="chat-header">
        <h1>Court Listener Agent</h1>
        <p className="chat-header-subtitle">
          Search case law or federal dockets. Ask in plain language—e.g. “Find cases on First Amendment free speech” or “Docket search for civil rights.”
        </p>
      </header>

      <main className="chat-messages">
        {messages.length === 0 && !loading && (
          <div className="chat-welcome">
            <p>Start a conversation. Try:</p>
            <ul>
              <li>Find cases on First Amendment free speech</li>
              <li>Docket search for civil rights</li>
              <li>Recent employment discrimination opinions</li>
            </ul>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message chat-message-${msg.role}`}>
            <div className="chat-message-avatar">
              {msg.role === 'user' ? 'You' : 'CL'}
            </div>
            <div className={`chat-message-bubble ${msg.isError ? 'chat-message-error' : ''}`}>
              <div className="chat-message-content">{msg.content}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-message chat-message-assistant">
            <div className="chat-message-avatar">CL</div>
            <div className="chat-message-bubble chat-message-loading">
              <span className="chat-typing-dots">
                <span></span><span></span><span></span>
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <footer className="chat-input-wrap">
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message Court Listener Agent…"
            disabled={loading}
            autoComplete="off"
            className="chat-input"
          />
          <button type="submit" disabled={loading || !input.trim()} className="chat-send-btn" aria-label="Send">
            Send
          </button>
        </form>
      </footer>
    </div>
  )
}
