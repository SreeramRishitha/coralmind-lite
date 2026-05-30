import { useState } from "react"
import Message from "./Message"

export default function ChatBot() {
  const [question, setQuestion] = useState("")
  const [owner, setOwner] = useState("withcoral")
  const [repo, setRepo] = useState("coral")
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const ask = async () => {
    if (!question.trim()) return
    const userMsg = { type: "user", text: question }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    setQuestion("")

    try {
      const res = await fetch("https://coralmind-lite-backend.onrender.com/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, owner, repo })
      })
      const data = await res.json()
      setMessages(prev => [...prev, { type: "bot", data }])
    } catch (e) {
      setMessages(prev => [...prev, { type: "error", text: "Backend not reachable." }])
    }
    setLoading(false)
  }

  const handleKey = (e) => {
    if (e.key === "Enter") ask()
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Repo selector */}
      <div className="flex gap-2">
        <input
          value={owner}
          onChange={e => setOwner(e.target.value)}
          placeholder="owner"
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm w-1/2 focus:outline-none focus:border-emerald-500"
        />
        <input
          value={repo}
          onChange={e => setRepo(e.target.value)}
          placeholder="repo"
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm w-1/2 focus:outline-none focus:border-emerald-500"
        />
      </div>

      {/* Chat messages */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 min-h-64 max-h-96 overflow-y-auto p-4 flex flex-col gap-3">
        {messages.length === 0 && (
          <p className="text-gray-600 text-sm text-center mt-8">
            Try: "What are the recent issues?" or "Show open PRs"
          </p>
        )}
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        {loading && (
          <div className="text-emerald-400 text-sm animate-pulse">
            Querying Coral...
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about this repo..."
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:border-emerald-500"
        />
        <button
          onClick={ask}
          disabled={loading}
          className="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-black font-semibold px-6 py-3 rounded-lg"
        >
          Ask
        </button>
      </div>
    </div>
  )
}