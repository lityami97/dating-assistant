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

    // Add user message to chat
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
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 relative overflow-hidden">
      {/* Animated background effect */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl animate-blob"></div>
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-0 left-1/3 w-96 h-96 bg-slate-500 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-4000"></div>
      </div>

      {/* Content wrapper */}
      <div className="relative z-10 flex flex-col h-screen">
        {/* Header */}
        <div className="border-b border-slate-700/50 backdrop-blur-md bg-slate-900/30">
          <div className="max-w-2xl mx-auto px-6 py-6">
            <h1 className="text-3xl font-light text-white tracking-tight">
              lityami
            </h1>
            <p className="text-slate-300 text-sm mt-2 font-light">
              Ask me anything about Yash
            </p>
          </div>
        </div>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-2xl mx-auto space-y-6">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${
                  msg.sender === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-5 py-3.5 rounded-2xl backdrop-blur-sm ${
                    msg.sender === "user"
                      ? "bg-blue-600/80 text-white rounded-br-sm shadow-lg hover:bg-blue-600 transition-all"
                      : "bg-slate-800/60 text-slate-100 border border-slate-700/50 rounded-bl-sm shadow-md hover:bg-slate-800/80 transition-all"
                  }`}
                >
                  <p className="text-sm leading-relaxed font-light">
                    {msg.text}
                  </p>
                  <span
                    className={`text-xs mt-2 block ${
                      msg.sender === "user"
                        ? "text-blue-200"
                        : "text-slate-400"
                    }`}
                  >
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
                <div className="bg-slate-800/60 text-slate-100 border border-slate-700/50 px-5 py-3.5 rounded-2xl rounded-bl-sm shadow-md backdrop-blur-sm">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-700/50 backdrop-blur-md bg-slate-900/30">
          <form onSubmit={sendMessage} className="max-w-2xl mx-auto px-6 py-6">
            <div className="flex gap-3">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Type your question here..."
                disabled={loading}
                className="flex-1 px-5 py-3 border border-slate-600/50 rounded-full bg-slate-800/50 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all font-light disabled:bg-slate-900/30 disabled:cursor-not-allowed backdrop-blur-sm hover:bg-slate-800/60"
              />
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-full font-light hover:from-blue-500 hover:to-blue-600 transition-all disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed shadow-lg hover:shadow-xl hover:shadow-blue-500/50"
              >
                {loading ? "..." : "Send"}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-3 text-center font-light">
              Powered by AI • Questions are processed securely
            </p>
          </form>
        </div>
      </div>

      <style jsx>{`
        @keyframes blob {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
        }

        .animate-blob {
          animation: blob 7s infinite;
        }

        .animation-delay-2000 {
          animation-delay: 2s;
        }

        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}