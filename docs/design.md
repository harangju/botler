# Botler

*An agent runtime you own*

---

## Vision

**Botler = an agent runtime you own**

Botler isn't an agent—it's the runtime/orchestrator that hosts agents. Think of it like:

```
Botler : Agents :: Docker : Containers
```

| Layer | What Botler manages |
|-------|---------------------|
| Agent lifecycle | Create, configure, run multiple agents with different personas |
| Execution | Docker Sandbox where agent code runs safely |
| Memory | Per-agent memory files, shared context |
| Coordination | @mentions, multi-agent threads, lab meetings |
| Interfaces | Pluggable ways to talk to agents (Slack, CLI, etc.) |
| Workspace | Mounting and exposing storage to agents |

**What agents are:** Just configurations. An agent is a persona (system prompt) + model choice + memory file. Botler handles everything else—running the model, executing tools, managing conversations, coordinating threads.

- Runs wherever you want (your machine, cloud VM, NAS)
- You own it, you control it
- Data lives in your workspace (source of truth, shareable)

**Productization angle:** "Self-hostable but feels like Notion" (think Obsidian's model)

---

## Design Principles

*Borrowed from [NanoClaw](https://github.com/gavrielc/nanoclaw)*

**Small enough to understand.** Keep the core codebase minimal. No microservices, no message queues, no unnecessary abstraction layers. A developer should be able to read and understand the entire agent logic in under an hour.

**Secure by isolation.** Agents run in [Docker Sandboxes](https://www.docker.com/blog/docker-sandboxes-run-claude-code-and-other-coding-agents-unsupervised-but-safely/)—microVM-based isolation stronger than regular containers, designed specifically for AI agents. They can only see what's explicitly mounted. Bash/shell access is safe because commands run inside the sandbox, not on the host.

**Interfaces over apps.** Don't build a monolithic app. Build a core with pluggable interfaces. Want Slack? Plugin. Want CLI? Plugin. Want a web UI? Plugin.

**Plugins over bloat.** Don't bloat the codebase with every integration. Keep core minimal; add capabilities via plugins.

---

## Architecture

**Key insight:** Core is an agent runtime—it manages agents but isn't one. Everything else is a plugin. Workspace is mountable storage.

```
          INTERFACE PLUGINS (outside sandbox)
          ┌───────────────────────────────────────────┐
          │  Server   │  Slack  │  Discord  │   Web   │
          │  (FastAPI)│         │           │         │
          └─────────────────────┬─────────────────────┘
                                │ socket
          ┌─────────────────────▼─────────────────────┐
          │              BOTLER CORE                  │
          │  ┌─────────────────────────────────────┐  │
          │  │  Docker Sandbox (microVM)           │  │
          │  │  ┌───────────────────────────────┐  │  │
          │  │  │  Agent Engine                 │  │  │
          │  │  │  - Agent A (persona, memory)  │  │  │
          │  │  │  - Agent B (persona, memory)  │  │  │
          │  │  │  - Agent C (persona, memory)  │  │  │
          │  │  └───────────────────────────────┘  │  │
          │  │  ┌───────────────────────────────┐  │  │
          │  │  │  Capability Plugins (tools)   │  │  │
          │  │  │  Gmail, Calendar, etc.        │  │  │
          │  │  └───────────────────────────────┘  │  │
          │  └─────────────────────────────────────┘  │
          └─────────────────────┬─────────────────────┘
                                │ mount
          ┌─────────────────────▼─────────────────────┐
          │              WORKSPACE (storage)          │
          │  Local dir  │  NAS  │  Cloud storage      │
          │  ─────────────────────────────────────    │
          │  - files/        (your files)             │
          │  - shared/       (shared context)         │
          │  - agents/*/     (config, memory)         │
          │  - conversations/ (thread history)        │
          └─────────────────────┬─────────────────────┘
                                │
          ┌─────────────────────▼─────────────────────┘
          │          FILE INTERFACES (plugins)        │
          │   SSH  │  SFTP  │  Web UI  │  (or none)   │
          └───────────────────────────────────────────┘
```

**Key decisions:**
- **Two plugin types:** Interface plugins run outside sandbox (Server, Slack, etc.). Capability plugins run inside sandbox as agent tools (Gmail, Calendar).
- **Server (FastAPI) handles routing.** Webhooks, auth, request routing—all outside sandbox. Communicates with sandbox via socket.
- **Docker Sandbox for execution.** MicroVM-based isolation (stronger than containers) designed for AI agents running untrusted code.
- **Workspace is external storage.** Mount from anywhere: local directory, NAS, cloud storage. Core is stateless.
- **File interfaces are optional.** If you mount the workspace directly (NAS, local), you don't need them. Use your normal tools (VS Code, Obsidian, Finder).
- **API keys via environment variables.** Injected into sandbox at start, never stored in workspace.

**CLI manages sandbox lifecycle.** The `botler` CLI handles starting/stopping sandboxes:

```bash
botler start       # creates sandbox, mounts workspace
botler stop        # shuts down sandbox
botler chat        # starts sandbox if needed, attaches interactive session
botler run "..."   # one-shot command inside sandbox
```

**CLI-only mode:** `botler chat` attaches directly to sandbox—no server needed. For network interfaces (Slack, web), the server runs alongside.

**Sandbox lifecycle:**

| Event | What happens |
|-------|--------------|
| `botler start` | Creates Docker Sandbox, mounts workspace, starts core |
| While running | Sandbox stays up, handles requests |
| `botler stop` | Graceful shutdown, sandbox removed |

One sandbox per workspace. Multiple workspaces = multiple sandboxes.

---

## UX Model

Two modes of interaction, both valid:

| Mode | How it works | Interface |
|------|--------------|-----------|
| **Direct** | You edit files, browse workspace | Your normal tools (mount workspace) or file interface plugin |
| **Agentic** | You chat with agents, they act | Conversation interface (Slack, CLI, web) |

**Simplest setup:** Mount the workspace on your computer (local dir or NAS share). Edit files with VS Code, Obsidian, whatever. Chat with agents via CLI. No plugins needed.

### Conversation Semantics

Regardless of which conversation interface, works like Slack/Discord:
- **Channels/threads**: Contexts for focused discussions
- **@mentions**: Call out specific agents (`@sinan what do you think?`)
- **DMs**: Private conversation with one agent
- **Group modes**: Multi-agent discussions, lab meetings

What you can do:
- @mention agents to get their perspective
- Start group threads (all agents participate)
- Create new agents (name, persona, values)
- Agents can @mention each other
- Agents work on goals, surface results, then stop (goal-oriented, not noisy)
- Invite real people to collaborate

### File References

Conversation can reference files (like Claude Code):
- Mention a file, it's pulled into context
- Agents can read/write/edit
- Changes appear in workspace immediately

---

## Multi-Agent Model

Multiple AgentEngine instances, each with:

| Component | Purpose |
|-----------|---------|
| **Persona** | System prompt defining values, what they care about |
| **Memory** | Individual memory file (past work, their positions) |
| **Shared access** | Same workspace, same tools, same sandbox |

### Example: Research Group

One configuration of agents (see [research.md](research.md)):

| Agent | Values | Pushes for |
|-------|--------|------------|
| **Sinan** | Impact, S-class venues | Big ideas, high-stakes bets |
| **Dean** | Rigor, ecological validity | Clean methods, honest limitations |
| **Critic** | Novelty | What's actually new? Has this been done? |

- Lab meetings = group threads where they debate
- Lab notebooks = markdown files in shared workspace
- You're the PI—set direction, break ties, make final calls

Not a separate "app"—just a set of agents with specific personas.

---

## Plugins

### Interface Plugins (outside sandbox)

Run alongside the server. Handle external communication, route messages to agents.

| Type | Options | Notes |
|------|---------|-------|
| Chat | Slack, Discord, CLI, Web | At least one needed |
| Files | SSH, SFTP, Web file browser | Optional—use native mount instead |
| Voice (later) | STT/TTS integration | |

### Capability Plugins (inside sandbox)

Run as agent tools. Give agents new abilities.

| Capability | Options |
|------------|---------|
| Calendar | Built-in, macOS native (EventKit), Google Calendar |
| Tasks | Built-in, macOS Reminders, Todoist |
| Email | Gmail, Outlook, etc. |
| External sync | Google Drive, Dropbox |

Capability plugins need network egress from sandbox to call external APIs.

### Installing Plugins

```bash
botler plugin add slack
botler plugin add gmail
botler plugin add calendar
```

Plugins are Python packages with a standard structure. Install what you need, skip what you don't.

---

## Stack Choices

### Agent Engine

**Decision: pydantic-ai + Claude Agent SDK (both)**

| Framework | Use case |
|-----------|----------|
| [pydantic-ai](https://github.com/pydantic/pydantic-ai) | Base layer. Model-agnostic, clean tool definition, Sequoia-backed. |
| [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) | Claude-specific features (extended thinking, computer use, etc.) |

The `AgentEngine` protocol abstracts over both—swap implementations per agent as needed.

**Tools to implement (~200 lines):**

| Tool | Purpose |
|------|---------|
| `read_file` | Read file contents |
| `write_file` | Write/create file |
| `edit_file` | String replacement edit |
| `ls` | List directory |
| `bash` | Execute shell command |
| `glob` | Pattern-based file search |
| `grep` | Content search |

**Agent engine interface:**
```python
@dataclass
class AgentContext:
    thread_id: str                    # conversation thread
    user_id: str                      # who's talking
    history: list[Message]            # conversation so far
    referenced_files: list[str]       # files pulled into context
    workspace_path: str               # root of workspace

@dataclass
class AgentResult:
    response: str                     # agent's reply
    files_modified: list[str]         # what changed
    tool_calls: list[ToolCall]        # for transparency/logging
    error: str | None                 # if something failed

class AgentEngine(Protocol):
    async def run(self, prompt: str, context: AgentContext) -> AgentResult: ...

class PydanticEngine:
    def __init__(self, persona: str, memory_path: str, model: str = "anthropic:claude-sonnet-4-20250514"):
        self.agent = Agent(model, system_prompt=persona, tools=[...])
        self.memory_path = memory_path
```

### Agent Creation

| Method | How | When |
|--------|-----|------|
| **Config file** | `agents/sinan/config.yaml` | MVP |
| **CLI** | `botler agent create --name sinan --persona "..."` | MVP |
| **Chat** | `@botler create an agent named Sinan who values impact` | Later |

```yaml
# agents/sinan/config.yaml
name: Sinan
model: anthropic:claude-sonnet-4-20250514
persona: |
  You are Sinan. You value impact and S-class venues.
  Push for big ideas and high-stakes bets.
```

### Execution Runtime

**Decision: [Docker Sandbox](https://www.docker.com/blog/docker-sandboxes-run-claude-code-and-other-coding-agents-unsupervised-but-safely/)** — microVM-based isolation designed for AI coding agents.

| Feature | Docker Sandbox | Regular Docker |
|---------|----------------|----------------|
| Isolation | Kernel + microVM | Kernel namespaces only |
| Security | Hardware-enforced | OS-enforced |
| Use case | Untrusted agent code | Trusted applications |

Works on macOS, Linux, and Windows (via WSL2). One sandbox per workspace.

### Storage

**Workspace is external, mountable storage.** Core doesn't care where it lives:

| Option | Use case |
|--------|----------|
| Local directory | Simplest, single machine |
| NAS (Synology, TrueNAS) | Home server, multi-device access, redundancy |
| Cloud storage (Hetzner, S3) | Cloud deployment |

Files for everything:
- Agent memory → markdown files
- Conversation history → markdown/json per thread
- Workspace state → filesystem itself

**Workspace structure:**
```
workspace/
  agents/
    sinan/
      config.yaml       # persona, model
      memory.md         # individual memory
    dean/
      config.yaml
      memory.md
  conversations/
    {thread-id}/
      messages.jsonl    # append-only log
      metadata.json     # participants, created, title
  files/                # user's actual files
  shared/               # shared context (lab notes, etc.)
```

**Direct file access:** If you mount the workspace on your computer (NAS share, local dir), you can edit files directly with your normal tools. No file interface plugin needed—just use VS Code, Obsidian, Finder, etc.

### Server

**FastAPI** — runs **outside** sandbox as part of interface layer:
- Receives webhooks (Slack, Discord)
- Handles auth, routing, rate limiting
- Communicates with sandbox via Unix socket or exposed port

**Optional for MVP.** CLI-only mode doesn't need a server—`botler chat` attaches directly to sandbox.

### Schemas

**messages.jsonl** — one JSON object per line:
```json
{"role": "user", "content": "...", "timestamp": "...", "user_id": "..."}
{"role": "assistant", "content": "...", "timestamp": "...", "agent_id": "sinan", "tool_calls": [...]}
```

**memory.md** — free-form markdown. Agent reads/writes as needed. No strict schema.

**metadata.json** — thread metadata:
```json
{"thread_id": "...", "participants": ["sinan", "dean"], "created": "...", "title": "..."}
```

### @Mention Mechanics

1. Parse incoming message for `@agentname` patterns
2. Route to matched agent (or all agents if `@all`)
3. Agent response is also parsed for @mentions → chains to next agent
4. No mention in group context = round-robin or broadcast

For Slack/Discord: use native mention parsing. For CLI: regex parse.

### Voice (Later)

- **STT**: Moonshine (on-device) + Deepgram/Groq fallback
- **TTS**: Chatterbox (on-device, voice cloning)

See [voice.md](voice.md) for full voice architecture.

---

## Build Order

| Step | What you build | Result |
|------|----------------|--------|
| 1. Core | Single agent + workspace + Docker Sandbox | One agent works |
| 2. First interface | CLI chat or Slack | You can chat with it |
| 3. Multi-agent | Multiple personas, memory files, @mentions | Agents can debate |
| 4. More interfaces | As needed | Expand reach |
| 5. Capabilities | Calendar, email, etc. | Plugins add tools |
| 6. File interfaces (optional) | SSH, web UI | Remote file access if needed |

Note: File interfaces are optional if you mount the workspace directly.

---

## Why Build Fresh (Not Extend NanoClaw)

[NanoClaw](https://github.com/gavrielc/nanoclaw) is excellent. We borrow its philosophy:
- Sandbox isolation model
- "Small enough to understand"
- Plugins over bloat

But NanoClaw's core assumption is **one agent per context**. Botler needs **multiple agents sharing a workspace**—they debate, @mention each other, have distinct personas.

Extending NanoClaw to support this would mean rearchitecting its core. That's building fresh with extra baggage.

**Decision:** Build fresh. Borrow philosophy, not code.

---

## Security Model

| Layer | Protection |
|-------|------------|
| Docker Sandbox (microVM) | Agents run in hardware-isolated microVMs, not just containers |
| Filesystem mounting | Agents can only see the mounted workspace—nothing else on host |
| Shell sandboxing | Bash commands execute inside sandbox, not on host |
| Per-workspace isolation | Each workspace has its own sandbox |

**What's protected:** Host OS, other directories, SSH keys, credentials—invisible and untouchable.

**What's exposed (by design):** The mounted workspace. Agents need to read/write files there.

**Pitch:** "The power of autonomous agents, with security you can trust—because agents run in microVM sandboxes, not on your system."

---

## Productization Path

1. **Personal tool** (you use it)
2. **Open source** (builds community, gets feedback)
3. **Hosted version** for non-technical users (the business)
4. **Team tier** with sharing, permissions

The "own your data" crowd won't pay much. The "I want Notion but private and AI-native" crowd will.

---

## Multi-Agent Coordination

| Mode | Who speaks | Trigger |
|------|------------|---------|
| **@mention** | Only the mentioned agent | `@sinan what do you think?` |
| **DM** | One agent only | Private thread with agent |
| **Lab meeting** | All agents, round-robin | `@all` or `/lab-meeting` |

In lab meeting mode:
1. User posts prompt
2. Each agent responds in sequence (order configurable)
3. Agents can @mention each other to trigger follow-ups
4. Continues until natural stop or user ends it

---

## Open Questions

- How do scheduled jobs/background tasks work?
- How do agents get assigned goals? How do they report back?
- Permission model when people are invited?
- Voice interface design (conversation interface plugin)
