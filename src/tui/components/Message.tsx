import { Box, Text } from "ink"

interface MessageProps {
  role: "user" | "assistant"
  content: string
  name?: string
  streaming?: boolean
}

const LABEL_WIDTH = 8

export function Message({ role, content, name, streaming }: MessageProps) {
  const isUser = role === "user"
  const label = isUser ? "You" : (name || "bot")
  const paddedLabel = label.padStart(LABEL_WIDTH)

  return (
    <Box marginY={0}>
      <Text color={isUser ? "green" : "magenta"} bold>
        {paddedLabel}
      </Text>
      <Text> </Text>
      <Box flexDirection="column" flexGrow={1}>
        <Text wrap="wrap">
          {content}
          {streaming && <Text dimColor>▋</Text>}
        </Text>
      </Box>
    </Box>
  )
}
