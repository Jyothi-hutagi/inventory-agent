import { useState, useRef, useEffect } from 'react'
import styled, { keyframes, createGlobalStyle } from 'styled-components'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ── Animations ──────────────────────────────────────────────────────────────
const fadeUp = keyframes`from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}`
const blink  = keyframes`0%,100%{opacity:1}50%{opacity:0}`
const pulse  = keyframes`0%,100%{box-shadow:0 0 0 0 rgba(0,212,255,0.3)}50%{box-shadow:0 0 0 6px rgba(0,212,255,0)}`
const spin   = keyframes`to{transform:rotate(360deg)}`
const glow   = keyframes`0%,100%{text-shadow:0 0 8px rgba(245,166,35,0.6)}50%{text-shadow:0 0 20px rgba(245,166,35,1)}`

// ── Layout ───────────────────────────────────────────────────────────────────
const Shell = styled.div`
  display: grid;
  grid-template-columns: 260px 1fr;
  grid-template-rows: 56px 1fr;
  height: 100vh;
  background: var(--bg-0);
`

const TopBar = styled.header`
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px;
  background: var(--bg-1);
  border-bottom: 1px solid var(--border);
  position: relative;
  z-index: 10;
`

const Logo = styled.div`
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--amber);
  animation: ${glow} 3s ease-in-out infinite;
  span { color: var(--text-secondary); font-weight: 300; }
`

const StatusDot = styled.div`
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--green);
  animation: ${pulse} 2s infinite;
  margin-left: auto;
`
const StatusLabel = styled.span`
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--green);
  letter-spacing: 0.1em;
`

const Sidebar = styled.aside`
  background: var(--bg-1);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
`

const SideSection = styled.div`
  padding: 16px;
  border-bottom: 1px solid var(--border);
`

const SideTitle = styled.div`
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.15em;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 12px;
`

const QueryBtn = styled.button`
  display: block;
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  margin-bottom: 6px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  line-height: 1.4;

  &:hover {
    background: var(--bg-3);
    border-color: var(--cyan-dim);
    color: var(--text-primary);
  }
  &:active { transform: scale(0.98); }
`

const InfoBox = styled.div`
  margin: 16px;
  padding: 14px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--amber-dim);
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.7;

  strong { color: var(--amber); font-family: var(--font-mono); }
`

// ── Chat area ────────────────────────────────────────────────────────────────
const ChatArea = styled.main`
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-0);
  position: relative;
`

const GridBg = styled.div`
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(var(--border) 1px, transparent 1px),
    linear-gradient(90deg, var(--border) 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.3;
  pointer-events: none;
`

const Messages = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: relative;
  z-index: 1;
`

const EmptyState = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  animation: ${fadeUp} 0.4s ease;

  .icon { font-size: 48px; margin-bottom: 8px; }
  h2 {
    font-family: var(--font-display);
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: var(--text-primary);
  }
  p { color: var(--text-secondary); max-width: 360px; font-size: 14px; }
`

const Msg = styled.div`
  display: flex;
  gap: 14px;
  animation: ${fadeUp} 0.25s ease;
  align-items: flex-start;
  ${p => p.$user && 'flex-direction: row-reverse;'}
`

const Avatar = styled.div`
  width: 34px; height: 34px;
  border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  ${p => p.$user
    ? 'background: var(--bg-3); border: 1px solid var(--border-bright);'
    : 'background: linear-gradient(135deg,#1a3a5c,#0a1a2e); border: 1px solid var(--cyan-dim);'}
`

const Bubble = styled.div`
  max-width: 72%;
  padding: 14px 18px;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;

  ${p => p.$user ? `
    background: var(--bg-3);
    border: 1px solid var(--border-bright);
    color: var(--text-primary);
    text-align: right;
  ` : `
    background: var(--bg-1);
    border: 1px solid var(--border);
    border-left: 3px solid var(--cyan-dim);
    color: var(--text-primary);
    font-family: var(--font-body);
  `}
`

const ThinkingBubble = styled(Bubble)`
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 12px;
`

const Spinner = styled.div`
  width: 16px; height: 16px;
  border: 2px solid var(--border-bright);
  border-top-color: var(--cyan);
  border-radius: 50%;
  animation: ${spin} 0.7s linear infinite;
  flex-shrink: 0;
`

// ── Input bar ─────────────────────────────────────────────────────────────────
const InputBar = styled.div`
  padding: 16px 32px 24px;
  border-top: 1px solid var(--border);
  background: var(--bg-1);
  position: relative;
  z-index: 1;
`

const InputRow = styled.div`
  display: flex;
  gap: 10px;
  align-items: flex-end;
`

const Textarea = styled.textarea`
  flex: 1;
  background: var(--bg-2);
  border: 1px solid var(--border-bright);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 14px;
  padding: 12px 16px;
  resize: none;
  min-height: 48px;
  max-height: 140px;
  line-height: 1.5;
  transition: border-color 0.15s;
  outline: none;

  &::placeholder { color: var(--text-muted); }
  &:focus { border-color: var(--cyan-dim); }
`

const SendBtn = styled.button`
  width: 48px; height: 48px;
  border-radius: 6px;
  border: none;
  background: ${p => p.disabled ? 'var(--bg-3)' : 'var(--amber)'};
  color: ${p => p.disabled ? 'var(--text-muted)' : '#000'};
  font-size: 20px;
  cursor: ${p => p.disabled ? 'not-allowed' : 'pointer'};
  transition: all 0.15s;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;

  &:hover:not(:disabled) { background: #ffba42; transform: scale(1.04); }
`

const Hint = styled.div`
  margin-top: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.05em;
`

// ── Main component ────────────────────────────────────────────────────────────
const SAMPLES = [
  { label: '📦 Inventory Overview',   query: 'Give me an overview of our current inventory status' },
  { label: '⚠️ Low Stock Alert',      query: 'Which raw materials are below reorder level?' },
  { label: '🔩 Metals Stock',         query: 'Show me the stock status for all metal materials' },
  { label: '🚚 Pending Orders',       query: 'What purchase orders are pending or delayed?' },
  { label: '🔥 Fast-Moving Stock',    query: 'What are our top 5 most consumed materials this month?' },
  { label: '🏭 Warehouse Breakdown',  query: 'Give me a breakdown of stock value by warehouse' },
]

export default function App() {
  const [messages, setMessages]     = useState([])
  const [input, setInput]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [sessionId, setSessionId]   = useState(null)
  const bottomRef                   = useRef(null)
  const textareaRef                 = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (text) => {
    const question = (text || input).trim()
    if (!question || loading) return

    setMessages(m => [...m, { role: 'user', text: question }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, session_id: sessionId }),
      })
      const data = await res.json()
      if (data.session_id) setSessionId(data.session_id)
      setMessages(m => [...m, { role: 'agent', text: data.answer || data.detail || 'No response.' }])
    } catch (e) {
      setMessages(m => [...m, { role: 'agent', text: '⚠️ Could not reach the agent API. Make sure the backend is running.' }])
    } finally {
      setLoading(false)
      textareaRef.current?.focus()
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  const handleSample = (q) => sendMessage(q)

  const clearChat = () => { setMessages([]); setSessionId(null) }

  return (
    <Shell>
      {/* Top bar */}
      <TopBar>
        <Logo>INVENTORY<span>IQ</span></Logo>
        <span style={{ color: 'var(--text-muted)', fontSize: 13, fontFamily: 'var(--font-mono)' }}>
          / manufacturing intelligence agent
        </span>
        <StatusDot />
        <StatusLabel>AGENT ONLINE</StatusLabel>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            style={{
              marginLeft: 12,
              background: 'none',
              border: '1px solid var(--border)',
              color: 'var(--text-muted)',
              padding: '4px 10px',
              borderRadius: 4,
              cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              letterSpacing: '0.08em',
            }}
          >
            CLEAR
          </button>
        )}
      </TopBar>

      {/* Sidebar */}
      <Sidebar>
        <SideSection>
          <SideTitle>Quick Queries</SideTitle>
          {SAMPLES.map(s => (
            <QueryBtn key={s.label} onClick={() => handleSample(s.query)} disabled={loading}>
              {s.label}
            </QueryBtn>
          ))}
        </SideSection>

        <InfoBox>
          <strong>DATA SOURCE</strong><br />
          BigQuery · inventory_db<br /><br />
          <strong>TABLES</strong><br />
          raw_materials<br />
          suppliers<br />
          purchase_orders<br />
          consumption_log<br /><br />
          <strong>STACK</strong><br />
          Google ADK · MCP Toolbox<br />
          Gemini 2.0 Flash · Cloud Run
        </InfoBox>
      </Sidebar>

      {/* Chat */}
      <ChatArea>
        <GridBg />
        <Messages>
          {messages.length === 0 && !loading ? (
            <EmptyState>
              <div className="icon">🏭</div>
              <h2>MANUFACTURING INTELLIGENCE</h2>
              <p>
                Ask anything about your raw material inventory — stock levels,
                reorder alerts, supplier status, warehouse breakdown, and more.
              </p>
            </EmptyState>
          ) : (
            messages.map((m, i) => (
              <Msg key={i} $user={m.role === 'user'}>
                <Avatar $user={m.role === 'user'}>
                  {m.role === 'user' ? '👤' : '🤖'}
                </Avatar>
                <Bubble $user={m.role === 'user'}>{m.text}</Bubble>
              </Msg>
            ))
          )}
          {loading && (
            <Msg>
              <Avatar>🤖</Avatar>
              <ThinkingBubble>
                <Spinner />
                querying bigquery via mcp...
              </ThinkingBubble>
            </Msg>
          )}
          <div ref={bottomRef} />
        </Messages>

        <InputBar>
          <InputRow>
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about your inventory — stock levels, reorder alerts, suppliers, consumption..."
              rows={1}
              disabled={loading}
            />
            <SendBtn onClick={() => sendMessage()} disabled={loading || !input.trim()}>
              ➤
            </SendBtn>
          </InputRow>
          <Hint>ENTER to send · SHIFT+ENTER for new line · session: {sessionId ? sessionId.slice(0,8)+'…' : 'new'}</Hint>
        </InputBar>
      </ChatArea>
    </Shell>
  )
}
