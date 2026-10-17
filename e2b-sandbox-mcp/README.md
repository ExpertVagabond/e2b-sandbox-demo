# e2b-sandbox-mcp

MCP server that gives AI agents safe code execution through [E2B](https://e2b.dev) sandboxes.

Built as a companion to E2B's SDKs — wraps sandbox lifecycle and code execution in the MCP tool protocol so any MCP-compatible agent (Claude, Cursor, Windsurf) can spin up isolated environments on demand.

## Why this exists

E2B provides the isolation layer agents need to run untrusted code safely. But most agent frameworks talk MCP, not E2B's SDK directly. This bridge lets an agent:

1. **Create** a sandbox (Firecracker microVM, ~2s cold start)
2. **Run code** with state preserved between calls
3. **Read/write files** inside the sandbox
4. **Destroy** the sandbox when done — no leaked resources

## Tools

| Tool | Description |
|------|-------------|
| `create-sandbox` | Spin up a new sandbox (shell or code-interpreter mode) |
| `run-code` | Execute Python in a code-interpreter sandbox (stateful) |
| `run-command` | Run a shell command in any sandbox |
| `upload-file` | Write content to a file inside the sandbox |
| `download-file` | Read a file from the sandbox |
| `list-sandboxes` | Show active sandboxes in this session |
| `kill-sandbox` | Destroy a sandbox |

## Setup

```bash
npm install
export E2B_API_KEY=e2b_...  # Free at https://e2b.dev
```

### Add to Claude Code
```bash
claude mcp add --transport stdio e2b-sandbox -s user -- node /path/to/e2b-sandbox-mcp/src/index.js
```

## Architecture

```
Agent (Claude, etc.)
  ↓ MCP (JSON-RPC over stdio)
e2b-sandbox-mcp
  ↓ E2B SDK (HTTPS)
E2B Cloud (Firecracker microVMs)
```

Each sandbox is a full Linux VM. Code runs in the sandbox, not on your machine. State persists between `run-code` calls within the same sandbox — the agent can build up context across multiple steps.

## License

MIT
