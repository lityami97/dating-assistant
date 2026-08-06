import { useState, useRef, useEffect } from "react";

const API = "https://dating-assistant-production.up.railway.app";

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hi! I'm lityami. Feel free to ask me anything about Yash.",
      sender: "bot",
      timestamp: new Date(),
    },
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function sendMessage(e) {
    e.preventDefault();
    if (!question.trim()) return;

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      text: question,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          user_id: "user1",
        }),
      });

      const data = await res.json();

      const botMessage = {
        id: messages.length + 2,
        text: data.response || "Sorry, I couldn't process that. Please try again.",
        sender: "bot",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error:", error);
      const errorMessage = {
        id: messages.length + 2,
        text: "Oops! Something went wrong. Please try again.",
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen bg-black text-white overflow-hidden">
      {/* HEADER */}
      <div className="border-b border-gray-800 px-6 py-8 flex-shrink-0">
        <h1 className="text-4xl font-bold tracking-tight text-center">
          lityami
        </h1>
      </div>

      {/* MESSAGES CONTAINER */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-md px-6 py-4 text-base leading-relaxed break-words ${
                  msg.sender === "user"
                    ? "bg-gray-900 text-white"
                    : "text-gray-200"
                }`}
              >
                <p>{msg.text}</p>
                <span className="text-xs text-gray-500 mt-2 block">
                  {msg.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="text-gray-500 text-base">
                <span className="animate-pulse">●●●</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* INPUT AREA */}
      <div className="border-t border-gray-800 px-6 py-6 flex-shrink-0">
        <form onSubmit={sendMessage} className="max-w-3xl mx-auto">
          <div className="flex gap-3 items-center">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Type your message..."
              disabled={loading}
              className="flex-1 px-6 py-4 bg-gray-950 border border-cyan-500 rounded-lg text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all disabled:opacity-50 disabled:cursor-not-allowed text-base"
              style={{
                boxShadow: "0 0 20px rgba(34, 211, 238, 0.2)",
              }}
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="px-6 py-4 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {loading ? "..." : "Send"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}