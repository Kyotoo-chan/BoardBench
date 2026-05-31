import path from "node:path";
import type {
  ExtensionAPI,
  ExtensionContext,
} from "@earendil-works/pi-coding-agent";

type Mode = "readonly" | "authoring";

const READONLY_BUILTINS = ["read", "grep", "find", "ls"];
const AUTHORING_BUILTINS = [
  "read",
  "grep",
  "find",
  "ls",
  "edit",
  "write",
  "bash",
];

const RESTRICTED_FILES = [
  "README.md",
  "CURRENT.md",
  "AGENTS.md",
  "QUESTIONS.txt",
  "workflow_description.md",
  "requirements.txt",
  "code/evaluation_draft.md",
  "code/evaluation.ipynb",
  "evaluation.ipynb",
];

const RESTRICTED_DIRS = [
  ".pi/extensions",
  "code",
  "code/input",
  "code/outputs",
  "inputs",
  "prompts",
  "outputs",
];

function toAbsolute(cwd: string, repoPath: string): string {
  return path.resolve(cwd, repoPath);
}

function isInsideDirectory(targetPath: string, directoryPath: string): boolean {
  const relative = path.relative(directoryPath, targetPath);
  return (
    relative === "" ||
    (!relative.startsWith("..") && !path.isAbsolute(relative))
  );
}

function isInsideRepo(cwd: string, requestedPath: string): boolean {
  const absoluteRequestedPath = toAbsolute(cwd, requestedPath);
  return isInsideDirectory(absoluteRequestedPath, cwd);
}

function getRequestedPath(
  toolName: string,
  input: unknown,
): string | undefined {
  if (
    toolName === "read" ||
    toolName === "write" ||
    toolName === "edit" ||
    toolName === "ls" ||
    toolName === "find" ||
    toolName === "grep"
  ) {
    const maybePath = (input as { path?: unknown } | undefined)?.path;
    return typeof maybePath === "string" && maybePath.trim()
      ? maybePath
      : undefined;
  }

  return undefined;
}

function normalizeForDisplay(repoPath: string): string {
  return repoPath.replace(/\\/g, "/");
}

export default function boardbenchContextExtension(pi: ExtensionAPI) {
  let mode: Mode = "authoring";

  function getRestrictedPathList(): string[] {
    return [...RESTRICTED_FILES, ...RESTRICTED_DIRS].map(normalizeForDisplay);
  }

  function buildActiveTools(): string[] {
    const extraTools = pi
      .getAllTools()
      .filter((tool) => tool.sourceInfo.source !== "builtin")
      .map((tool) => tool.name);

    const builtins =
      mode === "readonly" ? READONLY_BUILTINS : AUTHORING_BUILTINS;
    return Array.from(new Set([...builtins, ...extraTools]));
  }

  function applyMode(ctx?: ExtensionContext, notify = false): void {
    const activeTools = buildActiveTools();
    pi.setActiveTools(activeTools);

    if (ctx?.hasUI) {
      ctx.ui.setStatus("boardbench", `BoardBench ${mode}`);

      if (notify) {
        const toolLabel =
          mode === "readonly"
            ? READONLY_BUILTINS.join(", ")
            : AUTHORING_BUILTINS.join(", ");
        const scopeLabel =
          mode === "readonly"
            ? "workflow paths only; bash blocked"
            : "full repo authoring; bash allowed";

        ctx.ui.notify(
          `BoardBench ${mode} mode active (${toolLabel}; ${scopeLabel})`,
          "info",
        );
      }
    }
  }

  function isRestrictedPath(cwd: string, requestedPath: string): boolean {
    const absoluteRequestedPath = toAbsolute(cwd, requestedPath);

    const absoluteFiles = RESTRICTED_FILES.map((file) => toAbsolute(cwd, file));
    if (absoluteFiles.includes(absoluteRequestedPath)) {
      return true;
    }

    const absoluteDirs = RESTRICTED_DIRS.map((dir) => toAbsolute(cwd, dir));
    return absoluteDirs.some((dir) =>
      isInsideDirectory(absoluteRequestedPath, dir),
    );
  }

  pi.on("session_start", async (_event, ctx) => {
    applyMode(ctx, true);
  });

  pi.registerCommand("bb-readonly", {
    description:
      "Switch BoardBench extension to restricted readonly workflow mode",
    handler: async (_args, ctx) => {
      mode = "readonly";
      applyMode(ctx, true);
    },
  });

  pi.registerCommand("bb-generate", {
    description:
      "Switch BoardBench extension to restricted generation workflow mode",
    handler: async (_args, ctx) => {
      mode = "readonly";
      applyMode(ctx, true);
    },
  });

  pi.registerCommand("bb-authoring", {
    description:
      "Switch BoardBench extension to full authoring mode (edit/write/bash enabled)",
    handler: async (_args, ctx) => {
      mode = "authoring";
      applyMode(ctx, true);
    },
  });

  pi.registerCommand("bb-status", {
    description: "Show BoardBench extension status",
    handler: async (_args, ctx) => {
      if (mode === "readonly") {
        const paths = getRestrictedPathList().join(", ");
        ctx.ui.notify(
          `BoardBench readonly mode. Restricted workflow paths: ${paths}`,
          "info",
        );
        return;
      }

      ctx.ui.notify(
        "BoardBench authoring mode. Read/edit/write/bash allowed across the repository. Use /bb-readonly or /bb-generate for the restricted workflow mode.",
        "info",
      );
    },
  });

  pi.on("before_agent_start", async (event) => {
    const modeLine =
      mode === "readonly"
        ? "- Current mode is readonly. Do not attempt edit, write, or bash. Stay inside the restricted BoardBench workflow paths."
        : "- Current mode is authoring. You may read, edit, write, and use bash across the repository.";

    const restrictedPaths = getRestrictedPathList()
      .map((entry) => `- ${entry}`)
      .join("\n");

    return {
      systemPrompt:
        event.systemPrompt +
        `\n\n## BoardBench Local Extension\nDefault mode is authoring.\n- Use /bb-readonly or /bb-generate only when the user explicitly wants the restricted BoardBench workflow.\n${modeLine}\n- In readonly mode, prefer the workflow files first: README.md, CURRENT.md, requirements.txt, code/input/, code/outputs/, and the evaluation notebook.\n- If readonly mode is active, do not leave the restricted workflow paths below.\n\nRestricted workflow paths:\n${restrictedPaths}\n`,
    };
  });

  pi.on("tool_call", async (event, ctx) => {
    if (mode === "readonly") {
      if (event.toolName === "bash") {
        return {
          block: true,
          reason:
            "BoardBench readonly mode blocks bash. Use read, grep, find, or ls on the restricted workflow paths instead.",
        };
      }

      if (event.toolName === "write" || event.toolName === "edit") {
        return {
          block: true,
          reason:
            "BoardBench readonly mode blocks edit and write. Use /bb-authoring to return to full repo authoring mode.",
        };
      }
    }

    const requestedPath = getRequestedPath(event.toolName, event.input);
    const usesPathGuard = [
      "read",
      "write",
      "edit",
      "ls",
      "find",
      "grep",
    ].includes(event.toolName);

    if (!usesPathGuard) {
      return undefined;
    }

    if (!requestedPath) {
      return {
        block: true,
        reason:
          mode === "readonly"
            ? `${event.toolName} requires an explicit restricted workflow path, for example requirements.txt, code, code/input, or code/outputs.`
            : `${event.toolName} requires an explicit path inside the repository.`,
      };
    }

    if (mode === "readonly") {
      if (!isRestrictedPath(ctx.cwd, requestedPath)) {
        return {
          block: true,
          reason: `Path "${requestedPath}" is outside the restricted BoardBench workflow allowlist.`,
        };
      }

      return undefined;
    }

    if (!isInsideRepo(ctx.cwd, requestedPath)) {
      return {
        block: true,
        reason: `Path "${requestedPath}" is outside the repository root.`,
      };
    }

    return undefined;
  });
}
