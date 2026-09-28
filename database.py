import sqlite3
from pathlib import Path


# =========================================================
# CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "lecturelens.db"


# =========================================================
# CONNECTION
# =========================================================

def get_connection():
    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =========================================================
# INITIALIZE
# =========================================================

def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT DEFAULT '',
            professor TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            original_filename TEXT,
            media_path TEXT,
            duration REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (course_id)
                REFERENCES courses(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcript_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id INTEGER NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            text TEXT NOT NULL,

            FOREIGN KEY (lecture_id)
                REFERENCES lectures(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lecture_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id INTEGER NOT NULL UNIQUE,
            study_notes TEXT,
            exam_signals TEXT,

            FOREIGN KEY (lecture_id)
                REFERENCES lectures(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()

    print(f"Database ready: {DATABASE}")


# =========================================================
# COURSES
# =========================================================

def create_course(
    name,
    code="",
    professor=""
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO courses (
            name,
            code,
            professor
        )
        VALUES (?, ?, ?)
        """,
        (
            name.strip(),
            code.strip(),
            professor.strip()
        )
    )

    course_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return course_id


def get_courses():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            courses.id,
            courses.name,
            courses.code,
            courses.professor,
            courses.created_at,

            COUNT(lectures.id)
                AS lecture_count

        FROM courses

        LEFT JOIN lectures
            ON lectures.course_id = courses.id

        GROUP BY
            courses.id,
            courses.name,
            courses.code,
            courses.professor,
            courses.created_at

        ORDER BY
            courses.created_at DESC,
            courses.id DESC
    """)

    courses = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return courses


def get_course(course_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            courses.id,
            courses.name,
            courses.code,
            courses.professor,
            courses.created_at,

            COUNT(lectures.id)
                AS lecture_count

        FROM courses

        LEFT JOIN lectures
            ON lectures.course_id = courses.id

        WHERE courses.id = ?

        GROUP BY
            courses.id,
            courses.name,
            courses.code,
            courses.professor,
            courses.created_at
        """,
        (course_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def delete_course(course_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM courses
        WHERE id = ?
        """,
        (course_id,)
    )

    deleted = (
        cursor.rowcount > 0
    )

    connection.commit()
    connection.close()

    return deleted


# =========================================================
# LECTURES
# =========================================================

def create_lecture(
    course_id,
    title,
    original_filename="",
    media_path="",
    duration=0
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO lectures (
            course_id,
            title,
            original_filename,
            media_path,
            duration
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            course_id,
            title.strip(),
            original_filename,
            media_path,
            duration
        )
    )

    lecture_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return lecture_id


def update_lecture_duration(
    lecture_id,
    duration
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE lectures

        SET duration = ?

        WHERE id = ?
        """,
        (
            duration,
            lecture_id
        )
    )

    connection.commit()
    connection.close()


def get_lectures_for_course(
    course_id
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            course_id,
            title,
            original_filename,
            media_path,
            duration,
            created_at

        FROM lectures

        WHERE course_id = ?

        ORDER BY
            created_at DESC,
            id DESC
        """,
        (course_id,)
    )

    lectures = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return lectures


def get_lecture(lecture_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            course_id,
            title,
            original_filename,
            media_path,
            duration,
            created_at

        FROM lectures

        WHERE id = ?
        """,
        (lecture_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def delete_lecture(lecture_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM lectures
        WHERE id = ?
        """,
        (lecture_id,)
    )

    deleted = (
        cursor.rowcount > 0
    )

    connection.commit()
    connection.close()

    return deleted


# =========================================================
# TRANSCRIPT
# =========================================================

def save_transcript_segments(
    lecture_id,
    segments
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM transcript_segments
        WHERE lecture_id = ?
        """,
        (lecture_id,)
    )

    rows = []

    for segment in segments:
        rows.append(
            (
                lecture_id,
                segment["start"],
                segment["end"],
                segment["text"]
            )
        )

    cursor.executemany(
        """
        INSERT INTO transcript_segments (
            lecture_id,
            start_time,
            end_time,
            text
        )
        VALUES (?, ?, ?, ?)
        """,
        rows
    )

    connection.commit()
    connection.close()


def get_transcript_segments(
    lecture_id
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            lecture_id,
            start_time,
            end_time,
            text

        FROM transcript_segments

        WHERE lecture_id = ?

        ORDER BY
            start_time ASC,
            id ASC
        """,
        (lecture_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# GENERATED CONTENT
# =========================================================

def save_study_notes(
    lecture_id,
    study_notes
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO lecture_content (
            lecture_id,
            study_notes
        )

        VALUES (?, ?)

        ON CONFLICT(lecture_id)
        DO UPDATE SET
            study_notes =
                excluded.study_notes
        """,
        (
            lecture_id,
            study_notes
        )
    )

    connection.commit()
    connection.close()


def save_exam_signals(
    lecture_id,
    exam_signals
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO lecture_content (
            lecture_id,
            exam_signals
        )

        VALUES (?, ?)

        ON CONFLICT(lecture_id)
        DO UPDATE SET
            exam_signals =
                excluded.exam_signals
        """,
        (
            lecture_id,
            exam_signals
        )
    )

    connection.commit()
    connection.close()


def get_lecture_content(
    lecture_id
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            lecture_id,
            study_notes,
            exam_signals

        FROM lecture_content

        WHERE lecture_id = ?
        """,
        (lecture_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return {
            "lecture_id":
                lecture_id,

            "study_notes":
                None,

            "exam_signals":
                None
        }

    return dict(row)