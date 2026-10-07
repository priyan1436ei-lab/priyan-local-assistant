# Priyan Local — முதலில் இதைப் படி

இது **Ollama link செய்யும் app இல்லை**. GGUF model-ஐ app-க்குள்ளேயே llama.cpp engine மூலம் நேரடியாக இயக்கும் personal AI assistant.

## Windows-ல் start பண்ணுவது

1. **Python 3.11 அல்லது 3.12, 64-bit** install பண்ணு. “Add Python to PATH” tick பண்ணு.
2. ZIP-ஐ extract பண்ணு.
3. **install-windows.bat** double-click பண்ணு. முதல் தடவை internet வேண்டும்; engine + சுமார் 2.1 GB model download ஆகும்.
4. Install முடிந்ததும் **start-windows.bat** open பண்ணு.
5. Browser-ல் dashboard வரும். **Settings → Check embedded engine** click பண்ணு.
6. Assistant tab-ல் கேள்வி/வேலை கொடு.

**Ollama / paid API key / separate model server தேவையில்லை.** Model weights இந்த ZIP-க்குள் இல்லை; installer download செய்து checksum verify பண்ணும். புதிய language model-ஐ zero-லிருந்து train செய்தது இல்லை; open model-ஐ பயன்படுத்தும் முழு assistant application.

## என்ன செய்யலாம்?

- English, Tamil, Thenglish chat.
- Notes, tasks, reminders save பண்ணலாம்.
- உன்னைப் பற்றிய useful preferences-ஐ memory-ல் save/edit/delete பண்ணலாம்.
- PDF, DOCX, TXT, Markdown போன்ற files import பண்ணி கேள்வி கேட்கலாம்.
- Coding task கொடுத்து files create/edit, tests run, errors fix செய்யலாம்.
- Local backup எடுத்து வேறு computer-க்கு restore பண்ணலாம்.

## Voice வேண்டுமா?

**install-voice-windows.bat** ஒருமுறை run பண்ணு. பிறகு app restart பண்ணு. Chat-ல் Voice button → speak → Stop → recognized text verify → Send.

Voice recognition local-ஆ CPU-ல் ஓடும். Read aloud-க்கு உன் Windows-ல் installed voice பயன்படுத்தப்படும். Tamil output-க்கு Tamil-capable system voice வேண்டும்.

## தானாக commands ஓட வேண்டுமா?

Default-ல் PC commands-க்கு approval கேட்கும். Files read/write automatic.

Automatic mode-க்கு Docker install செய்து, project folder-ல்:

```text
docker build -t priyan-sandbox:local sandbox
```

பிறகு Settings → **Autonomous offline Docker sandbox** select பண்ணு. அதன் பிறகு coding commands network இல்லாத container-க்குள் automatic-ஆ ஓடும். இந்த container-ல் Python standard library மட்டும் இருக்கும்; கூடுதல் tools/dependencies முன்பே install செய்ய வேண்டும்.

## தெரிந்திருக்க வேண்டியது

- AI எல்லா பிரச்சினைக்கும் சரியான answer guarantee செய்யாது; output/test results inspect பண்ணு.
- Full PC/browser control, WhatsApp/email sending, payments, live internet research இதில் இல்லை.
- Reminders சரியான நேரத்தில் வர app running-ல் இருக்க வேண்டும். Browser close என்றால் popup வராது.
- RTX 3050 GPU setup optional; full steps SETUP.md-ல் இருக்கு. GPU speed இங்கே benchmark செய்யப்படவில்லை.
- Real model inference, Windows installer, microphone, Docker ஆகியவற்றை உன் PC-ல் run செய்து verify செய்ய வேண்டும். Included automated tests runner மற்றும் storage logic-ஐ test செய்கின்றன.

முழு technical guide: **SETUP.md**. Code எல்லாமே editable source-ஆ கொடுக்கப்பட்டுள்ளது.
