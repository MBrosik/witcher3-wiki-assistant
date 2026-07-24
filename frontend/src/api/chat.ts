import type { ChatResponse, RagMode } from "../types"

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

export async function sendMessage(
  question: string,
  history: { role: string; content: string }[] = [],
  mode: RagMode = "adaptive",
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history, mode }),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error (${res.status}): ${text}`)
  }

  return res.json()
}
