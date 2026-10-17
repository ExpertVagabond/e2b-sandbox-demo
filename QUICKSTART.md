# E2B Quick Start — Do This Before Monday 1:30 PM

**Time needed: 5 minutes**

## Step 1: Sign up (free, GitHub OAuth)

1. Go to https://e2b.dev and click Sign Up
2. Authenticate with GitHub
3. Copy your API key from the dashboard

## Step 2: Set the key

```bash
export E2B_API_KEY=e2b_...your_key...
```

## Step 3: Run the sandbox demo

```bash
cd "/Volumes/Virtual Server/projects/e2b-interview-prep"
.venv/bin/python3 demo_sandbox.py
```

This creates a sandbox, runs commands, writes/reads files, checks isolation, and destroys it. Takes ~30 seconds.

## Step 4: Run the code interpreter demo

```bash
.venv/bin/python3 demo_code_interpreter.py
```

This shows stateful code execution (the key differentiator), error recovery, file generation, and runtime package installs.

## Step 5 (optional): Test the MCP server

```bash
cd e2b-sandbox-mcp
E2B_API_KEY=e2b_... claude mcp add --transport stdio e2b-sandbox -s user -- node "$(pwd)/src/index.js"
```

Then in Claude Code, ask it to "create an E2B sandbox and run some Python."

## What you can say on the call

After running these:
- "I spun up an E2B sandbox this week, ran code in it, tested the isolation"
- "I built a small MCP server that wraps E2B — gives any MCP agent access to sandboxes"
- "The cold start was [X seconds], command latency was [Y ms]"
- "State persisting between run_code calls is the real differentiator — agents need that"
- "The code-interpreter SDK is the agent-facing product; the base SDK is for DevOps"
