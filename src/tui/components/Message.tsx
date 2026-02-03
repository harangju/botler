import { Box, Text } from "ink"

interface MessageProps {
  role: "user" | "assistant"
  content: string
  streaming?: boolean
}

export function Message({ role, content, streaming }: MessageProps) {
  const isUser = role === "user"

  return (
    <Box marginY={0}>
      <Box width={6}>
        <Text color={isUser ? "green" : "magenta"} bold>
          {isUser ? "You" : "Agent"}
        </Text>
      </Box>
      <Box flexDirection="column" flexGrow={1}>
        <Text wrap="wrap">
          {content}
          {streaming && <Text dimColor>▋</Text>}
        </Text>
      </Box>
    </Box>
  )
}
