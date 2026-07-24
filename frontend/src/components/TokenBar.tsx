import { Clock, Hash } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import type { Tokens } from "@/types"

interface Props {
  tokens: Tokens
  responseTimeMs?: number
}

export function TokenBar({ tokens, responseTimeMs }: Props) {
  const timeStr =
    responseTimeMs != null ? `${(responseTimeMs / 1000).toFixed(1)}s` : null

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2">
      <Badge variant="secondary" className="gap-1 font-normal">
        <Hash className="size-3" />
        {tokens.input} in · {tokens.output} out
      </Badge>
      {timeStr && (
        <Badge variant="secondary" className="gap-1 font-normal">
          <Clock className="size-3" />
          {timeStr}
        </Badge>
      )}
    </div>
  )
}
