import { useMutation } from "@tanstack/react-query"
import { useState } from "react"

import { sendMessage } from "@/api/chat"
import type { Message, RagMode } from "@/types"

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [mode, setMode] = useState<RagMode>("adaptive")

  const mutation = useMutation({
    mutationFn: ({
      question,
      history,
      mode: requestMode,
    }: {
      question: string
      history: { role: string; content: string }[]
      mode: RagMode
    }) => sendMessage(question, history, requestMode),
    onSuccess: (result) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.answer,
          sources: result.sources,
          tokens: result.tokens,
          responseTimeMs: result.response_time_ms,
          mode: result.mode ?? "adaptive",
          agentSteps: result.agent_steps ?? [],
        },
      ])
    },
  })

  const send = (question: string) => {
    const history = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }))

    setMessages((prev) => [...prev, { role: "user", content: question }])
    mutation.reset()
    mutation.mutate({ question, history, mode })
  }

  return {
    messages,
    send,
    mode,
    setMode,
    status: mutation.status,
    isPending: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error,
    data: mutation.data,
  }
}
