#!/usr/bin/env python3
"""
Phi-3 Autonomous Coding Agent
A fully autonomous terminal coding agent powered by local Phi-3 via Ollama.
Designed for coding, file operations, and controlled tool execution.

WARNING: This agent can run shell commands and download files.
Use only on systems and targets you own or have explicit permission for.
Unauthorized scanning, exploitation, or attacks are illegal.
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from openai import OpenAI
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Confirm
except ImportError:
    print("Missing dependencies. Run: pip install -r requirements.txt")
    sys.exit(1)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
MODEL_NAME = os.getenv("PHI3_MODEL", "phi3:latest")
MAX_ITERATIONS = 25
WORKING_DIR = Path.cwd()

console = Console()

DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r"mkfs",
    r"dd\s+if=",
    r":\(\)\{\s*:\|:&\s*\};:",
    r"chmod\s+-R\s+777\s+/",
    r"chown\s+-R\s+.*\s+/",
    r">\s*/dev/sd",
    r"curl.*\|.*sh",
    r"wget.*\|.*sh",
    r"curl.*\|.*bash",
    r"wget.*\|.*bash",
]

SYSTEM_PROMPT = """You are an elite autonomous coding agent running locally with Phi-3.
You help the user write, edit, debug, and manage code. You can also run shell commands and download tools when needed.

You have these tools available:

1. read_file(path) - Read the content of a file
2. write_file(path, content) - Write or overwrite a file
3. edit_file(path, old_text, new_text) - Replace text in a file
4. list_dir(path=".") - List files and directories
5. run_shell(command) - Execute a shell command and return output
6. search_files(pattern, path=".") - Search for text pattern in files (grep-like)
7. download_file(url, save_path) - Download a file from URL
8. finish(summary) - Call this when the task is fully completed

Rules:
- Always think step by step.
- Prefer small, safe changes.
- When using tools, output ONLY valid JSON in this exact format:

```json
{
  "tool": "tool_name",
  "args": {
    "param1": "value1"
  }
}
```

- You can call only ONE tool per response.
- After receiving tool results, continue reasoning and call the next tool if needed.
- When the entire task is done, call the "finish" tool with a short summary.
- Be careful with destructive commands.
- Never scan or attack systems without explicit permission from the user.
- You are running in autonomous mode, so keep going until the task is complete or you hit a hard limit.

Current working directory: {working_dir}
Current time: {current_time}
"""


def read_file(path: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Error: File not found: {p}"
        if p.stat().st_size > 500_000:
            return f"Error: File too large ({p.stat().st_size} bytes). Max 500KB."
        content = p.read_text(encoding="utf-8", errors="replace")
        return f"=== Content of {p} ===\n{content}"
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to {p}"
    except Exception as e:
        return f"Error writing file: {e}"


def edit_file(path: str, old_text: str, new_text: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Error: File not found: {p}"
        content = p.read_text(encoding="utf-8", errors="replace")
        if old_text not in content:
            return "Error: The old_text was not found in the file."
        new_content = content.replace(old_text, new_text, 1)
        p.write_text(new_content, encoding="utf-8")
        return f"Successfully edited {p}"
    except Exception as e:
        return f"Error editing file: {e}"


def list_dir(path: str = ".") -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Error: Path not found: {p}"
        items = []
        for item in sorted(p.iterdir()):
            kind = "DIR " if item.is_dir() else "FILE"
            size = f" ({item.stat().st_size} bytes)" if item.is_file() else ""
            items.append(f"{kind}  {item.name}{size}")
        return f"Contents of {p}:\n" + "\n".join(items) if items else f"{p} is empty."
    except Exception as e:
        return f"Error listing directory: {e}"


def is_dangerous(command: str) -> bool:
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return True
    return False


def run_shell(command: str) -> str:
    if is_dangerous(command):
        console.print(Panel(
            f"[bold red]DANGEROUS COMMAND DETECTED[/bold red]\n\n{command}\n\n"
            "This command matches a high-risk pattern.",
            title="Safety Check",
            border_style="red"
        ))
        if not Confirm.ask("Do you really want to execute this command?", default=False):
            return "User rejected the dangerous command."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(WORKING_DIR)
        )
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        output += f"\nExit code: {result.returncode}"
        return output.strip() or "Command executed with no output."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 120 seconds."
    except Exception as e:
        return f"Error running command: {e}"


def search_files(pattern: str, path: str = ".") -> str:
    try:
        p = Path(path).expanduser().resolve()
        matches = []
        for file in p.rglob("*"):
            if file.is_file() and file.stat().st_size < 200_000:
                try:
                    content = file.read_text(encoding="utf-8", errors="ignore")
                    for i, line in enumerate(content.splitlines(), 1):
                        if pattern.lower() in line.lower():
                            matches.append(f"{file}:{i}: {line.strip()[:120]}")
                            if len(matches) >= 40:
                                break
                except Exception:
                    continue
            if len(matches) >= 40:
                break
        if not matches:
            return f"No matches found for '{pattern}'"
        return f"Found {len(matches)} matches:\n" + "\n".join(matches)
    except Exception as e:
        return f"Error searching: {e}"


def download_file(url: str, save_path: str) -> str:
    try:
        import httpx
        p = Path(save_path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        console.print(f"[cyan]Downloading:[/cyan] {url}")
        with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as response:
            response.raise_for_status()
            with open(p, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
        size = p.stat().st_size
        return f"Successfully downloaded to {p} ({size} bytes)"
    except Exception as e:
        return f"Error downloading file: {e}"


def finish(summary: str) -> str:
    return f"TASK_COMPLETED::{summary}"


TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "list_dir": list_dir,
    "run_shell": run_shell,
    "search_files": search_files,
    "download_file": download_file,
    "finish": finish,
}


class Phi3Agent:
    def __init__(self):
        self.client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama"
        )
        self.messages: List[Dict[str, str]] = []
        self.iteration = 0

    def _build_system(self) -> str:
        return SYSTEM_PROMPT.format(
            working_dir=str(WORKING_DIR),
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def _extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r"```json\s*(\{.*?\})\s*```",
            r"```\s*(\{.*?\})\s*```",
            r"(\{\s*\"tool\".*?\})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if "tool" in data:
                        return data
                except json.JSONDecodeError:
                    continue
        return None

    def _call_llm(self) -> str:
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": self._build_system()}] + self.messages,
                temperature=0.2,
                max_tokens=2048,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"LLM Error: {e}"

    def run(self, user_task: str):
        console.print(Panel(
            f"[bold]Task:[/bold] {user_task}",
            title="[bold green]Phi-3 Autonomous Agent[/bold green]",
            border_style="green"
        ))

        self.messages = [{"role": "user", "content": user_task}]
        self.iteration = 0

        while self.iteration < MAX_ITERATIONS:
            self.iteration += 1
            console.print(f"\n[dim]── Iteration {self.iteration}/{MAX_ITERATIONS} ──[/dim]")

            response = self._call_llm()
            self.messages.append({"role": "assistant", "content": response})

            clean = re.sub(r"```json.*?```", "", response, flags=re.DOTALL).strip()
            if clean:
                console.print(Panel(Markdown(clean[:1500]), title="Thinking", border_style="blue"))

            tool_call = self._extract_tool_call(response)

            if not tool_call:
                console.print("[yellow]No tool call detected. Asking model to continue or finish...[/yellow]")
                self.messages.append({
                    "role": "user",
                    "content": "Please either call a tool using the JSON format or call the finish tool if the task is complete."
                })
                continue

            tool_name = tool_call.get("tool")
            args = tool_call.get("args", {})

            if tool_name not in TOOLS:
                result = f"Unknown tool: {tool_name}. Available tools: {list(TOOLS.keys())}"
            else:
                console.print(f"[bold cyan]→ Calling tool:[/bold cyan] {tool_name}({args})")
                try:
                    result = TOOLS[tool_name](**args)
                except TypeError as e:
                    result = f"Tool argument error: {e}"
                except Exception as e:
                    result = f"Tool execution error: {e}"

            if isinstance(result, str) and result.startswith("TASK_COMPLETED::"):
                summary = result.replace("TASK_COMPLETED::", "")
                console.print(Panel(
                    f"[bold green]Task Completed[/bold green]\n\n{summary}",
                    title="Done",
                    border_style="green"
                ))
                return

            display = result if len(result) < 2000 else result[:2000] + "\n...[truncated]"
            console.print(Panel(display, title="Tool Result", border_style="yellow"))

            self.messages.append({
                "role": "user",
                "content": f"Tool result for {tool_name}:\n{result}\n\nContinue with the next step or call finish if done."
            })

        console.print("[bold red]Reached maximum iterations. Stopping.[/bold red]")


def main():
    console.print(Panel(
        "[bold]Phi-3 Autonomous Coding Agent[/bold]\n"
        "Local • Private • Fully Autonomous Mode\n\n"
        "[yellow]Safety:[/yellow] Dangerous commands still require confirmation.\n"
        "Only use on systems/targets you own or have permission for.",
        title="Welcome",
        border_style="magenta"
    ))

    try:
        import httpx
        r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=3.0)
        if r.status_code != 200:
            console.print("[red]Ollama is not responding. Start it with: ollama serve[/red]")
            sys.exit(1)
    except Exception:
        console.print("[red]Cannot connect to Ollama. Make sure it is running on port 11434.[/red]")
        sys.exit(1)

    console.print(f"[green]✓[/green] Connected to Ollama | Model: [cyan]{MODEL_NAME}[/cyan]")
    console.print(f"[green]✓[/green] Working directory: [cyan]{WORKING_DIR}[/cyan]\n")

    while True:
        try:
            task = console.input("[bold green]You > [/bold green]").strip()
            if not task:
                continue
            if task.lower() in ("exit", "quit", "q"):
                console.print("Goodbye!")
                break
            if task.lower() in ("clear", "cls"):
                console.clear()
                continue

            agent = Phi3Agent()
            agent.run(task)
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
