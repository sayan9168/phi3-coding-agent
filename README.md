# Phi-3 Autonomous Coding Agent

A fully autonomous terminal coding agent powered by local **Phi-3** via Ollama.

## Features

- Fully autonomous multi-step execution
- File operations (read, write, edit)
- Shell command execution
- File search (grep-like)
- Download files from URL
- Beautiful terminal UI with Rich
- Safety filter for highly dangerous commands
- Runs 100% locally (no data leaves your machine)

## Requirements

- Python 3.10+
- Ollama installed and running
- `phi3:latest` model pulled

## Installation

```bash
cd phi3-coding-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
OLLAMA_CONTEXT_LENGTH=8192 ollama serve
```

## Usage

```bash
python agent.py
```

Then type your task in natural language.

### Examples

```
Create a simple Python calculator and save it as calc.py
```

```
Read the file main.py and explain what it does
```

```
Create a basic FastAPI hello world project
```

## Configuration

```bash
export PHI3_MODEL=phi3:latest
export OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
```

## Safety Notes

- The agent runs in autonomous mode (keeps going until the task is done).
- Extremely dangerous commands (like `rm -rf /`, `mkfs`, pipe-to-shell) still require confirmation.
- Only use this agent on systems and targets you own or have explicit written permission to test.
- Unauthorized scanning, exploitation, or attacks are illegal.
- The author is not responsible for any misuse.

## Limitations (Phi-3 Mini)

- Context window is limited. Keep tasks reasonably sized.
- Complex multi-file refactoring may need multiple iterations.
- For better coding quality, consider `qwen2.5-coder:7b` later.

## Switch model

```bash
ollama pull qwen2.5-coder:7b
PHI3_MODEL=qwen2.5-coder:7b python agent.py
```

---

Made for local privacy-first coding.
