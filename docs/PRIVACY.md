# Privacy and execution boundaries

- Runtime AI inference, document search, data storage and optional speech processing happen locally.
- The app makes no remote model calls. Setup downloads packages/model weights while you explicitly run it.
- Downloaded native packages and models remain separate third-party components with their own licenses and trust requirements.
- The UI binds only to 127.0.0.1, validates Host and Origin, and requires a random session token on API requests. Content Security Policy blocks remote assets and framing.
- It is single-user software for a trusted OS account. Local software with the same account permissions may read its data; the token is not an OS security boundary.
- Documents, memory, conversations and backups are unencrypted. Deleting records removes them from the app; it is not forensic secure erasure of SQLite pages, prior backups or OS storage.
- File tools reject workspace escapes, hidden paths, symlinks and hard links. Existing text files overwritten by file tools are backed up.
- Approved host commands run with your OS permissions. They are not constrained by file-tool path checks and may use the network. Review generated scripts before allowing execution.
- Automatic sandbox commands use a network-disabled container with only the dedicated workspace mounted. The workspace can still be modified/deleted. Containers are not an absolute protection against all vulnerabilities.
- Execution stop kills the managed command process group on Unix or the process tree on Windows and removes the named Docker container. Host processes can escape process groups or spawn detached services; this tool is not an endpoint-control product.
- Browser/OS notifications can reveal reminder text on your screen. Enable them only if that is appropriate for your computer.
- Voice audio is temporary and deleted after transcription; transcripts become conversation data when sent. No wake-word listener runs in the background.
