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

const writeFile: Tool = {
  name: "write_file",
  description: "Write content to a file (creates or overwrites)",
  input_schema: {
    type: "object" as const,
    properties: {
      path: { type: "string", description: "Path to the file" },
      content: { type: "string", description: "Content to write" }
    },
    required: ["path", "content"]
  },
  async execute(args) {
    await Bun.write(String(args.path), String(args.content))
    return "done"
  }
}

const editFile: Tool = {
  name: "edit_file",
  description: "Edit a file by replacing a specific string with new content",
  input_schema: {
    type: "object" as const,
    properties: {
      path: { type: "string", description: "Path to the file" },
      old_string: { type: "string", description: "The exact string to replace" },
      new_string: { type: "string", description: "The replacement string" }
    },
    required: ["path", "old_string", "new_string"]
  },
  async execute(args) {
    const file = Bun.file(String(args.path))
    const content = await file.text()
    const oldStr = String(args.old_string)
    const newStr = String(args.new_string)

    if (!content.includes(oldStr)) {
      throw new Error(`String not found in file: ${oldStr.slice(0, 50)}...`)
    }

    const newContent = content.replace(oldStr, newStr)
    await Bun.write(String(args.path), newContent)
    return "done"
  }
}

const glob: Tool = {
  name: "glob",
  description: "Find files matching a glob pattern",
  input_schema: {
    type: "object" as const,
    properties: {
      pattern: { type: "string", description: "Glob pattern (e.g., '**/*.ts', 'src/**/*.tsx')" }
    },
    required: ["pattern"]
  },
  async execute(args) {
    const g = new Bun.Glob(String(args.pattern))
    const files: string[] = []
    for await (const file of g.scan({ cwd: ".", onlyFiles: true })) {
      files.push(file)
    }
    return files.join("\n") || "no files found"
  }
}

const grep: Tool = {
  name: "grep",
  description: "Search for a pattern in files",
  input_schema: {
    type: "object" as const,
    properties: {
      pattern: { type: "string", description: "Regex pattern to search for" },
      path: { type: "string", description: "File or directory to search in (default: current dir)" }
    },
    required: ["pattern"]
  },
  async execute(args) {
    const pattern = String(args.pattern)
    const searchPath = String(args.path || ".")

    const proc = Bun.spawn(["grep", "-rn", "--include=*.ts", "--include=*.tsx", "--include=*.js", "--include=*.json", "--include=*.md", pattern, searchPath], {
      stdout: "pipe",
      stderr: "pipe"
    })
    const stdout = await new Response(proc.stdout).text()
    const stderr = await new Response(proc.stderr).text()
    return stdout || stderr || "no matches"
  }
}

const ls: Tool = {
  name: "ls",
  description: "List directory contents",
  input_schema: {
    type: "object" as const,
    properties: {
      path: { type: "string", description: "Directory path (default: current dir)" }
    },
    required: []
  },
  async execute(args) {
    const dir = String(args.path || ".")
    const proc = Bun.spawn(["ls", "-la", dir], {
      stdout: "pipe",
      stderr: "pipe"
    })
    const stdout = await new Response(proc.stdout).text()
    const stderr = await new Response(proc.stderr).text()
    return stdout || stderr
  }
}

export const tools: Tool[] = [bash, readFile, writeFile, editFile, glob, grep, ls]

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
