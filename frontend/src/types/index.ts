export type RagMode = "adaptive" | "agentic"

export interface AgentStep {
  type: string
  query?: string | null
}

export interface Message {
  role: "user" | "assistant"
  content: string
  sources?: Source[]
  tokens?: Tokens
  responseTimeMs?: number
  mode?: RagMode
  agentSteps?: AgentStep[]
}

export interface Source {
  title: string
  url: string
  excerpt: string
}

export interface Tokens {
  input: number
  output: number
}

export interface ChatResponse {
  answer: string
  sources: Source[]
  tokens: Tokens
  response_time_ms: number
  mode?: RagMode
  agent_steps?: AgentStep[]
}
