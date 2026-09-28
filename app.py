from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    Response,
    send_file
)

from werkzeug.utils import secure_filename

import whisper
import subprocess
import threading
import requests
import tempfile
import uuid
import json
import math
import os
import time

from database import (
    initialize_database,

    create_course,
    get_courses,
    get_course,
    delete_course,

    create_lecture,
    update_lecture_duration,
    get_lectures_for_course,
    get_lecture,
    delete_lecture,

    save_transcript_segments,
    get_transcript_segments,

    save_study_notes,
    save_exam_signals,
    get_lecture_content
)


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config[
    "UPLOAD_FOLDER"
] = UPLOAD_FOLDER

app.config[
    "MAX_CONTENT_LENGTH"
] = (
    2 * 1024 * 1024 * 1024
)


# =========================================================
# DATABASE
# =========================================================

initialize_database()


# =========================================================
# MEDIA
# =========================================================

ALLOWED_EXTENSIONS = {
    ".mp3",
    ".m4a",
    ".wav",
    ".mp4",
    ".mov",
    ".webm",
    ".aac",
    ".flac"
}


# =========================================================
# AI
# =========================================================

WHISPER_MODEL = "small"

OLLAMA_MODEL = "llama3.2"

OLLAMA_URL = (
    "http://localhost:11434/api/generate"
)


# =========================================================
# WHISPER
# =========================================================

print(
    "Loading Whisper..."
)

whisper_model = (
    whisper.load_model(
        WHISPER_MODEL
    )
)

print(
    "Whisper ready."
)


# =========================================================
# ACTIVE JOBS
# =========================================================

jobs = {}


# =========================================================
# HELPERS
# =========================================================

def format_timestamp(seconds):

    seconds = int(
        seconds
    )

    hours = (
        seconds // 3600
    )

    minutes = (
        seconds % 3600
    ) // 60

    secs = (
        seconds % 60
    )

    if hours:

        return (
            f"{hours:02}:"
            f"{minutes:02}:"
            f"{secs:02}"
        )

    return (
        f"{minutes:02}:"
        f"{secs:02}"
    )


def allowed_file(filename):

    extension = (
        os.path.splitext(
            filename
        )[1].lower()
    )

    return (
        extension
        in ALLOWED_EXTENSIONS
    )


def get_duration(file_path):

    command = [
        "ffprobe",
        "-v",
        "error",

        "-show_entries",
        "format=duration",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        file_path
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if (
        result.returncode
        != 0
    ):

        raise Exception(
            "Unable to read this recording."
        )

    output = (
        result.stdout.strip()
    )

    if not output:

        raise Exception(
            "Unable to determine recording duration."
        )

    return float(
        output
    )


def transcript_for_ai(
    segments
):

    lines = []

    for segment in segments:

        lines.append(
            f"[{segment['timestamp']}] "
            f"{segment['text']}"
        )

    return "\n".join(
        lines
    )


def database_segments_for_ai(
    lecture_id
):

    rows = (
        get_transcript_segments(
            lecture_id
        )
    )

    segments = []

    for row in rows:

        segments.append({
            "start":
                row["start_time"],

            "end":
                row["end_time"],

            "timestamp":
                format_timestamp(
                    row["start_time"]
                ),

            "text":
                row["text"]
        })

    return segments


def ask_ollama(prompt):

    try:

        response = requests.post(
            OLLAMA_URL,

            json={
                "model":
                    OLLAMA_MODEL,

                "prompt":
                    prompt,

                "stream":
                    False,

                "options": {
                    "temperature":
                        0.15
                }
            },

            timeout=300
        )

        response.raise_for_status()

        return (
            response
            .json()["response"]
            .strip()
        )

    except requests.exceptions.ConnectionError:

        raise Exception(
            "LectureLens could not connect "
            "to Ollama. Make sure Ollama "
            "is running."
        )

    except requests.exceptions.Timeout:

        raise Exception(
            "The local AI took too long "
            "to respond."
        )

    except requests.RequestException as e:

        raise Exception(
            f"Local AI error: {str(e)}"
        )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# COURSES
# =========================================================

@app.route(
    "/api/courses",
    methods=["GET"]
)
def api_get_courses():

    return jsonify({
        "courses":
            get_courses()
    })


@app.route(
    "/api/courses",
    methods=["POST"]
)
def api_create_course():

    data = (
        request.get_json()
        or {}
    )

    name = data.get(
        "name",
        ""
    ).strip()

    code = data.get(
        "code",
        ""
    ).strip()

    professor = data.get(
        "professor",
        ""
    ).strip()

    if not name:

        return jsonify({
            "error":
                "Course name is required."
        }), 400

    course_id = (
        create_course(
            name,
            code,
            professor
        )
    )

    return jsonify({
        "success":
            True,

        "course":
            get_course(
                course_id
            )
    }), 201


@app.route(
    "/api/courses/<int:course_id>",
    methods=["GET"]
)
def api_get_course(course_id):

    course = get_course(
        course_id
    )

    if not course:

        return jsonify({
            "error":
                "Course not found."
        }), 404

    return jsonify({
        "course":
            course,

        "lectures":
            get_lectures_for_course(
                course_id
            )
    })


@app.route(
    "/api/courses/<int:course_id>",
    methods=["DELETE"]
)
def api_delete_course(course_id):

    lectures = (
        get_lectures_for_course(
            course_id
        )
    )

    for lecture in lectures:

        media_path = (
            lecture.get(
                "media_path"
            )
        )

        if (
            media_path
            and
            os.path.exists(
                media_path
            )
        ):

            try:
                os.remove(
                    media_path
                )
            except OSError:
                pass

    deleted = (
        delete_course(
            course_id
        )
    )

    if not deleted:

        return jsonify({
            "error":
                "Course not found."
        }), 404

    return jsonify({
        "success":
            True
    })


# =========================================================
# SAVED LECTURE API
# =========================================================

@app.route(
    "/api/lectures/<int:lecture_id>",
    methods=["GET"]
)
def api_get_lecture(
    lecture_id
):

    lecture = get_lecture(
        lecture_id
    )

    if not lecture:

        return jsonify({
            "error":
                "Lecture not found."
        }), 404

    segments = (
        database_segments_for_ai(
            lecture_id
        )
    )

    content = (
        get_lecture_content(
            lecture_id
        )
    )

    return jsonify({
        "lecture":
            lecture,

        "segments":
            segments,

        "study_notes":
            content.get(
                "study_notes"
            ),

        "exam_signals":
            content.get(
                "exam_signals"
            )
    })


@app.route(
    "/api/lectures/<int:lecture_id>",
    methods=["DELETE"]
)
def api_delete_lecture(
    lecture_id
):

    lecture = get_lecture(
        lecture_id
    )

    if not lecture:

        return jsonify({
            "error":
                "Lecture not found."
        }), 404

    media_path = lecture.get(
        "media_path"
    )

    if (
        media_path
        and
        os.path.exists(
            media_path
        )
    ):

        try:

            os.remove(
                media_path
            )

        except OSError:

            pass

    delete_lecture(
        lecture_id
    )

    return jsonify({
        "success":
            True
    })


@app.route(
    "/saved-media/<int:lecture_id>"
)
def saved_media(
    lecture_id
):

    lecture = get_lecture(
        lecture_id
    )

    if not lecture:

        return (
            "Lecture not found.",
            404
        )

    file_path = lecture.get(
        "media_path"
    )

    if (
        not file_path
        or
        not os.path.exists(
            file_path
        )
    ):

        return (
            "Recording not found.",
            404
        )

    return send_file(
        file_path,
        conditional=True
    )


# =========================================================
# START TRANSCRIPTION
# =========================================================

@app.route(
    "/transcribe",
    methods=["POST"]
)
def start_transcription():

    if (
        "media"
        not in request.files
    ):

        return jsonify({
            "error":
                "No recording was uploaded."
        }), 400

    file = request.files[
        "media"
    ]

    if not file.filename:

        return jsonify({
            "error":
                "Choose a recording first."
        }), 400

    if not allowed_file(
        file.filename
    ):

        return jsonify({
            "error":
                "Unsupported file type."
        }), 400

    try:

        course_id = int(
            request.form.get(
                "course_id",
                ""
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error":
                "A valid course is required."
        }), 400

    course = get_course(
        course_id
    )

    if not course:

        return jsonify({
            "error":
                "Course not found."
        }), 404

    original_name = (
        secure_filename(
            file.filename
        )
    )

    extension = (
        os.path.splitext(
            original_name
        )[1].lower()
    )

    title = (
        os.path.splitext(
            original_name
        )[0]
    )

    unique_name = (
        f"{uuid.uuid4()}"
        f"{extension}"
    )

    file_path = os.path.join(
        app.config[
            "UPLOAD_FOLDER"
        ],
        unique_name
    )

    file.save(
        file_path
    )

    try:

        lecture_id = (
            create_lecture(
                course_id=
                    course_id,

                title=
                    title,

                original_filename=
                    original_name,

                media_path=
                    file_path,

                duration=
                    0
            )
        )

    except Exception:

        if os.path.exists(
            file_path
        ):

            os.remove(
                file_path
            )

        raise

    job_id = str(
        uuid.uuid4()
    )

    jobs[job_id] = {

        "lecture_id":
            lecture_id,

        "course_id":
            course_id,

        "progress":
            0,

        "status":
            "Preparing lecture...",

        "finished":
            False,

        "error":
            None,

        "segments":
            [],

        "original_name":
            original_name,

        "file_path":
            file_path,

        "extension":
            extension,

        "duration":
            0,

        "notes":
            None,

        "signals":
            None
    }

    thread = threading.Thread(
        target=
            transcribe_media,

        args=(
            job_id,
        ),

        daemon=True
    )

    thread.start()

    return jsonify({

        "job_id":
            job_id,

        "lecture_id":
            lecture_id,

        "filename":
            original_name
    })


# =========================================================
# TRANSCRIBE
# =========================================================

def transcribe_media(
    job_id
):

    job = jobs.get(
        job_id
    )

    if not job:
        return

    file_path = (
        job["file_path"]
    )

    lecture_id = (
        job["lecture_id"]
    )

    chunk_length = 30

    try:

        job["status"] = (
            "Reading recording..."
        )

        duration = (
            get_duration(
                file_path
            )
        )

        job["duration"] = (
            duration
        )

        update_lecture_duration(
            lecture_id,
            duration
        )

        total_chunks = max(
            1,

            math.ceil(
                duration
                /
                chunk_length
            )
        )

        all_segments = []

        for chunk_index in range(
            total_chunks
        ):

            start_time = (
                chunk_index
                *
                chunk_length
            )

            with (
                tempfile
                .NamedTemporaryFile(
                    suffix=".wav",
                    delete=False
                )
            ) as temp:

                chunk_file = (
                    temp.name
                )

            try:

                command = [
                    "ffmpeg",
                    "-y",

                    "-ss",
                    str(
                        start_time
                    ),

                    "-i",
                    file_path,

                    "-t",
                    str(
                        chunk_length
                    ),

                    "-vn",

                    "-ar",
                    "16000",

                    "-ac",
                    "1",

                    chunk_file
                ]

                conversion = (
                    subprocess.run(
                        command,

                        stdout=
                            subprocess.DEVNULL,

                        stderr=
                            subprocess.DEVNULL
                    )
                )

                if (
                    conversion.returncode
                    != 0
                ):

                    raise Exception(
                        "FFmpeg could not "
                        "process this recording."
                    )

                job["status"] = (
                    "Listening · "
                    f"{chunk_index + 1} "
                    f"of {total_chunks}"
                )

                result = (
                    whisper_model
                    .transcribe(
                        chunk_file,
                        fp16=False,
                        verbose=False
                    )
                )

                for segment in (
                    result["segments"]
                ):

                    text = (
                        segment[
                            "text"
                        ].strip()
                    )

                    if not text:
                        continue

                    absolute_start = (
                        start_time
                        +
                        segment["start"]
                    )

                    absolute_end = (
                        start_time
                        +
                        segment["end"]
                    )

                    all_segments.append({

                        "start":
                            round(
                                absolute_start,
                                2
                            ),

                        "end":
                            round(
                                absolute_end,
                                2
                            ),

                        "timestamp":
                            format_timestamp(
                                absolute_start
                            ),

                        "text":
                            text
                    })

                job["segments"] = (
                    all_segments.copy()
                )

                job["progress"] = int(
                    (
                        (
                            chunk_index
                            + 1
                        )
                        /
                        total_chunks
                    )
                    * 100
                )

            finally:

                if os.path.exists(
                    chunk_file
                ):

                    try:
                        os.remove(
                            chunk_file
                        )
                    except OSError:
                        pass

        # =============================================
        # PERMANENTLY SAVE TRANSCRIPT
        # =============================================

        job["status"] = (
            "Saving lecture..."
        )

        save_transcript_segments(
            lecture_id,
            all_segments
        )

        job["progress"] = 100

        job["status"] = (
            "Lecture saved"
        )

        job["finished"] = (
            True
        )

    except Exception as e:

        job["error"] = (
            str(e)
        )

        job["status"] = (
            "Processing failed"
        )

        job["finished"] = (
            True
        )


# =========================================================
# PROGRESS
# =========================================================

@app.route(
    "/progress/<job_id>"
)
def progress(job_id):

    def generate():

        while True:

            job = jobs.get(
                job_id
            )

            if not job:

                yield (
                    "data: "
                    +
                    json.dumps({
                        "error":
                            "Lecture not found.",

                        "finished":
                            True
                    })
                    +
                    "\n\n"
                )

                break

            payload = {

                "lecture_id":
                    job.get(
                        "lecture_id"
                    ),

                "progress":
                    job["progress"],

                "status":
                    job["status"],

                "finished":
                    job["finished"],

                "error":
                    job["error"],

                "segments":
                    job["segments"],

                "duration":
                    job["duration"]
            }

            yield (
                "data: "
                +
                json.dumps(
                    payload
                )
                +
                "\n\n"
            )

            if job[
                "finished"
            ]:
                break

            time.sleep(
                0.8
            )

    return Response(
        generate(),

        mimetype=
            "text/event-stream",

        headers={
            "Cache-Control":
                "no-cache",

            "X-Accel-Buffering":
                "no"
        }
    )


# =========================================================
# ACTIVE MEDIA
# =========================================================

@app.route(
    "/media/<job_id>"
)
def media(job_id):

    job = jobs.get(
        job_id
    )

    if not job:

        return (
            "Lecture not found.",
            404
        )

    file_path = (
        job["file_path"]
    )

    if not os.path.exists(
        file_path
    ):

        return (
            "Recording not found.",
            404
        )

    return send_file(
        file_path,
        conditional=True
    )


# =========================================================
# STUDY NOTES - ACTIVE JOB
# =========================================================

@app.route(
    "/study-notes/<job_id>",
    methods=["POST"]
)
def study_notes(job_id):

    job = jobs.get(
        job_id
    )

    if not job:

        return jsonify({
            "error":
                "Lecture not found."
        }), 404

    lecture_id = (
        job["lecture_id"]
    )

    saved_content = (
        get_lecture_content(
            lecture_id
        )
    )

    if saved_content.get(
        "study_notes"
    ):

        job["notes"] = (
            saved_content[
                "study_notes"
            ]
        )

        return jsonify({
            "notes":
                job["notes"]
        })

    transcript = (
        transcript_for_ai(
            job["segments"]
        )
    )

    try:

        notes = (
            generate_study_notes(
                transcript
            )
        )

        job["notes"] = (
            notes
        )

        save_study_notes(
            lecture_id,
            notes
        )

        return jsonify({
            "notes":
                notes
        })

    except Exception as e:

        return jsonify({
            "error":
                str(e)
        }), 500


# =========================================================
# STUDY NOTES - SAVED LECTURE
# =========================================================

@app.route(
    "/api/lectures/<int:lecture_id>/study-notes",
    methods=["POST"]
)
def saved_study_notes(
    lecture_id
):

    lecture = get_lecture(
        lecture_id
    )

    if not lecture:

        return jsonify({
            "error":
                "Lecture not found."
        }), 404

    content = (
        get_lecture_content(
            lecture_id
        )
    )

    if content.get(
        "study_notes"
    ):

        return jsonify({
            "notes":
                content[
                    "study_notes"
                ]
        })

    segments = (
        database_segments_for_ai(
            lecture_id
        )
    )

    transcript = (
        transcript_for_ai(
            segments
        )
    )

    if not transcript:

        return jsonify({
            "error":
                "No transcript is available."
        }), 400

    try:

        notes = (
            generate_study_notes(
                transcript
            )
        )

        save_study_notes(
            lecture_id,
            notes
        )

        return jsonify({
            "notes":
                notes
        })

    except Exception as e:

        return jsonify({
            "error":
                str(e)
        }), 500


def generate_study_notes(
    transcript
):

    if not transcript:

        raise Exception(
            "No transcript is available."
        )

    prompt = f"""
You are LectureLens, an academic study assistant.

Create high-quality study notes using ONLY the
lecture transcript below.

Your goal is to help the student understand and
remember what their professor taught.

Use this structure:

# Overview

Give a concise explanation of the lecture.

# Key Concepts

Organize major concepts logically.

For every major concept:

- explain it clearly
- preserve important definitions
- preserve useful professor examples
- cite relevant timestamps like [12:34]

# Professor Emphasis

Identify concepts the lecturer emphasized,
repeated, warned about, or spent substantial
time explaining.

Do not predict exam questions.

# Key Takeaways

Give a concise list of the most important ideas.

RULES:

Use ONLY the transcript.
Do not invent information.
Use timestamp citations.

TRANSCRIPT:

{transcript}
"""

    return ask_ollama(
        prompt
    )


# =========================================================
# EXAM SIGNALS - ACTIVE JOB
# =========================================================

@app.route(
    "/exam-signals/<job_id>",
    methods=["POST"]
)
def exam_signals(job_id):

    job = jobs.get(
        job_id
    )

    if not job:

        return jsonify({
            "error":
                "Lecture not found."
        }), 404

    lecture_id = (
        job["lecture_id"]
    )

    content = (
        get_lecture_content(
            lecture_id
        )
    )

    if content.get(
        "exam_signals"
    ):

        job["signals"] = (
            content[
                "exam_signals"
            ]
        )

        return jsonify({
            "signals":
                job["signals"]
        })

    transcript = (
        transcript_for_ai(
            job["segments"]
        )
    )

    try:

        signals = (
            generate_exam_signals(
                transcript
            )
        )

        job["signals"] = (
            signals
        )

        save_exam_signals(
            lecture_id,
            signals
        )

        return jsonify({
            "signals":
                signals
        })

    except Exception as e:

        return jsonify({
            "error":
                str(e)
        }), 500


# =========================================================
# EXAM SIGNALS - SAVED
# =========================================================

@app.route(
    "/api/lectures/<int:lecture_id>/exam-signals",
    methods=["POST"]
)
def saved_exam_signals(
    lecture_id
):

    lecture = get_lecture(
        lecture_id
    )

    if not lecture:

        return jsonify({
            "error":
                "Lecture not found."
        }), 404

    content = (
        get_lecture_content(
            lecture_id
        )
    )

    if content.get(
        "exam_signals"
    ):

        return jsonify({
            "signals":
                content[
                    "exam_signals"
                ]
        })

    segments = (
        database_segments_for_ai(
            lecture_id
        )
    )

    transcript = (
        transcript_for_ai(
            segments
        )
    )

    try:

        signals = (
            generate_exam_signals(
                transcript
            )
        )

        save_exam_signals(
            lecture_id,
            signals
        )

        return jsonify({
            "signals":
                signals
        })

    except Exception as e:

        return jsonify({
            "error":
                str(e)
        }), 500


def generate_exam_signals(
    transcript
):

    if not transcript:

        raise Exception(
            "No transcript is available."
        )

    prompt = f"""
You are LectureLens.

Analyze this lecture for STUDY SIGNALS.

These are NOT exam predictions.

Look for:

- explicit importance statements
- explicit exam references
- repeated concepts
- repeated definitions
- detailed explanations
- warnings
- common mistakes
- repeated connections

Use this structure:

## Topic

Signal strength: Strong / Moderate / Review

Why it matters:
Explain why it was flagged.

Evidence:
[12:34] Evidence
[18:21] Evidence

---

Use ONLY the transcript.

Never claim something will appear on an exam unless
the lecturer explicitly says so.

TRANSCRIPT:

{transcript}
"""

    return ask_ollama(
        prompt
    )


# =========================================================
# ASK ACTIVE LECTURE
# =========================================================

@app.route(
    "/ask/<job_id>",
    methods=["POST"]
)
def ask_lecture(job_id):

    job = jobs.get(
        job_id
    )

    if not job:

        return jsonify({
            "error":
                "Lecture not found."
        }), 404

    data = (
        request.get_json()
        or {}
    )

    question = data.get(
        "question",
        ""
    ).strip()

    if not question:

        return jsonify({
            "error":
                "Enter a question."
        }), 400

    transcript = (
        transcript_for_ai(
            job["segments"]
        )
    )

    try:

        answer = (
            generate_answer(
                transcript,
                question
            )
        )

        return jsonify({
            "answer":
                answer
        })

    except Exception as e:

        return jsonify({
            "error":
                str(e)
        }), 500


# =========================================================
# ASK SAVED LECTURE
# =========================================================

@app.route(
    "/api/lectures/<int:lecture_id>/ask",
    methods=["POST"]
)
def ask_saved_lecture(
    lecture_id
):

    lecture = get_lecture(
        lecture_id
    )

    if not lecture:

        return jsonify({
            "error":
                "Lecture not found."
        }), 404

    data = (
        request.get_json()
        or {}
    )

    question = data.get(
        "question",
        ""
    ).strip()

    if not question:

        return jsonify({
            "error":
                "Enter a question."
        }), 400

    segments = (
        database_segments_for_ai(
            lecture_id
        )
    )

    transcript = (
        transcript_for_ai(
            segments
        )
    )

    try:

        answer = (
            generate_answer(
                transcript,
                question
            )
        )

        return jsonify({
            "answer":
                answer
        })

    except Exception as e:

        return jsonify({
            "error":
                str(e)
        }), 500


def generate_answer(
    transcript,
    question
):

    if not transcript:

        raise Exception(
            "No transcript is available."
        )

    prompt = f"""
You are LectureLens.

The student is asking about ONE specific lecture.

Answer ONLY using information supported by the
lecture transcript.

If the transcript does not contain enough information,
say:

"I couldn't find enough information about that in
this lecture."

Do not use outside knowledge to fill gaps.

Give a clear and useful explanation.

Cite relevant timestamps like [12:34].

TRANSCRIPT:

{transcript}

STUDENT QUESTION:

{question}

ANSWER:
"""

    return ask_ollama(
        prompt
    )


# =========================================================
# CLEAR ACTIVE JOB
# =========================================================

@app.route(
    "/clear/<job_id>",
    methods=["DELETE"]
)
def clear_job(job_id):

    # IMPORTANT:
    #
    # Clear now removes only the temporary job.
    # It does NOT delete the permanent lecture.

    jobs.pop(
        job_id,
        None
    )

    return jsonify({
        "success":
            True
    })


# =========================================================
# ERRORS
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    return jsonify({
        "error":
            "This recording is too large."
    }), 413


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        threaded=True,
        use_reloader=False
    )