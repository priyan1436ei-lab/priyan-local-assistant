# Priyan Local · Setup from A to Z

## 1. Windows installation

Use 64-bit Python 3.11 or 3.12. These versions are a practical starting point for native engine wheels. Install Python from https://www.python.org/downloads/ and select “Add Python to PATH”.

Extract the project to a folder such as `C:\PriyanLocal`. Run `install-windows.bat`. It:

1. Creates a private `.venv` Python environment.
2. Installs the embedded `llama-cpp-python` CPU engine from the official package sources, requiring a prebuilt engine wheel rather than silently compiling it.
3. Installs local PDF support.
4. Downloads the official `qwen2.5-3b-instruct-q4_k_m.gguf` model into `agent-data/models`.
5. Verifies the SHA-256 before activating the download.
6. Records installed versions in `installed-versions.txt`.

The GGUF download is about 2.1 GB; native packages and optional voice add more. Leave free space for downloads, the installed model, runtime memory and your own data. This ZIP contains source, not model weights.

Start with `start-windows.bat`. Keep the terminal open while using the app. Close with Ctrl+C. The browser address is http://127.0.0.1:8765.

If the Python launcher selected an unsupported newer Python and the wheel install fails, use an explicit environment:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install --only-binary=llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-documents.txt
.venv\Scripts\python.exe setup.py --model
.venv\Scripts\python.exe app.py
```

If no compatible wheel is published for your machine, the installer stops with an error. Use a supported 64-bit Python, or build the native engine following its official documentation. This project does not silently download random third-party executables.

## 2. GPU / RTX 3050

The default configuration is CPU and does not need CUDA. For GPU inference, install a CUDA-enabled engine matching your NVIDIA driver, CUDA runtime and Python version. The engine's official instructions list supported wheel indexes:

https://github.com/abetlen/llama-cpp-python#installation

For example, **only if your system is compatible with the CUDA 12.4 wheel**, run:

```powershell
.venv\Scripts\python.exe -m pip install --upgrade --force-reinstall --only-binary=llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124 "llama-cpp-python>=0.3,<0.4"
```

Then Settings → Inference device → GPU, save, and send a short message. GPU offload requires a GPU-enabled build; changing the setting alone does not install CUDA support. If VRAM is insufficient, choose 16-layer offload, reduce context to 2048 or return to CPU. Model weights plus the context/KV cache consume memory. No speed, full-GPU residency or RTX 3050 benchmark is claimed.

## 3. Linux / macOS

```bash
sh install.sh
sh start.sh
```

If a CPU wheel isn't available for your platform, follow the native engine's documented source build. Apple Silicon users should use an ARM64 Python and the documented Metal build/index, then set GPU offload. The launchers and Python code are portable; they have not been run on every OS.

## 4. Truly local model loading

The app does not call Ollama or a hosted model API. `local_model.py` starts `native_worker.py`, which loads the GGUF file directly using `llama_cpp.Llama`. Requests and results travel over local process pipes. Only one model instance is kept resident, reducing memory use; chat and code requests serialize through one engine.

First generation includes model load time. Later requests reuse the process. Inference is limited to five minutes per request. If it exceeds this limit the process is killed and the UI reports an error. Stop prevents further tool actions; an in-flight generation may continue until it returns or times out. The application does not show token streaming; it shows completion and action activity.

You can copy a compatible instruction-tuned GGUF file into `agent-data/models` and select its filename. Its tokenizer/chat template must be supported by the installed engine. Choosing an arbitrary model does not guarantee correct tool use. The default model is small and may make mistakes on long or complex agent tasks.

Official model:
https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF

Default file:
`qwen2.5-3b-instruct-q4_k_m.gguf`

SHA-256:
`626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`

The installer keeps interrupted bytes in `.gguf.part` and attempts HTTP Range resume. If the server ignores Range, it restarts the download. A checksum mismatch never activates the file; delete the `.part` and retry. Model license terms are separate from this project's source.

## 5. Voice

Windows: run `install-voice-windows.bat` once while online. Manual equivalent:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-voice.txt
.venv\Scripts\python.exe setup.py --voice
```

On Linux/macOS use `.venv/bin/python` instead. Restart the assistant afterward.

In Chat press Voice, allow microphone access, speak, then Stop recording. Recording stops automatically after one minute. The audio goes to the **same local Python app**, where faster-whisper transcribes it with the downloaded multilingual small model on CPU. Transcription never downloads models at runtime. Review the recognized text before pressing Send. Audio is kept in a temporary file for transcription and removed afterward. Transcript text is saved only when you send it.

Read aloud uses `pyttsx3` and the OS's installed voices. Tamil output needs a Tamil-capable installed system voice; availability differs by OS. Linux may require `espeak-ng` and audio libraries. Installing pyttsx3 alone does not guarantee a working OS voice. A microphone and audio playback device are required for real voice tests.

No always-listening wake word is implemented. Voice recording is deliberately push-to-talk.

## 6. Coding autonomy

### Review commands on your PC

Default mode. The agent can create/read/edit text files in `workspace` automatically. Every command shows the exact argv list and requires Approve once. Review both the command and files/scripts it executes. Host commands have your OS permissions and are **not sandboxed**. They may use the network if you approve a command that does so. Execution of dependencies/build scripts can also run code.

### Automatic offline sandbox

Install Docker Desktop/Engine, start it and build the included image while online:

```text
docker build -t priyan-sandbox:local sandbox
```

Then Settings → Command execution → Autonomous offline Docker sandbox → Save. Commands execute automatically with:

- No network (`--network=none`), no image pulls at runtime.
- Only the project workspace mounted.
- Read-only container root; writable temporary scratch.
- Dropped capabilities, no-new-privileges, process/memory/CPU limits.
- 60-second command limit and capped output.

The included image provides Python's standard library. Add dependencies to its Dockerfile and rebuild in advance. It does not include Node, Java or arbitrary system packages. A command that needs an absent tool fails honestly and the agent sees the error. There is no automatic fallback from sandbox to host.

The workspace remains writable; automatic code may overwrite or delete files there. Put **copies** of projects in it. Container isolation is a practical boundary, not a guarantee against every OS/container vulnerability. Docker must remain available. Container images are not included in backups.

## 7. Documents and memory

Import documents in the Documents tab. Text extraction and retrieval remain local. UTF-8 text/code and DOCX work without additional packages. PDF needs pypdf. Limits: 5 MB per document, 400000 text characters, up to 250 PDF pages. Scans/images have no OCR support.

Retrieval matches query words against overlapping passages; it is not semantic/vector search. Use specific words from your source. The assistant includes source excerpts under an answer so you can verify what it saw. A citation alone is not proof the model interpreted it correctly.

Memory is manually editable. The assistant can also save memory when explicitly asked; tool results are visible. Turn off “Use my saved memory in chat” to omit it from the automatic prompt. The Memory tab still allows you to inspect/delete saved entries.

## 8. Tasks and reminders

Planner works without an AI model. Reminder times entered in the UI are converted from your browser's local time to UTC. Natural-language requests use the computer's local timezone in the model context. Make timezone and date explicit for clarity.

The Python process checks reminders every three seconds. Keep it running for on-time evaluation; keep a browser tab open for banners/desktop notifications. Closing the app stops checks. Missed reminders are flagged at next startup. Acknowledging a recurring reminder advances to the next future fixed interval. This app does not wake a sleeping computer or install itself as a system service.

## 9. Backups, restore and moving computers

Settings → Download backup exports SQLite databases, coding workspace and file-tool backups. It is blocked during active chat/coding work. Model weights are excluded.

To restore, close the app and use a new folder:

```text
python maintenance.py priyan-backup.zip --to restored-data
python app.py --data restored-data
```

Copy or download models into `restored-data/models`, or run:

```text
python setup.py --model --data restored-data
```

The restore tool rejects unsafe paths and verifies SQLite integrity; it never overwrites an existing target folder. Backups are unencrypted and contain your private content. Keep them somewhere you trust.

## 10. Troubleshooting

| Symptom | Action |
|---|---|
| Embedded engine missing | Run the installer using the same `.venv` Python that launches the app |
| Model missing | Run `.venv\Scripts\python.exe setup.py --model`; use the filename in Settings |
| Generation is slow | First load is slower; reduce context, use GPU-compatible build or a smaller supported model |
| Native engine exits | Check free RAM/VRAM, correct CPU architecture and CUDA build compatibility |
| Model returns bad actions | Narrow the task; small models have limited tool reliability; try a stronger compatible local GGUF |
| Context too large | Shorten the prompt; use fewer document excerpts or a larger context setting |
| Port already used | Open the running app or use `python app.py --port 8766` |
| Voice button says setup needed | Install voice packages and download the voice model into the same data folder |
| Speech is silent | Install/enable an OS speech voice and audio output; see pyttsx3 documentation |
| PDF has no text | Use an OCR tool first; scanned-PDF OCR isn't included |
| Container executable missing | Install it in the sandbox image before switching back to offline operation |
| File blocked | Hidden paths, symlinks, hard links and workspace escapes are intentionally excluded by file tools |

Run `python diagnose.py` for local dependency/model checks. No internet request is made by the diagnostic. Do not expose the app to the public internet; it is a single-user localhost application.

## Upstream references

- Native engine and supported wheels: https://github.com/abetlen/llama-cpp-python
- Default model and license: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF
- Offline speech recognition: https://github.com/SYSTRAN/faster-whisper
- Offline speech output: https://github.com/nateshmbhat/pyttsx3
- Docker command isolation: https://docs.docker.com/reference/cli/docker/container/run/
