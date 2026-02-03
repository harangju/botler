import { getAgent, type Agent } from "../agents/index.js"

export interface ParsedMention {
  agentName: string | null
  agent: Agent | null
  content: string
}

// Parse @mention from start of message
export function parseMention(text: string): ParsedMention {
  const match = text.match(/^@(\w+)\s*/)
  if (!match) return { agentName: null, agent: null, content: text }

  const agentName = match[1].toLowerCase()
  return {
    agentName,
    agent: getAgent(agentName) || null,
    content: text.slice(match[0].length)
  }
}

// Check for @mention anywhere in text (for chaining)
export function extractMention(text: string): ParsedMention {
  const match = text.match(/@(\w+)(?:\s|$)/)
  if (!match) return { agentName: null, agent: null, content: text }

  const agentName = match[1].toLowerCase()
  return { agentName, agent: getAgent(agentName) || null, content: text }
}
