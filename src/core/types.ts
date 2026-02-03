export interface Message {
  role: "user" | "assistant"
  content: string
  agentName?: string
}

export interface ToolCall {
  id: string
  name: string
  args: Record<string, unknown>
  status: "running" | "done" | "error"
  result?: string
}

export type EngineEvent =
  | { type: "text"; text: string }
  | { type: "tool_start"; id: string; name: string }
  | { type: "tool_args"; id: string; args: Record<string, unknown> }
  | { type: "tool_done"; id: string; result: string }
  | { type: "tool_error"; id: string; error: string }
  | { type: "done"; response: string }
