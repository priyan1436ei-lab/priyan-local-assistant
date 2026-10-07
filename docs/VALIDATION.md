# Verification record

## Passed in the build environment

- **37 Python automated tests**: all passed.
- JavaScript syntax validation with `node --check`: passed.
- Python module compilation: passed.
- Static HTML/JavaScript integration: unique element IDs, all literal JS ID references present, local-only asset URLs.
- Local server starts and serves the dashboard; HTTP tests exercise real requests, token checks, Host/Origin rejection, document import, organizer mutation and file-download boundary checks.

Tests include real SQLite persistence, backup/restore, Unicode/Tamil text retrieval, DOCX extraction, due reminder firing and recurrence, task completion, memory disabling, invalid model action recovery, stop preventing subsequent tool execution, file backups, path/symlink restrictions, real approved Python command execution, denial, running process termination, budget/resume and single-instance locking.

The native worker protocol test launches the real worker subprocess with a stand-in `llama_cpp` API. It verifies JSON input/output and model reload behavior; it is **not a real model inference test**. The sandbox dispatch test checks that sandbox mode never silently falls back to host execution; it is **not a Docker isolation benchmark**.

## Not verified here

- Real GGUF generation quality, throughput, native wheel installation and RTX 3050 CUDA behavior: native inference dependencies/model weights/GPU were unavailable in this environment.
- Physical microphone capture, real Whisper transcription, Tamil OS voice availability and audio playback.
- Windows batch launchers and installation on a Windows machine.
- Actual Docker image build and live container isolation.
- Visual desktop/mobile browser behavior: no browser binary was installed. Playwright browser download was attempted but returned an unusable archive, so visual and browser-interaction verification could not be completed. No screenshot or simulated browser result is presented as proof.

## First-run acceptance checks on your computer

1. Run the installer, start the app, and check that Settings finds the embedded engine and the GGUF model.
2. Ask “What is 17 multiplied by 23? Use the calculator.” Verify a calculate event with result 391.
3. Ask it to save a note; check Notes, then restart and confirm the note remains.
4. Import a short document with a unique phrase. Search that phrase and ask a document-grounded question; inspect the actual source card.
5. Set a reminder a minute ahead. Keep the app/browser open; verify the alert and snooze/done behavior.
6. Give the coding agent a small Python task. Inspect its generated files, approve the test command and check the real exit code.
7. If using sandbox mode, build the image first and check a Python test runs without approval inside that mode. Do not infer sandbox availability from the setting alone.
8. If voice is installed, record a short sentence and inspect the recognized text before sending it.
9. Export a backup; restore into a new folder and verify a saved note there.

This is a local personal software build with source and tests, not a guarantee of arbitrary autonomous task completion or a security-certified desktop agent.
