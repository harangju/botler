import { Box, Text } from "ink"
import Spinner from "ink-spinner"

const TOOL_ICONS: Record<string, string> = {
  bash: "$",
  read_file: "→",
  write_file: "←",
  edit_file: "~",
  glob: "*",
  grep: "?",
  ls: "#",
  compact_memory: "◆",
}

interface ToolCallProps {
  name: string
  args: Record<string, unknown>
  status: "running" | "done" | "error"
  result?: string
}

function getSummary(name: string, args: Record<string, unknown>): string {
  if (name === "bash" && args.command) {
    const cmd = String(args.command)
    return cmd.length > 50 ? cmd.slice(0, 47) + "..." : cmd
  }
  if (["read_file", "write_file", "edit_file"].includes(name) && args.path) {
    return String(args.path)
  }
  if (name === "glob" && args.pattern) {
    return String(args.pattern)
  }
  if (name === "grep" && args.pattern) {
    return String(args.pattern)
  }
  if (name === "ls") {
    return String(args.path || ".")
  }
  if (name === "compact_memory") {
    return `${args.messages} messages, ${args.artifacts} artifacts`
  }
  return JSON.stringify(args).slice(0, 40)
}

function getResultSummary(name: string, result?: string): string {
  if (!result) return ""
  if (name === "bash") {
    const trimmed = result.trim()
    return trimmed.length > 30 ? trimmed.slice(0, 27) + "..." : trimmed || "done"
  }
  if (["read_file", "glob", "grep", "ls"].includes(name)) {
    const lines = result.trim().split("\n").length
    return `${lines} lines`
  }
  if (["write_file", "edit_file", "compact_memory"].includes(name)) {
    return "done"
  }
  return ""
}

export function ToolCall({ name, args, status, result }: ToolCallProps) {
  const icon = TOOL_ICONS[name] || ">"
  const summary = getSummary(name, args)
  const resultSummary = getResultSummary(name, result)

  return (
    <Box>
      <Box width={4}>
        {status === "running" ? (
          <Text color="yellow"><Spinner type="dots" /></Text>
        ) : status === "error" ? (
          <Text color="red">✗</Text>
        ) : (
          <Text color="green">✓</Text>
        )}
      </Box>
      <Text dimColor>{icon} </Text>
      <Text>{summary}</Text>
      {resultSummary && (
        <Text dimColor> → {resultSummary}</Text>
      )}
    </Box>
  )
}
