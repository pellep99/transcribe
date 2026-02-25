#!/usr/bin/env python3
"""Transcribe an MP4 file to DOCX using ffmpeg and whisperx."""

import argparse
import os
import re
import subprocess
import sys

from docx import Document


def vtt_to_docx(vtt_path, docx_path):
    """Convert a VTT subtitle file to a DOCX document with speaker/transcription table."""
    document = Document()
    table = document.add_table(rows=1, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Speaker ID"
    hdr_cells[1].text = "Transcription"

    pattern_time = re.compile(r"(\d{2}:)?\d{2}:\d{2}\.\d{3} --> (\d{2}:)?\d{2}:\d{2}\.\d{3}")
    pattern_speaker = re.compile(r"\[SPEAKER_\d{2}\]:")

    current_speaker = None
    current_text = ""
    start_timestamp, end_timestamp = None, None
    end_timestamp_temp = None

    def add_row_to_table():
        nonlocal current_speaker, current_text, start_timestamp, end_timestamp
        if current_text:
            current_text = current_text.replace("WEBVTT", "")
            cells = table.add_row().cells
            cells[0].text = current_speaker if current_speaker else "Unknown Speaker"
            cells[1].text = current_text.strip() + f" ({start_timestamp} --> {end_timestamp})"
            current_text = ""
            start_timestamp, end_timestamp = None, None

    with open(vtt_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if pattern_time.match(line):
                end_timestamp_temp = line.split(" --> ")[1]
                if not start_timestamp:
                    start_timestamp = line.split(" --> ")[0]
            elif pattern_speaker.match(line):
                speaker = line.split(":")[0] + "]"
                if current_speaker and current_speaker != speaker:
                    if end_timestamp_temp:
                        end_timestamp = end_timestamp_temp
                    add_row_to_table()
                current_speaker = speaker
                current_text += " " + line.split(":", 1)[1].strip()
            elif line:
                current_text += " " + line

        if end_timestamp_temp:
            end_timestamp = end_timestamp_temp
        add_row_to_table()

    document.save(docx_path)


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe an MP4 file using whisperx (Swedish or English)."
    )
    parser.add_argument("input_mp4", help="Path to the input MP4 file")
    parser.add_argument(
        "language",
        choices=["SE", "EN"],
        help="Transcription language: SE (Swedish) or EN (English)",
    )
    args = parser.parse_args()

    input_mp4 = args.input_mp4
    language = args.language

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("Error: environment variable HF_TOKEN is not set.")
        print("Set it with: export HF_TOKEN=your_huggingface_token")
        sys.exit(1)

    if not os.path.isfile(input_mp4):
        print(f"Error: file '{input_mp4}' not found.")
        sys.exit(1)

    # Derive paths: put the wav file next to the input mp4
    base_name = os.path.splitext(os.path.basename(input_mp4))[0]
    input_dir = os.path.dirname(os.path.abspath(input_mp4))
    wav_file = os.path.join(input_dir, f"{base_name}.wav")
    vtt_file = os.path.join(input_dir, f"{base_name}.vtt")

    # Step 1: Convert MP4 to WAV
    print(f"[1/4] Converting '{input_mp4}' to WAV...")
    subprocess.run(["ffmpeg", "-i", input_mp4, wav_file], check=True)

    # Steps 2-4: Activate conda env and run whisperx in a single shell session
    if language == "SE":
        whisperx_cmd = (
            f"whisperx {wav_file}"
            f" --model large"
            f" --task transcribe"
            f" --hf_token {hf_token}"
            f" --language sv"
            f" --align_model KBLab/wav2vec2-large-voxrex-swedish"
            f" --output_format vtt"
            f" --compute_type float32"
            f" --diarize"
            f" --output_dir {input_dir}"
        )
    else:
        whisperx_cmd = (
            f"whisperx {wav_file}"
            f" --model large"
            f" --task transcribe"
            f" --hf_token {hf_token}"
            f" --language en"
            f" --output_format vtt"
            f" --compute_type float32"
            f" --diarize"
            f" --output_dir {input_dir}"
        )

    # conda activate requires sourcing conda.sh first, then running in the same shell
    shell_cmd = f"conda activate whisperx && {whisperx_cmd}"

    print(f"[2/4] Activating conda environment 'whisperx'...")
    print(f"[3/4] Running whisperx ({language})... This may take a long time.")
    subprocess.run(["bash", "-c", shell_cmd], check=True)

    # Step 5: Convert VTT to DOCX
    if not os.path.isfile(vtt_file):
        print(f"Error: expected VTT file '{vtt_file}' was not created.")
        sys.exit(1)

    docx_file = os.path.join(input_dir, f"{base_name}.docx")
    print(f"[4/4] Converting VTT to DOCX...")
    vtt_to_docx(vtt_file, docx_file)

    print("Done!")


if __name__ == "__main__":
    main()
