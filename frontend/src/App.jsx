import { useState } from "react";

const API = "https://dating-assistant-production.up.railway.app";

export default function App() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState("");

  async function sendMessage() {
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
    setResponse(data.response);
  }

  return (
    <div style={{ padding: "40px" }}>
      <h1>Yash AI ❤️</h1>

      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask something..."
        style={{ width: "300px", padding: "10px" }}
      />

      <button onClick={sendMessage} style={{ marginLeft: "10px" }}>
        Send
      </button>

      <p>{response}</p>
    </div>
  );
}