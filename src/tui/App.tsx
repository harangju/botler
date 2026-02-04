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
  const [statusMessage, setStatusMessage] = useState("")
  const [isExiting, setIsExiting] = useState(false)
  const { messages, toolCalls, streamingText, isLoading, sendMessage, memory, remember, compact } = useChat(currentAgent, setCurrentAgent)

  useInput((input, key) => {
    if (key.ctrl && input === "c") {
      if (isExiting) return
      if (messages.length === 0) {
        exit()
        return
      }
      setIsExiting(true)
      compact().then(() => exit())
    }
  })

  const handleSubmit = useCallback(async (value: string) => {
    const input = value.trim()
    if (!input || isLoading) return

    // Handle commands
    if (input.startsWith("/")) {
      const [cmd, ...args] = input.split(" ")

      switch (cmd) {
        case "/agent":
          if (args[0]) {
            const agent = getAgent(args[0])
            if (agent) setCurrentAgent(agent)
          }
          setInputValue("")
          return

        case "/remember":
          if (args.length > 0) {
            const content = args.join(" ")
            await remember(content)
            setStatusMessage(`Remembered: ${content}`)
            setTimeout(() => setStatusMessage(""), 3000)
          }
          setInputValue("")
          return

        case "/memory":
          if (memory) {
            setStatusMessage(`Memory:\n${memory}`)
          } else {
            setStatusMessage("No memory yet. Use /remember <text> to add.")
          }
          setTimeout(() => setStatusMessage(""), 10000)
          setInputValue("")
          return

        case "/compact":
          compact()
          setInputValue("")
          return
      }
    }

    sendMessage(input)
    setInputValue("")
  }, [isLoading, sendMessage, remember, memory, compact])

  return (
    <Box flexDirection="column" padding={1}>
      <Box marginBottom={1}>
        <Text bold color="cyan">botler</Text>
        <Text dimColor> • </Text>
        <Text color="yellow">@{currentAgent.name}</Text>
        <Text dimColor> • /agent /memory /remember /compact • ctrl+c to exit</Text>
      </Box>

      {statusMessage && (
        <Box marginBottom={1} borderStyle="single" borderColor="gray" paddingX={1}>
          <Text>{statusMessage}</Text>
        </Box>
      )}

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
          placeholder={isExiting ? "Compacting memory..." : (isLoading && !streamingText) ? "Thinking..." : "Type a message..."}
          disabled={isLoading || isExiting}
          showSpinner={isExiting || (isLoading && !streamingText)}
        />
      </Box>
    </Box>
  )
}
