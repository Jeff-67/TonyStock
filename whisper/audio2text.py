"""Audio transcription module using OpenAI's Whisper model.

This module provides functionality to transcribe audio files using Whisper,
outputting both complete transcripts and timestamped segments.
"""

import whisper

# Force CPU usage since MPS has compatibility issues with Whisper's sparse operations
device = "cpu"
print("Using CPU due to MPS compatibility issues with Whisper")

model = whisper.load_model("large-v3", device=device)  # type: ignore[attr-defined]

# load audio and pad/trim it to fit 30 seconds
result = model.transcribe(audio="/Users/jeffyang/Desktop/Untitled.m4a")

# Format and save the text with timestamps
with open("transcript.txt", "w") as f:
    # Write the complete text first
    f.write("Complete Transcript:\n")
    f.write(result["text"])
    f.write("\n\nDetailed Segments with Timestamps:\n")

    # Write each segment with timestamps
    for segment in result["segments"]:
        # Format timestamps as [MM:SS.mmm]
        start = f"{int(segment['start'] // 60):02d}:{segment['start'] % 60:06.3f}"
        end = f"{int(segment['end'] // 60):02d}:{segment['end'] % 60:06.3f}"
        f.write(f"[{start} -> {end}] {segment['text'].strip()}\n")
