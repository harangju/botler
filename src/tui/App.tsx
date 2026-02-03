import { useState, useCallback } from "react"
import { Box, Text, useInput, useApp } from "ink"
import { Input } from "./components/Input.js"
import { Message } from "./components/Message.js"
import { ToolCall } from "./components/ToolCall.js"
import { useChat } from "./hooks/useChat.js"
import { defaultAgent, getAgent } from "../agents/index.js"

export function App() {
  const { exit } = useApp()
  const [inputValue, setInputValue] = useState("")
  const [currentAgent, setCurrentAgent] = useState(defaultAgent)
  const { messages, toolCalls, streamingText, isLoading, sendMessage } = useChat(currentAgent, setCurrentAgent)

  useInput((input, key) => {
    if (key.ctrl && input === "c") {
      exit()
    }
  })

  const handleSubmit = useCallback((value: string) => {
    if (!value.trim() || isLoading) return

    // Handle /agent command
    if (value.startsWith("/agent")) {
      const parts = value.split(" ")
      if (parts.length === 1) {
        // List agents
        return
      }
      const agentName = parts[1]
      const agent = getAgent(agentName)
      if (agent) {
        setCurrentAgent(agent)
      }
      setInputValue("")
      return
    }

    sendMessage(value.trim())
    setInputValue("")
  }, [isLoading, sendMessage])

  return (
    <Box flexDirection="column" padding={1}>
      <Box marginBottom={1}>
        <Text bold color="cyan">botler</Text>
        <Text dimColor> • </Text>
        <Text color="yellow">@{currentAgent.name}</Text>
        <Text dimColor> • /agent [name] to switch • ctrl+c to exit</Text>
      </Box>

      <Box flexDirection="column" flexGrow={1}>
        {messages.map((msg, i) => (
          <Message key={i} role={msg.role} content={msg.content} name={msg.agentName} />
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
          <Message role="assistant" content={streamingText} name={currentAgent.name} streaming />
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
