import { ExternalLink } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import type { Source } from "@/types"

interface Props {
  sources: Source[]
}

export function SourcesPanel({ sources }: Props) {
  return (
    <div className="mt-2 space-y-2">
      {sources.map((source, i) => (
        <div
          key={i}
          className="bg-background/60 space-y-1.5 rounded-lg border p-2.5 text-xs leading-relaxed"
        >
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-primary border-primary/40">
              {i + 1}
            </Badge>
            <span className="text-primary font-medium">{source.title}</span>
          </div>
          <p className="text-muted-foreground line-clamp-3">{source.excerpt}</p>
          {source.url && (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-primary inline-flex items-center gap-1 transition-colors"
            >
              View on wiki
              <ExternalLink className="size-3" />
            </a>
          )}
        </div>
      ))}
    </div>
  )
}
