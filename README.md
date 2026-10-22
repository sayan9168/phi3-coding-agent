# Phi-3 Autonomous Coding Agent

Local terminal coding agent. Talks to **Phi-3** on Ollama. Your code stays on the machine.

## Tools

| Tool | What it does |
|---|---|
| `read_file` | Read a text file (max 500 KB) |
| `write_file` | Create or overwrite a file |
| `append_file` | Add text to the end of a file |
| `edit_file` | Replace one exact snippet |
| `delete_file` | Delete a file or directory (refuses `/` and home) |
| `move_path` | Move or rename |
| `mkdir` | Create a directory |
| `list_dir` | List a folder |
| `search_files` | Case-insensitive text search |
| `run_shell` | Run a shell command (180s) |
| `run_python` | Run a Python snippet |
| `download_file` | HTTP download to a path |
| `open_editor` | Open a path in VS Code (`code` / `codium`) |
| `git_status` | `git status` |
| `git_diff` | Diff stat |
| `git_log` | Recent commits |
| `git_commit` | `git add -A` and commit |
| `git_push` | Push to a named remote (no `--force`) |
| `finish` | Stop when the task is done |

Dangerous shell patterns (`rm -rf /`, `curl \| sh`, `git push --force`, `git reset --hard`) still ask before they run.

This is a coding agent, not an attack tool. Do not point it at systems you do not own or do not have permission to change.

## Requirements

- Python 3.10+
- Ollama with `phi3:latest` (or another local model)
- Optional: `git`, VS Code `code` command

## Install

```bash
git clone https://github.com/sayan9168/phi3-coding-agent.git
cd phi3-coding-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

In another terminal:

```bash
OLLAMA_CONTEXT_LENGTH=8192 ollama serve
```

## Run

```bash
python agent.py
```

Examples:

```text
Create calc.py, a small calculator, then open it in VS Code
```

```text
Show git status, then commit the changes with a short message
```

```text
Search for TODO and list the files
```

## Config

```bash
export PHI3_MODEL=phi3:latest
export OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
export PHI3_MAX_STEPS=30
```

Phi-3 Mini is small. Long multi-file jobs may stall. A coder model is better if you have RAM:

```bash
ollama pull qwen2.5-coder:7b
PHI3_MODEL=qwen2.5-coder:7b python agent.py
```

## VS Code

```bash
# Arch
sudo pacman -S code
# or
yay -S visual-studio-code-bin
```

In VS Code: Command Palette, **Shell Command: Install 'code' command in PATH**.
