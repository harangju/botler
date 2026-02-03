import { useState, useCallback } from "react"
import { runAgent } from "../../core/engine.js"
import type { Message, ToolCall } from "../../core/types.js"
import { defaultAgent, type Agent } from "../../agents/index.js"

export function useChat(agent: Agent = defaultAgent) {
  const [messages, setMessages] = useState<Message[]>([])
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([])
  const [streamingText, setStreamingText] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true)
    setStreamingText("")
    setToolCalls([])

    const userMessage: Message = { role: "user", content }
    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)

    const currentToolCalls: ToolCall[] = []

    for await (const event of runAgent(updatedMessages, agent)) {
      switch (event.type) {
        case "text":
          setStreamingText(event.text)
          break

        case "tool_start":
          currentToolCalls.push({
            id: event.id,
            name: event.name,
            args: {},
            status: "running"
          })
          setToolCalls([...currentToolCalls])
          break

        case "tool_args": {
          const tc = currentToolCalls.find(t => t.id === event.id)
          if (tc) {
            tc.args = event.args
            setToolCalls([...currentToolCalls])
          }
          break
        }

        case "tool_done": {
          const tc = currentToolCalls.find(t => t.id === event.id)
          if (tc) {
            tc.status = "done"
            tc.result = event.result
            setToolCalls([...currentToolCalls])
          }
          break
        }

        case "tool_error": {
          const tc = currentToolCalls.find(t => t.id === event.id)
          if (tc) {
            tc.status = "error"
            tc.result = event.error
            setToolCalls([...currentToolCalls])
          }
          break
        }

        case "done":
          if (event.response) {
            setMessages(prev => [...prev, { role: "assistant", content: event.response, agentName: agent.name }])
          }
          setStreamingText("")
          break
      }
    }

    setIsLoading(false)
  }, [messages, agent])

  return {
    messages,
    toolCalls,
    streamingText,
    isLoading,
    sendMessage
  }
}
