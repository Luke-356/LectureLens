# LectureLens

**Your lectures, understood.**

LectureLens is a local AI-powered learning application that transforms lecture recordings into searchable, timestamped learning material.

Instead of treating a lecture as a recording students rarely revisit, LectureLens turns it into an interactive study resource. Students can organize lectures by course, search what their professor said, generate study guides, ask questions about a lecture, identify evidence-backed study signals, and jump directly from AI-generated timestamp citations to the relevant moment in the original recording.

> **Core idea:** AI study tools should not just give students answers. They should show where those answers came from.

---

## 🚀 Current Version — v0.3

LectureLens currently supports persistent courses and lectures.

Students can create courses, upload audio or video lectures, transcribe them locally, and return to their saved learning material even after restarting the application.

### Current Features

- 📚 **Course Organization**
  - Create and manage individual courses
  - Organize multiple lectures under each course
  - Persistent course storage with SQLite

- 🎙️ **Audio & Video Lecture Processing**
  - Upload MP3, M4A, WAV, MP4, MOV, WEBM, AAC, and FLAC recordings
  - Process lecture audio using FFmpeg
  - Local transcription with OpenAI Whisper

- 📝 **Timestamped Transcripts**
  - Automatically divide lectures into timestamped transcript segments
  - Search the transcript
  - Click a timestamp to jump directly to that moment in the original recording

- ✦ **AI Study Guides**
  - Generate structured study material from the lecture
  - Identify key concepts
  - Preserve professor examples and explanations
  - Highlight important takeaways
  - Include timestamp citations linking back to the recording

- 💬 **Ask Lecture**
  - Ask questions about a specific lecture
  - Answers are grounded in the lecture transcript
  - Responses include timestamp evidence
  - The AI avoids filling gaps with unrelated outside information

- ◎ **Exam Signals**
  - Detect concepts the professor emphasized
  - Identify repeated definitions and explanations
  - Surface warnings, common mistakes, and explicit exam references
  - Provide evidence with timestamps
  - Exam Signals are study signals, not exam predictions

- 💾 **Persistent Lecture Storage**
  - Courses survive application restarts
  - Lecture metadata is stored in SQLite
  - Transcript segments are stored permanently
  - Generated study guides are saved
  - Exam Signals are saved
  - Original lecture recordings remain available for playback

- 🔒 **Local AI**
  - Whisper runs locally
  - Ollama runs the language model locally
  - No paid AI API is required for the current version

---

## 🧠 How LectureLens Works

```text
Create Course
      │
      ▼
Upload Lecture
      │
      ▼
Audio / Video
      │
      ▼
FFmpeg Processing
      │
      ▼
Whisper Transcription
      │
      ▼
Timestamped Transcript
      │
      ├──────────────┬───────────────┐
      ▼              ▼               ▼
 Study Guide     Ask Lecture     Exam Signals
      │              │               │
      └──────────────┼───────────────┘
                     ▼
                  SQLite
                     │
                     ▼
             Persistent Course
```

---

## 💡 Why LectureLens?

Many AI study tools focus on generating summaries, flashcards, or generic answers.

LectureLens is being designed around a different principle:

### Every important insight should be connected to evidence.

If LectureLens says a concept was emphasized, students should be able to see **why**.

If an AI answer references something the professor explained, students should be able to jump directly to the relevant moment in the lecture.

For example:

```text
Professor Emphasis

Active Transport
Strong Signal

Why?

[18:42] Professor introduces the concept
[27:16] Definition repeated
[32:11] Compared with facilitated diffusion
[41:05] Professor emphasizes the distinction
```

Clicking a timestamp returns the student directly to that point in the original recording.

---

## 🎯 Product Vision

LectureLens is evolving from a lecture transcription application into a **course intelligence system**.

The long-term goal is for LectureLens to understand:

```text
What the professor taught
          +
What the professor emphasized
          +
How concepts connect across lectures
          +
What the student understands
          +
What the student struggles with
          │
          ▼
What should the student study next?
```

Instead of treating every lecture independently, LectureLens will build an understanding of the entire course over time.

---

## 🧩 Planned Course Intelligence

Future versions will extract and connect concepts across all lectures in a course.

Example:

```text
BIO 181
Anatomy & Physiology I

                 Cell Membrane
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    Phospholipids               Transport
                                    │
                          ┌─────────┴─────────┐
                          ▼                   ▼
                       Passive             Active
```

Each concept will eventually be connected to:

- Lectures where it appeared
- Exact timestamps
- Professor explanations
- Repetition frequency
- Professor emphasis
- Related concepts
- Student practice performance
- Student mastery

---

## 🔄 Future Learning Loop

LectureLens is being designed around an evidence-backed active learning loop:

```text
Professor
    │
    ▼
Lecture
    │
    ▼
Concept
    │
    ▼
Student Practices
    │
    ▼
Student Makes Mistake
    │
    ▼
LectureLens Detects Weak Concept
    │
    ▼
Return to Exact Professor Explanation
    │
    ▼
Student Practices Again
    │
    ▼
Mastery Improves
```

This allows the original lecture recording to become an active part of studying instead of passive storage.

---

# 🗺️ Roadmap

## v0.1 — Transcription

- Audio/video upload
- Local Whisper transcription
- Processing progress

## v0.2 — Lecture Intelligence

- Timestamped transcripts
- Searchable transcript
- Recording playback
- Clickable timestamps
- AI Study Guide
- Ask Lecture
- Exam Signals
- Local Ollama integration

## v0.3 — Courses & Persistence

- Course dashboard
- Create courses
- Multiple lectures per course
- SQLite database
- Persistent lecture recordings
- Persistent transcripts
- Persistent Study Guides
- Persistent Exam Signals
- Reopen previously processed lectures

## v0.4 — Course Intelligence

Planned:

- Automatic concept extraction
- Cross-lecture concept matching
- Concept relationships
- Professor emphasis analysis
- Evidence-backed concept pages
- Cross-lecture timestamp references
- Course knowledge map

## v0.5 — Active Learning

Planned:

- Concept-based practice questions
- Active recall
- Flashcards
- Quiz generation
- Answer tracking
- Concept mastery tracking

## v0.6 — Weakness Engine

Planned:

- Detect weak concepts
- Identify recurring misconceptions
- Connect incorrect answers to course concepts
- Return students to exact professor explanations
- Personalized remediation

## v0.7 — Exam Mode

Planned:

- Exam date and coverage
- Course-wide study priorities
- Professor emphasis + student mastery analysis
- Personalized study sessions
- Evidence-backed review recommendations
- Progress tracking

---

# 🛠️ Technology Stack

## Backend

- Python
- Flask
- SQLite

## AI

- OpenAI Whisper
- Ollama
- Llama 3.2

## Media Processing

- FFmpeg
- FFprobe

## Frontend

- HTML
- CSS
- JavaScript

The current interface is intentionally lightweight and dependency-free while the core product architecture is being developed.

---

# 📁 Project Structure

```text
LectureLens/
│
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   └── index.html
│
├── uploads/
│
└── lecturelens.db
```

`uploads/` and `lecturelens.db` contain local application data and should not be committed to Git.

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Luke-356/LectureLens.git
cd LectureLens
```

## 2. Create a Virtual Environment

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

# 🎬 Install FFmpeg

LectureLens uses FFmpeg and FFprobe to process lecture recordings.

## macOS

Using Homebrew:

```bash
brew install ffmpeg
```

Verify:

```bash
ffmpeg -version
ffprobe -version
```

## Windows

Install FFmpeg and make sure the FFmpeg binaries are available through your system `PATH`.

---

# 🤖 Install Ollama

LectureLens currently uses Ollama to run the language model locally.

After installing Ollama, download the current model:

```bash
ollama pull llama3.2
```

Verify that Ollama is running:

```bash
ollama list
```

---

# ▶️ Run LectureLens

Activate the virtual environment:

```bash
source venv/bin/activate
```

Start the Flask application:

```bash
python app.py
```

You should see output similar to:

```text
Database ready: .../LectureLens/lecturelens.db
Loading Whisper...
Whisper ready.
```

Then open:

```text
http://127.0.0.1:5000
```

---

# 💾 Local Data

LectureLens automatically creates:

```text
lecturelens.db
```

This SQLite database stores:

- Courses
- Lectures
- Transcript segments
- Study Guides
- Exam Signals

Uploaded lecture recordings are stored locally inside:

```text
uploads/
```

These files are intentionally excluded from Git.

---

# 🔐 Privacy

The current version of LectureLens is designed as a **local-first application**.

Lecture transcription and AI study features can run on the user's machine using Whisper and Ollama rather than requiring lecture content to be sent to a paid third-party AI API.

This architecture is especially relevant for educational recordings that may contain private classroom discussions or student information.

LectureLens is still under active development and should not yet be treated as a production security or privacy solution.

---

# ⚠️ Current Limitations

LectureLens v0.3 is an early development version.

Current limitations include:

- Flask development server is not intended for production deployment
- Whisper processing can be slow without suitable hardware
- Long transcripts may exceed the local language model's effective context window
- Ask Lecture currently uses the full lecture transcript rather than a retrieval system
- AI-generated timestamp citations are not yet independently validated
- Transcription currently uses fixed audio chunks
- Multi-user authentication is not implemented
- Cloud synchronization is not implemented
- Background processing is not yet handled by a production job queue

These areas are planned for future development.

---

# 🧭 Development Philosophy

LectureLens is being built around four principles:

### Evidence over hallucination

AI-generated learning material should remain connected to the student's actual course material.

### Active learning over passive summaries

Students should eventually practice, retrieve, answer, fail, retry, and improve rather than simply read AI-generated notes.

### Course understanding over isolated files

A semester is a connected body of knowledge, not a folder full of unrelated recordings.

### Useful AI over AI for its own sake

AI features should solve a real learning problem rather than exist simply because a model can generate text.

---

# 📌 Status

LectureLens is currently under active development.

**Current milestone:** `v0.3 — Courses & Persistent Lectures`

**Next milestone:** `v0.4 — Course Intelligence`

---

# 👨‍💻 Author

**Nyi Nyi Lwin (Luke)**

Computer Science graduate building LectureLens around the intersection of AI, software engineering, and learning technology.

---

# 📄 License

A license has not yet been selected for LectureLens.

All rights reserved unless otherwise stated.
