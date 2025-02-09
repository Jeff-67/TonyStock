"""Flask web application for audio transcription using Whisper.

This module provides a web interface for uploading audio files and getting their
transcriptions using OpenAI's Whisper model. It includes features for managing
transcripts and downloading results.
"""

import json
import os
import platform
from datetime import datetime

import torch
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)

import whisper

app = Flask(__name__)
# Configure upload and transcript directories using os.path.join for cross-platform compatibility
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["TRANSCRIPTS_FOLDER"] = os.path.join(BASE_DIR, "static", "transcripts")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["TRANSCRIPTS_INDEX"] = os.path.join(
    app.config["TRANSCRIPTS_FOLDER"], "index.json"
)

# Ensure directories exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["TRANSCRIPTS_FOLDER"], exist_ok=True)


def get_device():
    """Determine the appropriate device for model inference.

    Returns:
        str: Either 'cuda' for NVIDIA GPU or 'cpu' for CPU processing.
    """
    if torch.cuda.is_available():
        return "cuda"  # NVIDIA GPU
    return "cpu"  # Fall back to CPU


DEVICE = get_device()
print(f"PyTorch version: {torch.__version__}")
print(
    f"Available devices: {'CUDA (NVIDIA GPU)' if torch.cuda.is_available() else ''}"
    f"{'MPS (Apple Silicon)' if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else ''}"
    f"{'CPU' if DEVICE == 'cpu' else ''}"
)
print(f"Using device: {DEVICE}")

# Load whisper model with device parameter - using large-v3 model as in audio2text.py
model = whisper.load_model("large-v3", device=DEVICE)  # type: ignore[attr-defined]


def process_audio(filepath):
    """Process audio file using direct transcription.

    Args:
        filepath (str): Path to the audio file to transcribe.

    Returns:
        dict: Transcription result containing text and segments.
    """
    # Use the high-level transcribe method that handles all preprocessing
    result = model.transcribe(filepath)
    return result


def save_transcript(filename, text, metadata, segments):
    """Save transcript and metadata to disk.

    Args:
        filename (str): Original audio filename.
        text (str): Transcribed text.
        metadata (dict): Additional metadata like language, duration, etc.
        segments (list): List of segments with timestamps and text.

    Returns:
        str: Generated transcript ID.
    """
    timestamp = datetime.now()
    transcript_id = timestamp.strftime("%Y%m%d_%H%M%S")

    # Create transcript data structure
    transcript_data = {
        "id": transcript_id,
        "original_filename": filename,
        "text": text,
        "segments": segments,  # Add segments to JSON data
        "metadata": metadata,
        "created_at": timestamp.isoformat(),
        "audio_file": os.path.join("uploads", filename).replace(
            "\\", "/"
        ),  # Ensure forward slashes for URLs
    }

    # Also save as a text file for easy reading
    text_file = os.path.join(app.config["TRANSCRIPTS_FOLDER"], f"{transcript_id}.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(f"Transcript of: {filename}\n")
        f.write(f"Created at: {timestamp.isoformat()}\n")
        f.write(f"Language: {metadata.get('language', 'unknown')}\n")
        f.write(f"Duration: {metadata.get('duration', 0):.2f} seconds\n")
        f.write(f"Model: {metadata.get('model', 'unknown')}\n")
        f.write(f"Device: {DEVICE}\n")
        f.write("\n--- Complete Transcript ---\n\n")
        f.write(text)
        f.write("\n\n--- Detailed Segments with Timestamps ---\n\n")
        # Write each segment with timestamps
        for segment in segments:
            # Format timestamps as [MM:SS.mmm]
            start = f"{int(segment['start'] // 60):02d}:{segment['start'] % 60:06.3f}"
            end = f"{int(segment['end'] // 60):02d}:{segment['end'] % 60:06.3f}"
            f.write(f"[{start} -> {end}] {segment['text'].strip()}\n")

    # Save individual transcript file
    transcript_file = os.path.join(
        app.config["TRANSCRIPTS_FOLDER"], f"{transcript_id}.json"
    )
    with open(transcript_file, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)

    # Update index file
    try:
        with open(app.config["TRANSCRIPTS_INDEX"], "r", encoding="utf-8") as f:
            index = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        index = {"transcripts": []}

    # Add to index with summary
    index["transcripts"].append(
        {
            "id": transcript_id,
            "original_filename": filename,
            "created_at": timestamp.isoformat(),
            "language": metadata.get("language", "unknown"),
            "duration": metadata.get("duration", 0),
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
        }
    )

    # Sort by creation date (newest first)
    index["transcripts"].sort(key=lambda x: x["created_at"], reverse=True)

    # Save updated index
    with open(app.config["TRANSCRIPTS_INDEX"], "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    return transcript_id


@app.route("/")
def index():
    """Render the main page of the application.

    Returns:
        str: Rendered HTML template.
    """
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload and transcription.

    Returns:
        flask.Response: JSON response with transcription results or error message.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Save the uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        try:
            # Transcribe the audio using the simplified approach
            result = process_audio(filepath)

            # Prepare metadata
            metadata = {
                "language": result.get("language", "unknown"),
                "duration": result.get(
                    "duration", 0
                ),  # Duration is provided by transcribe
                "model": "large-v3",
                "device": DEVICE,
                "audio_format": os.path.splitext(file.filename)[1][1:],
                "original_filename": file.filename,
                "file_size": os.path.getsize(filepath),
            }

            # Save transcript with metadata and segments
            transcript_id = save_transcript(
                filename, result["text"], metadata, result["segments"]
            )

            # Read the saved transcript to return complete data
            transcript_file = os.path.join(
                app.config["TRANSCRIPTS_FOLDER"], f"{transcript_id}.json"
            )
            with open(transcript_file, "r", encoding="utf-8") as f:
                transcript_data = json.load(f)

            return jsonify({"success": True, "transcript": transcript_data})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Failed to process file"}), 400


@app.route("/transcripts")
def get_transcripts():
    """Get list of all transcripts.

    Returns:
        flask.Response: JSON response containing all transcripts.
    """
    try:
        with open(app.config["TRANSCRIPTS_INDEX"], "r", encoding="utf-8") as f:
            index = json.load(f)
        return jsonify(index)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"transcripts": []})


@app.route("/transcripts/<transcript_id>")
def get_transcript(transcript_id):
    """Get a specific transcript by ID.

    Args:
        transcript_id (str): ID of the transcript to retrieve.

    Returns:
        flask.Response: JSON response containing the transcript data.
    """
    transcript_file = os.path.join(
        app.config["TRANSCRIPTS_FOLDER"], f"{transcript_id}.json"
    )
    try:
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript = json.load(f)
        return jsonify(transcript)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Transcript not found"}), 404


@app.route("/download/transcript/<transcript_id>")
def download_transcript(transcript_id):
    """Download transcript as a text file.

    Args:
        transcript_id (str): ID of the transcript to download.

    Returns:
        flask.Response: Text file download response.
    """
    transcript_file = os.path.join(
        app.config["TRANSCRIPTS_FOLDER"], f"{transcript_id}.txt"
    )
    try:
        return send_file(
            transcript_file,
            as_attachment=True,
            download_name=f"transcript_{transcript_id}.txt",
        )
    except FileNotFoundError:
        return jsonify({"error": "Transcript file not found"}), 404


@app.route("/download/audio/<path:filename>")
def download_audio(filename):
    """Download original audio file.

    Args:
        filename (str): Name of the audio file to download.

    Returns:
        flask.Response: Audio file download response.
    """
    try:
        return send_from_directory(
            app.config["UPLOAD_FOLDER"], filename, as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({"error": "Audio file not found"}), 404


if __name__ == "__main__":
    print(f"Running on {platform.system()} using {DEVICE}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Transcripts folder: {app.config['TRANSCRIPTS_FOLDER']}")
    app.run(debug=True)
