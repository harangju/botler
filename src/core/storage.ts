import { mkdir } from "fs/promises"
import { dirname } from "path"
import { getAgentMemoryPath, getArchivePath } from "./paths.js"
import { getClient } from "./client.js"
import type { Message, SessionSummary } from "./types.js"

const COMPACTION_PROMPT = `You are a memory compaction system. Given an agent's memory and a conversation, produce updated memory.

Rules:
- PRESERVE: user preferences, project context, technical decisions, recurring patterns
- REMOVE: transient debugging, resolved issues, conversational fluff
- MERGE: combine related facts, deduplicate
- Be concise - aim for <500 words
- Use bullet points and sections
- Output markdown only, no explanation.`

export async function loadMemory(agentName: string): Promise<string> {
  const path = getAgentMemoryPath(agentName)
  const file = Bun.file(path)
  if (!(await file.exists())) return ""
  return file.text()
}

export async function appendToMemory(agentName: string, content: string): Promise<void> {
  const path = getAgentMemoryPath(agentName)
  await mkdir(dirname(path), { recursive: true })
  const existing = await Bun.file(path).text().catch(() => "")
  const separator = existing ? "\n\n" : ""
  await Bun.write(path, existing + separator + content)
}

export async function archiveConversation(messages: Message[]): Promise<void> {
  if (messages.length === 0) return
  const path = getArchivePath()
  await mkdir(dirname(path), { recursive: true })
  const lines = messages.map(m => JSON.stringify({ ...m, timestamp: m.timestamp || new Date().toISOString() })).join("\n") + "\n"
  const existing = await Bun.file(path).text().catch(() => "")
  await Bun.write(path, existing + lines)
}

export async function compactMemory(
  agentName: string,
  agentPrompt: string,
  currentMemory: string,
  session: SessionSummary
): Promise<string> {
  const client = getClient()

  const conversationText = session.messages
    .map(m => `${m.role}: ${m.content}`)
    .join("\n\n")

  const artifactsText = session.artifacts.length > 0
    ? `Files modified: ${session.artifacts.join(", ")}`
    : ""

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 2048,
    system: COMPACTION_PROMPT,
    messages: [{
      role: "user",
      content: `## Agent\n${agentName}: ${agentPrompt}\n\n## Current Memory\n${currentMemory || "(empty)"}\n\n## Session\n${conversationText}\n\n${artifactsText}`
    }]
  })

  const content = response.content[0]
  return content.type === "text" ? content.text : currentMemory
}

export async function writeMemory(agentName: string, content: string): Promise<void> {
  const path = getAgentMemoryPath(agentName)
  await mkdir(dirname(path), { recursive: true })
  await Bun.write(path, content)
}
