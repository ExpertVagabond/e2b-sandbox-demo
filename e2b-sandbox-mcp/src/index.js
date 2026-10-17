#!/usr/bin/env node
/**
 * E2B Sandbox MCP Server
 *
 * Gives AI agents safe code execution through E2B sandboxes.
 * Each sandbox is isolated (Firecracker microVM), stateful across calls,
 * and automatically cleaned up.
 *
 * Tools:
 *   create-sandbox  — spin up a new sandbox
 *   run-code        — execute code in an existing sandbox (stateful)
 *   run-command     — execute a shell command in a sandbox
 *   upload-file     — write a file into the sandbox
 *   download-file   — read a file from the sandbox
 *   list-sandboxes  — show active sandboxes in this session
 *   kill-sandbox    — destroy a sandbox
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "e2b-sandbox-mcp",
  version: "0.1.0",
});

// Session-scoped sandbox registry
const sandboxes = new Map();
let sandboxCounter = 0;

// Lazy-load E2B SDK (only when first tool is called)
let SandboxClass = null;
let CodeInterpreter = null;

async function getSandboxClass() {
  if (!SandboxClass) {
    const mod = await import("e2b");
    SandboxClass = mod.Sandbox;
  }
  return SandboxClass;
}

async function getCodeInterpreter() {
  if (!CodeInterpreter) {
    try {
      const mod = await import("e2b-code-interpreter");
      CodeInterpreter = mod.Sandbox;
    } catch {
      return null;
    }
  }
  return CodeInterpreter;
}

function getSandbox(id) {
  const entry = sandboxes.get(id);
  if (!entry) throw new Error(`No sandbox with id "${id}". Use list-sandboxes to see active ones.`);
  return entry;
}

// --- Tools ---

server.tool(
  "create-sandbox",
  "Create a new isolated E2B sandbox. Returns a session-local ID to use with other tools.",
  {
    mode: z.enum(["shell", "code-interpreter"]).default("code-interpreter")
      .describe("'shell' = raw sandbox, 'code-interpreter' = stateful code execution"),
    timeout: z.number().min(60).max(3600).default(300)
      .describe("Sandbox lifetime in seconds (default 300)"),
  },
  async ({ mode, timeout }) => {
    if (!process.env.E2B_API_KEY) {
      return { content: [{ type: "text", text: "E2B_API_KEY not set. Get a free key at https://e2b.dev" }] };
    }

    const id = `sbx-${++sandboxCounter}`;
    let sbx;

    if (mode === "code-interpreter") {
      const CI = await getCodeInterpreter();
      if (CI) {
        sbx = await CI.create({ timeoutMs: timeout * 1000 });
      } else {
        const Sbx = await getSandboxClass();
        sbx = await Sbx.create({ timeoutMs: timeout * 1000 });
        mode = "shell";
      }
    } else {
      const Sbx = await getSandboxClass();
      sbx = await Sbx.create({ timeoutMs: timeout * 1000 });
    }

    sandboxes.set(id, { sbx, mode, created: new Date().toISOString() });

    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          id,
          sandbox_id: sbx.sandboxId,
          mode,
          timeout_seconds: timeout,
          message: `Sandbox ready. Use run-${mode === "code-interpreter" ? "code" : "command"} with id "${id}".`,
        }, null, 2),
      }],
    };
  }
);

server.tool(
  "run-code",
  "Execute Python code in a code-interpreter sandbox. State persists between calls.",
  {
    id: z.string().describe("Sandbox ID from create-sandbox"),
    code: z.string().describe("Python code to execute"),
  },
  async ({ id, code }) => {
    const { sbx, mode } = getSandbox(id);
    if (mode !== "code-interpreter") {
      return { content: [{ type: "text", text: "This sandbox is shell-mode. Use run-command instead." }] };
    }

    const execution = await sbx.runCode(code);
    const result = {
      text: execution.text || null,
      stdout: execution.logs?.stdout?.join("") || null,
      stderr: execution.logs?.stderr?.join("") || null,
      error: execution.error ? { name: execution.error.name, value: execution.error.value } : null,
    };

    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }
);

server.tool(
  "run-command",
  "Execute a shell command in a sandbox.",
  {
    id: z.string().describe("Sandbox ID from create-sandbox"),
    command: z.string().describe("Shell command to run"),
  },
  async ({ id, command }) => {
    const { sbx } = getSandbox(id);
    const result = await sbx.commands.run(command);
    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          stdout: result.stdout,
          stderr: result.stderr,
          exit_code: result.exitCode,
        }, null, 2),
      }],
    };
  }
);

server.tool(
  "upload-file",
  "Write content to a file inside the sandbox.",
  {
    id: z.string().describe("Sandbox ID"),
    path: z.string().describe("Absolute path inside the sandbox (e.g. /home/user/data.csv)"),
    content: z.string().describe("File content to write"),
  },
  async ({ id, path, content }) => {
    const { sbx } = getSandbox(id);
    await sbx.files.write(path, content);
    return { content: [{ type: "text", text: `Wrote ${content.length} bytes to ${path}` }] };
  }
);

server.tool(
  "download-file",
  "Read a file from the sandbox.",
  {
    id: z.string().describe("Sandbox ID"),
    path: z.string().describe("Absolute path inside the sandbox"),
  },
  async ({ id, path }) => {
    const { sbx } = getSandbox(id);
    const content = await sbx.files.read(path);
    return { content: [{ type: "text", text: content }] };
  }
);

server.tool(
  "list-sandboxes",
  "List all active sandboxes in this session.",
  {},
  async () => {
    const entries = [];
    for (const [id, { sbx, mode, created }] of sandboxes) {
      entries.push({ id, sandbox_id: sbx.sandboxId, mode, created });
    }
    return {
      content: [{
        type: "text",
        text: entries.length
          ? JSON.stringify(entries, null, 2)
          : "No active sandboxes. Use create-sandbox to start one.",
      }],
    };
  }
);

server.tool(
  "kill-sandbox",
  "Destroy a sandbox and free its resources.",
  {
    id: z.string().describe("Sandbox ID to destroy"),
  },
  async ({ id }) => {
    const { sbx } = getSandbox(id);
    await sbx.kill();
    sandboxes.delete(id);
    return { content: [{ type: "text", text: `Sandbox ${id} destroyed.` }] };
  }
);

// --- Start ---

const transport = new StdioServerTransport();
await server.connect(transport);
