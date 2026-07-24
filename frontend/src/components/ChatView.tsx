import { useRef, useEffect } from "react"
import { AlertCircle, Loader2, PawPrint } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { ChatInput } from "@/components/ChatInput"
import { MessageBubble } from "@/components/MessageBubble"
import { useChat } from "@/hooks/useChat"
import { cn } from "@/lib/utils"
import type { RagMode } from "@/types"

const MODES: { id: RagMode; label: string }[] = [
  { id: "adaptive", label: "Adaptive" },
  { id: "agentic", label: "Agentic" },
]

export function ChatView() {
  const { messages, send, mode, setMode, isPending, isError, error } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isPending])

  return (
    <div className="mx-auto flex h-screen max-w-3xl flex-col">
      <header className="flex shrink-0 flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-3">
          <PawPrint className="text-primary size-7" />
          <div>
            <h1 className="text-primary text-lg font-semibold">
              Witcher 3 — Wiki Assistant
            </h1>
            <p className="text-muted-foreground text-xs">
              Adaptive RAG · LangGraph agentic mode · multi-provider LLM
            </p>
          </div>
        </div>

        <div
          className="bg-muted flex rounded-lg p-0.5"
          role="group"
          aria-label="RAG mode"
        >
          {MODES.map((option) => (
            <Button
              key={option.id}
              type="button"
              size="sm"
              variant="ghost"
              disabled={isPending}
              onClick={() => setMode(option.id)}
              className={cn(
                "h-7 rounded-md px-2.5 text-xs",
                mode === option.id
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </header>
      <Separator />

      <ScrollArea className="min-h-0 flex-1">
        <div className="space-y-4 px-4 py-4">
          {messages.length === 0 && (
            <Card className="mx-auto mt-16 max-w-sm border-dashed text-center">
              <CardHeader>
                <PawPrint className="text-primary mx-auto size-10 opacity-80" />
                <CardTitle className="text-base">Ask anything about The Witcher 3</CardTitle>
                <CardDescription>
                  Quests, characters, gear, monsters, alchemy, lore...
                  {mode === "agentic"
                    ? " Agentic mode uses a LangGraph tool loop for multi-step search."
                    : " Adaptive mode rewrites and retries on weak retrieval."}
                </CardDescription>
              </CardHeader>
            </Card>
          )}

          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}

          {isPending && (
            <div className="text-muted-foreground flex items-center gap-2 text-sm">
              <Loader2 className="size-4 animate-spin" />
              {mode === "agentic" ? "agent researching..." : "thinking..."}
            </div>
          )}

          {isError && (
            <Alert variant="destructive">
              <AlertCircle />
              <AlertDescription>
                {error instanceof Error ? error.message : "Something went wrong"}
              </AlertDescription>
            </Alert>
          )}

          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <ChatInput onSend={send} disabled={isPending} />
    </div>
  )
}
