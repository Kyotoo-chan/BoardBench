import path from "node:path";
import type {
  ExtensionAPI,
  ExtensionContext,
} from "@earendil-works/pi-coding-agent";

type Mode = "readonly" | "generate" | "authoring";

const MODE_ENTRY_TYPE = "boardbench-mode";
const OPEN_SPIEL_GAME = "nine_mens_morris";
const GENERATED_CODE_PATH = `code/outputs/${OPEN_SPIEL_GAME}.py`;

const MINIMAL_START_PROMPT = [
  "Lies code/input/prompt.txt und genau eine vorhandene Regeldatei: code/input/game_rules.txt oder code/input/game_rules.pdf.",
  "Nutze ausschließlich diese Inhalte.",
  "Generiere die Python-Implementation im geforderten Format.",
  `Schreibe genau die vollständige Python-Datei nach ${GENERATED_CODE_PATH}.`,
  `Der Dateiname ist der OpenSpiel-Name für Mühle: ${OPEN_SPIEL_GAME}.py.`,
  "Nutze dafür das write-Tool; schreibe keine anderen Dateien.",
  "Antworte danach nur kurz mit dem Pfad.",
  "Lies keine weiteren Dateien.",
].join("\n");

const READONLY_BUILTINS = ["read", "grep", "find", "ls"];
const GENERATE_BUILTINS = ["read", "grep", "find", "ls", "write"];
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
  "workflow_description.md",
  "TODO.md",
  "boardbench_checkliste.md",
  "boardbench_checkliste_einschaetzung.md",
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
  "checks",
  "inputs",
  "prompts",
  "outputs",
];

const OUTPUT_DIRS = ["code/outputs", "outputs"];

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

function modeFromEntryData(data: unknown): Mode | undefined {
  if (!data || typeof data !== "object") {
    return undefined;
  }

  const mode = (data as { mode?: unknown }).mode;
  return mode === "readonly" || mode === "generate" || mode === "authoring"
    ? mode
    : undefined;
}

export default function boardbenchContextExtension(pi: ExtensionAPI) {
  let mode: Mode = "authoring";

  function getRestrictedPathList(): string[] {
    return [...RESTRICTED_FILES, ...RESTRICTED_DIRS].map(normalizeForDisplay);
  }

  function getBuiltinToolsForMode(): string[] {
    if (mode === "readonly") {
      return READONLY_BUILTINS;
    }

    if (mode === "generate") {
      return GENERATE_BUILTINS;
    }

    return AUTHORING_BUILTINS;
  }

  function getScopeLabel(): string {
    if (mode === "readonly") {
      return "workflow paths only; bash/edit/write blocked";
    }

    if (mode === "generate") {
      return "workflow paths only; write limited to outputs; bash/edit blocked";
    }

    return "full repo authoring; bash allowed";
  }

  function buildActiveTools(): string[] {
    const extraTools = pi
      .getAllTools()
      .filter((tool) => tool.sourceInfo.source !== "builtin")
      .map((tool) => tool.name);

    return Array.from(new Set([...getBuiltinToolsForMode(), ...extraTools]));
  }

  function restoreModeFromSession(ctx: ExtensionContext): void {
    mode = "authoring";

    for (const entry of ctx.sessionManager.getBranch()) {
      if (entry.type !== "custom" || entry.customType !== MODE_ENTRY_TYPE) {
        continue;
      }

      const restoredMode = modeFromEntryData(entry.data);
      if (restoredMode) {
        mode = restoredMode;
      }
    }
  }

  function persistMode(): void {
    pi.appendEntry(MODE_ENTRY_TYPE, { mode });
  }

  function applyMode(ctx?: ExtensionContext, notify = false): void {
    const activeTools = buildActiveTools();
    pi.setActiveTools(activeTools);

    if (ctx?.hasUI) {
      ctx.ui.setStatus("boardbench", `BoardBench ${mode}`);

      if (notify) {
        const toolLabel = getBuiltinToolsForMode().join(", ");
        const scopeLabel = getScopeLabel();

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

  function isOutputPath(cwd: string, requestedPath: string): boolean {
    const absoluteRequestedPath = toAbsolute(cwd, requestedPath);
    const absoluteDirs = OUTPUT_DIRS.map((dir) => toAbsolute(cwd, dir));
    return absoluteDirs.some((dir) =>
      isInsideDirectory(absoluteRequestedPath, dir),
    );
  }

  pi.on("session_start", async (_event, ctx) => {
    restoreModeFromSession(ctx);
    applyMode(ctx, true);
  });

  pi.registerCommand("bb-start", {
    description:
      "Start a fresh restricted BoardBench workflow session with the minimal prompt",
    handler: async (_args, ctx) => {
      if (!ctx.isIdle()) {
        ctx.ui.notify(
          "Wait until the agent is idle before starting a new BoardBench session.",
          "warning",
        );
        return;
      }

      const result = await ctx.newSession({
        parentSession: ctx.sessionManager.getSessionFile(),
        setup: async (session) => {
          session.appendCustomEntry(MODE_ENTRY_TYPE, { mode: "generate" });
          session.appendSessionInfo("boardbench minimal generation");
        },
        withSession: async (replacementCtx) => {
          replacementCtx.ui.setEditorText(MINIMAL_START_PROMPT);
          replacementCtx.ui.notify(
            `New BoardBench generate session ready. Submit the prefilled prompt to write ${GENERATED_CODE_PATH}.`,
            "info",
          );
        },
      });

      if (result.cancelled) {
        ctx.ui.notify("BoardBench start cancelled", "info");
      }
    },
  });

  pi.registerCommand("bb-readonly", {
    description:
      "Switch BoardBench extension to restricted readonly workflow mode",
    handler: async (_args, ctx) => {
      mode = "readonly";
      persistMode();
      applyMode(ctx, true);
    },
  });

  pi.registerCommand("bb-generate", {
    description:
      "Switch BoardBench extension to restricted generation workflow mode",
    handler: async (_args, ctx) => {
      mode = "generate";
      persistMode();
      applyMode(ctx, true);
    },
  });

  pi.registerCommand("bb-authoring", {
    description:
      "Switch BoardBench extension to full authoring mode (edit/write/bash enabled)",
    handler: async (_args, ctx) => {
      mode = "authoring";
      persistMode();
      applyMode(ctx, true);
    },
  });

  pi.registerCommand("bb-status", {
    description: "Show BoardBench extension status",
    handler: async (_args, ctx) => {
      const paths = getRestrictedPathList().join(", ");

      if (mode === "readonly") {
        ctx.ui.notify(
          `BoardBench readonly mode. Restricted workflow paths: ${paths}`,
          "info",
        );
        return;
      }

      if (mode === "generate") {
        ctx.ui.notify(
          `BoardBench generate mode. Restricted workflow paths: ${paths}. Writes are limited to code/outputs/ and outputs/.`,
          "info",
        );
        return;
      }

      ctx.ui.notify(
        "BoardBench authoring mode. Read/edit/write/bash allowed across the repository. Use /bb-readonly or /bb-generate for restricted workflow modes.",
        "info",
      );
    },
  });

  pi.on("before_agent_start", async (event) => {
    const modeLine =
      mode === "readonly"
        ? "- Current mode is readonly. Do not attempt edit, write, or bash. Stay inside the restricted BoardBench workflow paths."
        : mode === "generate"
          ? "- Current mode is generate. Do not attempt edit or bash. Read only restricted workflow paths, and write only under code/outputs/ or outputs/."
          : "- Current mode is authoring. You may read, edit, write, and use bash across the repository.";

    const restrictedPaths = getRestrictedPathList()
      .map((entry) => `- ${entry}`)
      .join("\n");

    return {
      systemPrompt:
        event.systemPrompt +
        `\n\n## BoardBench Local Extension\nDefault mode is authoring.\n- Use /bb-start for a fresh restricted workflow session with the minimal starter prompt.\n- Use /bb-readonly or /bb-generate only when the user explicitly wants the restricted BoardBench workflow.\n${modeLine}\n- In restricted modes, prefer the workflow files first: README.md, CURRENT.md, requirements.txt, code/input/, code/outputs/, checks/, and the evaluation notebook.\n- If a restricted mode is active, do not leave the restricted workflow paths below.\n\nRestricted workflow paths:\n${restrictedPaths}\n`,
    };
  });

  pi.on("tool_call", async (event, ctx) => {
    if (mode === "readonly" || mode === "generate") {
      if (event.toolName === "bash") {
        return {
          block: true,
          reason:
            mode === "generate"
              ? "BoardBench generate mode blocks bash. Use read, grep, find, ls, or write under code/outputs/ or outputs/ instead."
              : "BoardBench readonly mode blocks bash. Use read, grep, find, or ls on the restricted workflow paths instead.",
        };
      }

      if (event.toolName === "edit") {
        return {
          block: true,
          reason: `BoardBench ${mode} mode blocks edit. Use /bb-authoring to return to full repo authoring mode.`,
        };
      }

      if (mode === "readonly" && event.toolName === "write") {
        return {
          block: true,
          reason:
            "BoardBench readonly mode blocks write. Use /bb-generate for restricted output writes or /bb-authoring for full authoring mode.",
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
          mode === "readonly" || mode === "generate"
            ? `${event.toolName} requires an explicit restricted workflow path, for example requirements.txt, code, code/input, or code/outputs.`
            : `${event.toolName} requires an explicit path inside the repository.`,
      };
    }

    if (mode === "readonly" || mode === "generate") {
      if (!isRestrictedPath(ctx.cwd, requestedPath)) {
        return {
          block: true,
          reason: `Path "${requestedPath}" is outside the restricted BoardBench workflow allowlist.`,
        };
      }

      if (mode === "generate" && event.toolName === "write") {
        if (!isOutputPath(ctx.cwd, requestedPath)) {
          return {
            block: true,
            reason:
              "BoardBench generate mode allows write only under code/outputs/ or outputs/.",
          };
        }
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
