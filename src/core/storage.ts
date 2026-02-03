import { mkdir } from "fs/promises"
import { dirname } from "path"
import { getAgentMemoryPath, getArchivePath } from "./paths.js"
import type { Message } from "./types.js"

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
