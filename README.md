# transcribe

Kommandoradsverktyg som transkriberar MP4-videofiler till DOCX-dokument med hjälp av [WhisperX](https://github.com/m-bain/whisperX). Stöder svenska och engelska.

## Förutsättningar

- **ffmpeg** — för konvertering av MP4 till WAV
- **Conda** — med en miljö vid namn `whisperx` som har WhisperX installerat
- **Hugging Face-token** — krävs för diarization och alignment-modeller
- **whisper_vtt_to_docx.py** — skript för att konvertera VTT-undertexter till DOCX

## Användning

1. Sätt din Hugging Face-token som miljövariabel:

   ```bash
   export HF_TOKEN=din_huggingface_token
   ```

2. Kör programmet:

   ```bash
   python transcribe.py <mp4-fil> <språk>
   ```

   - `<mp4-fil>` — sökväg till MP4-filen som ska transkriberas
   - `<språk>` — `SE` för svenska eller `EN` för engelska

### Exempel

```bash
python transcribe.py meeting.mp4 SE    # transkribera på svenska
python transcribe.py lecture.mp4 EN    # transkribera på engelska
```

## Vad programmet gör

1. Konverterar MP4-filen till WAV med `ffmpeg`
2. Aktiverar conda-miljön `whisperx`
3. Kör WhisperX med `large`-modellen för transkribering och diarization (talaridentifiering)
   - Svenska använder alignment-modellen `KBLab/wav2vec2-large-voxrex-swedish`
4. Konverterar den genererade VTT-filen till ett DOCX-dokument via `whisper_vtt_to_docx.py`
