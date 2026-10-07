# PRIYAN LOCAL · Personal AI Assistant v2

A complete local assistant application with an **embedded GGUF inference engine**. No Ollama, hosted model API, cloud account, API key or separate inference server is required. The application loads a downloaded model directly through llama.cpp in a local child process.

This is runnable application source, an installer and tests—not a trained-from-scratch language model or a bundled Windows EXE. The first installation downloads native dependencies and approximately 2.1 GB of model weights. Thereafter chat and built-in tools can run offline. Voice and PDF support have additional local packages.

## Start on Windows

1. Install **64-bit Python 3.11 or 3.12**; enable **Add Python to PATH**.
2. Extract the ZIP into a writable folder.
3. Double-click **`install-windows.bat`** while online. Leave the window open until it says installation finished.
4. Double-click **`start-windows.bat`**.
5. The dashboard opens at **http://127.0.0.1:8765**. Go to **Settings → Check embedded engine**, then chat.

The default installer uses CPU inference for broad compatibility. RTX 3050 users can install a compatible CUDA engine and choose GPU offload; see [SETUP.md](SETUP.md). Hardware speed and GPU fit are not guaranteed or benchmarked here.

## What is included

| Area | Implemented behavior |
|---|---|
| Local AI | Direct GGUF inference through a persistent local child process; model switching and CPU/GPU offload settings |
| Chat | Multiple conversations, saved history, bounded context, stop, copy replies and visible action results |
| Languages | English, Tamil and Thenglish instructions; actual fluency depends on the model |
| Personal tools | Natural-language creation of notes, to-dos, reminders and explicit memory, plus arithmetic and document search |
| Documents | Local text, Markdown, code, CSV, JSON, DOCX and text-PDF extraction; snippet retrieval and source cards |
| Memory | User-editable persistent facts and preferences; enable/disable in settings |
| Organizer | Notes with edit/delete, task completion, reminders, snooze and fixed daily/weekly recurrence |
| Voice | Optional microphone recording, fully local Whisper transcription, OS speech output and speech stop |
| Coding agent | Plan, inspect, write, execute, inspect results, repair, finish; stop/resume; saved history and overwrite backups |
| Execution | Individually approved host commands OR automatic network-disabled Docker commands |
| Workspace | File browsing, text preview, download; file-tool path/symlink/hard-link restrictions |
| Backup | Download a consistent SQLite + workspace ZIP; restore into a new folder with path and database checks |
| Setup | Windows/macOS/Linux launchers, verified/resumable model download, optional voice installation and diagnostics |

## Things to try

- “Explain Python decorators in Thenglish with two small examples.”
- “Save a note called Exam plan: revise unit 1 and practise five problems.”
- “Remember that I prefer short answers with examples.”
- “Create a task to review my portfolio.”
- “Remind me on 10 October 2026 at 7 PM India time to review my project.”
- Import a document, enable **Use my documents**, and ask using a topic word from that document.
- In **Coding agent**: “Create a standard-library Python CSV expense tracker. Include add/list/total commands, unit tests and a README. Run the tests and fix failures.”

## A clear boundary

The assistant is a working local software project with defined tools; it cannot automatically do every possible computer task. It does **not** include arbitrary desktop/browser control, web research, email/WhatsApp sending, live banking, payments, image generation, OCR, calendar-provider integration or a trained custom foundation model. Internet-dependent services would require separate integrations. Core tools remain available offline.

The chat assistant can delegate coding goals to the background coding agent. They share a local model; inspect execution and approve commands in the Coding agent tab. The agent's “completed” state is a model report; inspect actual tool output and test exit codes.

Document search uses overlapping text chunks and **keyword matching**, not embedding/vector retrieval. Cross-language matching of unrelated terms is not guaranteed. Scanned PDFs need external OCR. No automatic browsing occurs.

## Local data

Default folder: `agent-data/` beside `app.py`.

- `assistant.sqlite3`: chats, notes, memories, reminders, documents and chat jobs.
- `tasks.sqlite3`: coding tasks and action history.
- `workspace/`: coding files; place copies of existing project files here.
- `backups/`: versions of text files overwritten by the agent's file tool.
- `models/`: GGUF and optional speech-recognition model.

Data and backups are not encrypted by the app. Use your OS disk encryption if needed. Do not copy secrets into the coding workspace. No analytics, telemetry or remote CDN assets are used by this application's runtime. Approved host commands still have your OS account's network permissions.

## Tests

From this folder:

```text
python -m unittest discover -v
python diagnose.py
```

Tests exercise real persistence, document extraction/retrieval, reminders, backups, file tools, approved subprocesses, HTTP access controls and model/tool orchestration with scripted responses. They do not establish real model intelligence, GPU performance, native wheel compatibility or microphone/OS voice quality. See [docs/VALIDATION.md](docs/VALIDATION.md) for the exact verification scope.

## Project map

```text
app.py                  Loopback HTTP API and launcher
assistant.py            Personal assistant, tools, reminders, backup
agent.py                Coding agent, approval, sandbox, stop/resume
local_model.py          Embedded inference process manager
native_worker.py        GGUF loading and local token generation
storage.py              SQLite persistence
knowledge.py            Document extraction and local retrieval
voice.py                Offline speech recognition and system TTS
setup.py                Explicit one-time model downloads
maintenance.py          Safe restore into a new data directory
diagnose.py             Offline dependency/model checks
static/                 Dashboard HTML, CSS, JavaScript
sandbox/Dockerfile      Offline Python command container
requirements*.txt       Native engine and optional packages
tests/                  Assistant and HTTP tests
test_agent.py           Coding-agent tests
SETUP.md                Detailed installation/troubleshooting
docs/                   Architecture, privacy and validation
```

Model and third-party software retain their own licenses. The default model comes from the official Qwen repository; review its model card and license before redistribution or commercial deployment. Sources and the download checksum are in SETUP.md and setup.py.
"# priyan-local-assistant" 
