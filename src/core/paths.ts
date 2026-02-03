import { homedir } from "os"
import { join } from "path"

export const BOTLER_DIR = join(homedir(), ".botler")

export function getAgentMemoryPath(agentName: string) {
  return join(BOTLER_DIR, "agents", agentName, "memory.md")
}

export function getArchivePath() {
  const date = new Date().toISOString().split("T")[0]
  return join(BOTLER_DIR, "archive", `${date}.jsonl`)
}
