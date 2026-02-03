# Botler

An agent runtime you own.

## Quick Start

```bash
bun install
bun run dev
```

## Commands

| Command | Description |
|---------|-------------|
| `/agent <name>` | Switch to a different agent |
| `/memory` | Show current agent's memory |
| `/remember <text>` | Add something to agent's memory |
| `@agent` | Mention an agent inline |
| `ctrl+c` | Exit |

## Memory

Each agent has persistent memory stored in `~/.botler/agents/{name}/memory.md`.

```bash
# Add to memory via CLI
/remember User prefers TypeScript

# View current memory
/memory
```

Memory is injected into the agent's system prompt. Conversations are ephemeral (not reloaded on restart) but archived to `~/.botler/archive/YYYY-MM-DD.jsonl`.

## Architecture

See [docs/design.md](docs/design.md) for details.
