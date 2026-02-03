import type Anthropic from "@anthropic-ai/sdk"

export interface Tool {
  name: string
  description: string
  input_schema: Anthropic.Tool["input_schema"]
  execute: (args: Record<string, unknown>) => Promise<string>
}

const bash: Tool = {
  name: "bash",
  description: "Run a bash command",
  input_schema: {
    type: "object" as const,
    properties: {
      command: { type: "string", description: "The command to run" }
    },
    required: ["command"]
  },
  async execute(args) {
    const proc = Bun.spawn(["bash", "-c", String(args.command)], {
      stdout: "pipe",
      stderr: "pipe"
    })
    const stdout = await new Response(proc.stdout).text()
    const stderr = await new Response(proc.stderr).text()
    return stdout || stderr || "done"
  }
}

const readFile: Tool = {
  name: "read_file",
  description: "Read a file",
  input_schema: {
    type: "object" as const,
    properties: {
      path: { type: "string", description: "Path to the file" }
    },
    required: ["path"]
  },
  async execute(args) {
    const file = Bun.file(String(args.path))
    return await file.text()
  }
}

export const tools: Tool[] = [bash, readFile]

export function getToolSchemas(): Anthropic.Tool[] {
  return tools.map(t => ({
    name: t.name,
    description: t.description,
    input_schema: t.input_schema
  }))
}

export async function executeTool(name: string, args: Record<string, unknown>): Promise<string> {
  const tool = tools.find(t => t.name === name)
  if (!tool) {
    throw new Error(`Unknown tool: ${name}`)
  }
  return tool.execute(args)
}
