import { ChevronDown, ListTree, Paperclip, User, PawPrint } from "lucide-react"

import { AgentSteps } from "@/components/AgentSteps"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Separator } from "@/components/ui/separator"
import { MarkdownContent } from "@/components/MarkdownContent"
import { SourcesPanel } from "@/components/SourcesPanel"
import { TokenBar } from "@/components/TokenBar"
import { cn } from "@/lib/utils"
import type { Message } from "@/types"

interface Props {
  message: Message
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user"
  const agentSteps = message.agentSteps ?? []
  const showAgentSteps = !isUser && message.mode === "agentic" && agentSteps.length > 0

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <Card
        className={cn(
          "max-w-[85%] gap-3 py-3",
          isUser
            ? "border-primary/30 bg-primary/10"
            : "bg-card"
        )}
      >
        <CardHeader className="flex-row items-center gap-2 space-y-0 px-4 py-0">
          {isUser ? (
            <User className="text-muted-foreground size-3.5" />
          ) : (
            <PawPrint className="text-primary size-3.5" />
          )}
          <span className="text-muted-foreground text-xs font-medium">
            {isUser ? "You" : "Assistant"}
          </span>
          {!isUser && message.mode === "agentic" && (
            <Badge variant="outline" className="ml-1 font-normal">
              Agentic
            </Badge>
          )}
        </CardHeader>

        <CardContent className="px-4 py-0">
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            <MarkdownContent content={message.content} />
          )}

          {showAgentSteps && (
            <div className="mt-3">
              <Separator className="mb-3" />
              <Collapsible className="group/steps">
                <CollapsibleTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-primary h-auto gap-1.5 px-0 py-0 hover:bg-transparent"
                  >
                    <ListTree className="size-3.5" />
                    Steps ({agentSteps.length})
                    <ChevronDown className="size-3.5 transition-transform group-data-[state=open]/steps:rotate-180" />
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <AgentSteps steps={agentSteps} />
                </CollapsibleContent>
              </Collapsible>
            </div>
          )}

          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-3">
              <Separator className="mb-3" />
              <Collapsible className="group/sources">
                <CollapsibleTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-primary h-auto gap-1.5 px-0 py-0 hover:bg-transparent"
                  >
                    <Paperclip className="size-3.5" />
                    Sources ({message.sources.length})
                    <ChevronDown className="size-3.5 transition-transform group-data-[state=open]/sources:rotate-180" />
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <SourcesPanel sources={message.sources} />
                </CollapsibleContent>
              </Collapsible>
            </div>
          )}

          {!isUser && message.tokens && (
            <TokenBar
              tokens={message.tokens}
              responseTimeMs={message.responseTimeMs}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
