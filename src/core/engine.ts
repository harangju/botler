import type Anthropic from "@anthropic-ai/sdk"
import { getClient } from "./client.js"
import { getToolSchemas, executeTool } from "../tools/index.js"
import type { Message, EngineEvent } from "./types.js"

export async function* runAgent(
  messages: Message[],
  model = "claude-sonnet-4-20250514"
): AsyncGenerator<EngineEvent> {
  const client = getClient()
  const tools = getToolSchemas()

  const apiMessages: Anthropic.MessageParam[] = messages.map(m => ({
    role: m.role,
    content: m.content
  }))

  let continueLoop = true

  while (continueLoop) {
    continueLoop = false
    let responseText = ""

    const stream = client.messages.stream({
      model,
      max_tokens: 4096,
      tools,
      messages: apiMessages
    })

    for await (const event of stream) {
      if (event.type === "content_block_delta") {
        if (event.delta.type === "text_delta") {
          responseText += event.delta.text
          yield { type: "text", text: responseText }
        }
      } else if (event.type === "content_block_start") {
        if (event.content_block.type === "tool_use") {
          yield {
            type: "tool_start",
            id: event.content_block.id,
            name: event.content_block.name
          }
        }
      }
    }

    const finalMessage = await stream.finalMessage()

    const toolUseBlocks = finalMessage.content.filter(
      (b): b is Anthropic.ToolUseBlock => b.type === "tool_use"
    )

    if (toolUseBlocks.length > 0) {
      const toolResults: Anthropic.ToolResultBlockParam[] = []

      for (const block of toolUseBlocks) {
        const args = block.input as Record<string, unknown>
        yield { type: "tool_args", id: block.id, args }

        try {
          const result = await executeTool(block.name, args)
          yield { type: "tool_done", id: block.id, result }
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: result
          })
        } catch (err) {
          const error = String(err)
          yield { type: "tool_error", id: block.id, error }
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: `Error: ${error}`,
            is_error: true
          })
        }
      }

      apiMessages.push({
        role: "assistant",
        content: finalMessage.content
      })
      apiMessages.push({
        role: "user",
        content: toolResults
      })

      continueLoop = true
    } else {
      yield { type: "done", response: responseText }
    }
  }
}
