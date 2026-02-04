import { useState, useCallback, useEffect, useRef } from "react"
import { runAgent } from "../../core/engine.js"
import type { Message, ToolCall } from "../../core/types.js"
import { defaultAgent, type Agent } from "../../agents/index.js"
import { parseMention, extractMention } from "../../core/mentions.js"
import { loadMemory, appendToMemory, archiveConversation, compactMemory, writeMemory } from "../../core/storage.js"

const MAX_CHAIN_DEPTH = 5

export function useChat(
  agent: Agent = defaultAgent,
  onAgentChange?: (agent: Agent) => void
) {
  const [messages, setMessages] = useState<Message[]>([])
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([])
  const [streamingText, setStreamingText] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [memory, setMemory] = useState("")
  const [artifacts, setArtifacts] = useState<string[]>([])
  const messagesRef = useRef<Message[]>([])
  const artifactsRef = useRef<string[]>([])
  const agentRef = useRef(agent)
  const memoryRef = useRef(memory)

  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

  useEffect(() => {
    artifactsRef.current = artifacts
  }, [artifacts])

  useEffect(() => {
    agentRef.current = agent
  }, [agent])

  useEffect(() => {
    memoryRef.current = memory
  }, [memory])

  useEffect(() => {
    loadMemory(agent.name).then(setMemory)
  }, [agent.name])

  useEffect(() => {
    return () => {
      if (messagesRef.current.length > 0) {
        archiveConversation(messagesRef.current)
      }
    }
  }, [])

  const remember = useCallback(async (content: string) => {
    await appendToMemory(agent.name, content)
    const updated = await loadMemory(agent.name)
    setMemory(updated)
  }, [agent.name])

  const compact = useCallback(async () => {
    if (messages.length === 0) return

    const toolId = `compact-${Date.now()}`
    const toolCall: ToolCall = {
      id: toolId,
      name: "compact_memory",
      args: { agent: agent.name, messages: messages.length, artifacts: artifacts.length },
      status: "running"
    }
    setToolCalls([toolCall])

    try {
      const newMemory = await compactMemory(
        agent.name,
        agent.systemPrompt,
        memory,
        { messages, artifacts, agent: agent.name }
      )
      await writeMemory(agent.name, newMemory)
      setMemory(newMemory)
      setToolCalls([{ ...toolCall, status: "done", result: "Memory compacted" }])
    } catch (err) {
      setToolCalls([{ ...toolCall, status: "error", result: String(err) }])
    }
  }, [agent.name, agent.systemPrompt, memory, messages, artifacts])

  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true)
    setStreamingText("")
    setToolCalls([])

    const { agent: mentionedAgent, content: messageContent } = parseMention(content)
    let currentAgent = mentionedAgent || agent

    if (mentionedAgent) {
      onAgentChange?.(mentionedAgent)
    }

    if (!messageContent.trim()) {
      setIsLoading(false)
      return
    }

    const userMessage: Message = { role: "user", content: messageContent, timestamp: new Date().toISOString() }
    let currentMessages = [...messages, userMessage]
    setMessages(currentMessages)

    let chainDepth = 0

    while (chainDepth < MAX_CHAIN_DEPTH) {
      chainDepth++

      const currentToolCalls: ToolCall[] = []
      let responseText = ""

      for await (const event of runAgent(currentMessages, currentAgent, memory)) {
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
              if (tc.name === "write_file" || tc.name === "edit_file") {
                const path = tc.args.path as string
                if (path) setArtifacts(prev => [...prev, path])
              }
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
            responseText = event.response
            if (responseText) {
              const assistantMessage: Message = {
                role: "assistant",
                content: responseText,
                agentName: currentAgent.name,
                timestamp: new Date().toISOString()
              }
              currentMessages = [...currentMessages, assistantMessage]
              setMessages(currentMessages)
            }
            setStreamingText("")
            break
        }
      }

      const { agent: nextAgent } = extractMention(responseText)
      if (nextAgent && nextAgent.name !== currentAgent.name) {
        currentAgent = nextAgent
        onAgentChange?.(nextAgent)
        setToolCalls([])
      } else {
        break
      }
    }

    setIsLoading(false)
  }, [messages, agent, onAgentChange, memory])

  return {
    messages,
    toolCalls,
    streamingText,
    isLoading,
    sendMessage,
    memory,
    remember,
    compact
  }
}
