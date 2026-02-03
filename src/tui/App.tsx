import { useState, useCallback } from "react"
import { Box, Text, useInput, useApp } from "ink"
import { Input } from "./components/Input.js"
import { Message } from "./components/Message.js"
import { ToolCall } from "./components/ToolCall.js"
import { useChat } from "./hooks/useChat.js"

export function App() {
  const { exit } = useApp()
  const [inputValue, setInputValue] = useState("")
  const { messages, toolCalls, streamingText, isLoading, sendMessage } = useChat()

  useInput((input, key) => {
    if (key.ctrl && input === "c") {
      exit()
    }
  })

  const handleSubmit = useCallback((value: string) => {
    if (value.trim() && !isLoading) {
      sendMessage(value.trim())
      setInputValue("")
    }
  }, [isLoading, sendMessage])

  return (
    <Box flexDirection="column" padding={1}>
      <Box marginBottom={1}>
        <Text bold color="cyan">botler</Text>
        <Text dimColor> • ctrl+c to exit</Text>
      </Box>

      <Box flexDirection="column" flexGrow={1}>
        {messages.map((msg, i) => (
          <Message key={i} role={msg.role} content={msg.content} />
        ))}

        {toolCalls.map((tool) => (
          <ToolCall
            key={tool.id}
            name={tool.name}
            args={tool.args}
            status={tool.status}
            result={tool.result}
          />
        ))}

        {streamingText && (
          <Message role="assistant" content={streamingText} streaming />
        )}
      </Box>

      <Box marginTop={1}>
        <Input
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSubmit}
          placeholder={isLoading ? "Thinking..." : "Type a message..."}
          disabled={isLoading}
        />
      </Box>
    </Box>
  )
}
