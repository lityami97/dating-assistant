import { useEffect, useRef, useState } from "react";

const API = "https://dating-assistant-production.up.railway.app";

const INSTA_GRADIENT =
  "linear-gradient(45deg, #4f5bd5, #962fbf, #d62976, #fa7e1e, #feda75)";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hey! I'm abhinav. What's on your mind today?",
    },
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function sendMessage() {
  const text = question.trim();
  if (!text || loading) return;

  setMessages((prev) => [...prev, { role: "user", text }]);
  setQuestion("");
  setLoading(true);

  try {
    const res = await fetch(`${API}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: text,
        user_id: "user1",
      }),
    });

    if (!res.ok) {
      throw new Error(`HTTP Error: ${res.status}`);
    }

    const data = await res.json();

    console.log("Backend Response:", data);

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        text:
          data.answer ||
          data.response ||
          "Sorry, I couldn't generate a response.",
      },
    ]);
  } catch (err) {
    console.error("Chat Error:", err);

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        text: `Error: ${err.message}`,
      },
    ]);
  } finally {
    setLoading(false);
  }
}

  return (
    <div style={styles.page}>
      <div style={styles.app}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.avatarRing}>
            <div style={styles.avatar}>L</div>
          </div>
          <div>
            <div style={styles.headerName}>Lityami</div>
            <div style={styles.headerStatus}>Active now</div>
          </div>
        </div>

        {/* Messages */}
        <div style={styles.thread} ref={scrollRef}>
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                ...styles.bubbleRow,
                justifyContent:
                  m.role === "user" ? "flex-end" : "flex-start",
              }}
            >
              <div
                style={
                  m.role === "user"
                    ? styles.bubbleUser
                    : styles.bubbleAssistant
                }
              >
                {m.text}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ ...styles.bubbleRow, justifyContent: "flex-start" }}>
              <div style={styles.bubbleAssistant}>
                <TypingDots />
              </div>
            </div>
          )}
        </div>

        {/* Composer */}
        <div style={styles.composer}>
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Message..."
            style={styles.input}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !question.trim()}
            style={{
              ...styles.sendBtn,
              opacity: loading || !question.trim() ? 0.4 : 1,
            }}
            aria-label="Send message"
          >
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <div style={styles.typing}>
      <span style={{ ...styles.dot, animationDelay: "0s" }} />
      <span style={{ ...styles.dot, animationDelay: "0.15s" }} />
      <span style={{ ...styles.dot, animationDelay: "0.3s" }} />
      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

function SendIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path
        d="M4 12L20 4L14 20L11 13L4 12Z"
        stroke="white"
        strokeWidth="1.8"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#000",
    display: "flex",
    justifyContent: "center",
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
  },
  app: {
    width: "100%",
    maxWidth: "420px",
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    background: "#000",
    borderLeft: "1px solid #1a1a1a",
    borderRight: "1px solid #1a1a1a",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "14px 16px",
    borderBottom: "1px solid #1c1c1e",
  },
  avatarRing: {
    width: "42px",
    height: "42px",
    borderRadius: "50%",
    padding: "2px",
    background: INSTA_GRADIENT,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  avatar: {
    width: "100%",
    height: "100%",
    borderRadius: "50%",
    background: "#000",
    color: "#fff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 700,
    fontSize: "16px",
  },
  headerName: {
    color: "#f5f5f5",
    fontSize: "15px",
    fontWeight: 600,
  },
  headerStatus: {
    color: "#8e8e8e",
    fontSize: "12px",
    marginTop: "1px",
  },
  thread: {
    flex: 1,
    overflowY: "auto",
    padding: "16px 12px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  bubbleRow: {
    display: "flex",
    width: "100%",
  },
  bubbleUser: {
    maxWidth: "75%",
    padding: "10px 14px",
    borderRadius: "20px",
    color: "#fff",
    fontSize: "14.5px",
    lineHeight: 1.35,
    background: INSTA_GRADIENT,
  },
  bubbleAssistant: {
    maxWidth: "75%",
    padding: "10px 14px",
    borderRadius: "20px",
    color: "#f5f5f5",
    fontSize: "14.5px",
    lineHeight: 1.35,
    background: "#262626",
  },
  typing: {
    display: "flex",
    gap: "4px",
    padding: "2px 0",
  },
  dot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    background: "#b3b3b3",
    display: "inline-block",
    animation: "bounce 1s infinite",
  },
  composer: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px 12px",
    borderTop: "1px solid #1c1c1e",
  },
  input: {
    flex: 1,
    background: "#1c1c1e",
    border: "1px solid #2c2c2e",
    borderRadius: "999px",
    padding: "10px 16px",
    color: "#f5f5f5",
    fontSize: "14.5px",
    outline: "none",
  },
  sendBtn: {
    width: "38px",
    height: "38px",
    borderRadius: "50%",
    border: "none",
    background: INSTA_GRADIENT,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    flexShrink: 0,
  },
};
