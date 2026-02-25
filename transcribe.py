#!/usr/bin/env python3
"""Transcribe an MP4 file to DOCX using ffmpeg, whisperx, and whisper_vtt_to_docx."""

import argparse
import os
import subprocess
import sys


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

    print(f"[4/4] Converting VTT to DOCX...")
    subprocess.run(["python", "whisper_vtt_to_docx.py", vtt_file], check=True)

    print("Done!")


if __name__ == "__main__":
    main()
