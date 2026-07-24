import type { AgentStep } from "@/types"

interface Props {
  steps: AgentStep[]
}

function labelFor(step: AgentStep): string {
  switch (step.type) {
    case "search":
      return step.query ? `search: ${step.query}` : "search"
    case "refine":
      return step.query ? `refine → ${step.query}` : "refine"
    case "generate":
      return "generate answer"
    default:
      return step.query ? `${step.type}: ${step.query}` : step.type
  }
}

export function AgentSteps({ steps }: Props) {
  if (steps.length === 0) return null

  return (
    <ol className="text-muted-foreground mt-2 list-decimal space-y-1 pl-4 text-xs">
      {steps.map((step, i) => (
        <li key={`${step.type}-${i}`} className="leading-relaxed">
          {labelFor(step)}
        </li>
      ))}
    </ol>
  )
}
