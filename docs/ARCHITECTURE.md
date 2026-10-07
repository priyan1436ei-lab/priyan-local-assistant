# Architecture and data flow

## Runtime

The frontend is plain HTML/CSS/JavaScript served by a Python loopback HTTP server. The browser communicates only with the same local origin. No frontend package manager, remote fonts, CDN, analytics or cloud API is needed.

`Assistant` owns the organizer, personal tools and SQLite records. A background thread processes one conversational job at a time. The model returns a JSON action, the dispatcher validates and executes the allowed tool, then sends the observed result into the next model turn. Up to eight actions are allowed per reply. Chat can launch a separate coding task and ask for its status.

`Agent` owns code/files/command tasks. Its plan → tool → result loop allows 30 actions before pausing. Tasks can be resumed with a fresh budget. Commands either pause for user approval or execute automatically in the configured offline Docker sandbox. One coding task runs at a time. Chat and coding share the model manager, which serializes inference to avoid holding two models in VRAM.

`LocalModel` manages a persistent `native_worker.py` subprocess over stdin/stdout JSON. The worker loads a GGUF through `llama_cpp.Llama`, uses its chat template and constrains output to a JSON object. It does not contact a model server. A 300-second response timeout terminates a stuck engine. A model/context/GPU configuration change reloads the native model. Model dependencies are imported lazily, so non-AI organizer tools run without them.

## Local retrieval

Documents are extracted, limited in size, split into 1200-character chunks with 180-character overlap and stored in SQLite. Query terms are normalized and matched against passages. The highest-scoring passages become model context. Actual snippets are retained in source cards. This is keyword retrieval, not embedding search, training or proof that the answer is correct.

## Persistence

Two SQLite databases preserve compatibility with the original coding runner. Both use local thread locks and WAL mode. The assistant stores typed JSON records; the coding runner stores task snapshots and events. A process-level data-directory lock prevents duplicate app instances from reopening the same live jobs.

The backup path blocks new chat work and locks the stores/agent while SQLite backup and file archive creation run. Active coding work must finish or stop first. Restore only accepts an unused directory, rejects unsafe paths and checks database integrity.

## Reminder execution

A local clock checks due times every three seconds and persists fired reminders. Browser polling shows banners and may issue OS notifications after browser permission. Recurrence advances when the reminder is acknowledged. Reminders do not wake the machine or run while the app is closed; overdue entries fire when the service starts again.

## Voice

Microphone recording uses MediaRecorder. Audio is sent to localhost and transcribed by a cached faster-whisper CPU model loaded with local-files-only. No browser SpeechRecognition/cloud endpoint is used. Read aloud launches a local pyttsx3 process using installed OS voices. Optional package/model installation is an explicit setup step, not a runtime fallback.

## Extension points

- New personal tool: add an explicit schema to SYSTEM and an allowlisted branch in Assistant.tool.
- New coding tool: add its contract to PROMPT and validate in Agent.execute or the dedicated command handler.
- Different model: copy a compatible instruct GGUF into models and select it in Settings.
- More offline runtime languages/dependencies: extend sandbox/Dockerfile and build ahead of time.
- Semantic search, OCR or OS integrations would be separate features; they are not silently simulated here.
