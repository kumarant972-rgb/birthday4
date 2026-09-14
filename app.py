import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATABASE = os.path.join(BASE_DIR, "birthday.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "replace-this-secret-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024

ADMIN_PASSWORD = os.environ.get("BIRTHDAY_ADMIN_PASSWORD", "Birthday@2026#M7x!")

VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "m4v"}
AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "m4a"}
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def initialize_database():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year TEXT NOT NULL,
            title TEXT NOT NULL,
            movie_filename TEXT NOT NULL,
            song_filename TEXT,
            cover_filename TEXT,
            created_at TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()


def allowed_file(filename, extensions):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in extensions
    )


def admin_required(view):
    @wraps(view)
    def protected_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return protected_view


@app.route("/")
def index():
    db = get_db()
    memories = db.execute(
        "SELECT * FROM memories ORDER BY year DESC, id DESC"
    ).fetchall()
    db.close()

    years = sorted({memory["year"] for memory in memories}, reverse=True)
    return render_template("index.html", memories=memories, years=years)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        flash("Incorrect password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin():
    db = get_db()
    memories = db.execute(
        "SELECT * FROM memories ORDER BY year DESC, id DESC"
    ).fetchall()
    db.close()
    return render_template("admin.html", memories=memories)


@app.route("/upload", methods=["POST"])
@admin_required
def upload():
    year = request.form.get("year", "").strip()
    title = request.form.get("title", "").strip() or "Birthday Memories"
    movie = request.files.get("movie")
    song = request.files.get("song")
    cover = request.files.get("cover")

    if not year:
        flash("Please enter the memory year.", "error")
        return redirect(url_for("admin"))

    if not movie or not movie.filename:
        flash("Please select a complete movie video.", "error")
        return redirect(url_for("admin"))

    if not allowed_file(movie.filename, VIDEO_EXTENSIONS):
        flash("Movie must be MP4, WEBM, MOV or M4V.", "error")
        return redirect(url_for("admin"))

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")

    movie_filename = secure_filename(
        f"{timestamp}_movie_{movie.filename}"
    )
    movie.save(os.path.join(UPLOAD_FOLDER, movie_filename))

    song_filename = None
    if song and song.filename:
        if not allowed_file(song.filename, AUDIO_EXTENSIONS):
            flash("Song must be MP3, WAV, OGG or M4A.", "error")
            return redirect(url_for("admin"))

        song_filename = secure_filename(
            f"{timestamp}_song_{song.filename}"
        )
        song.save(os.path.join(UPLOAD_FOLDER, song_filename))

    cover_filename = None
    if cover and cover.filename:
        if not allowed_file(cover.filename, IMAGE_EXTENSIONS):
            flash("Cover photo format is not supported.", "error")
            return redirect(url_for("admin"))

        cover_filename = secure_filename(
            f"{timestamp}_cover_{cover.filename}"
        )
        cover.save(os.path.join(UPLOAD_FOLDER, cover_filename))

    db = get_db()
    db.execute("""
        INSERT INTO memories
        (year, title, movie_filename, song_filename, cover_filename, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        year,
        title,
        movie_filename,
        song_filename,
        cover_filename,
        datetime.now().isoformat(timespec="seconds")
    ))
    db.commit()
    db.close()

    flash("Birthday movie uploaded successfully.", "success")
    return redirect(url_for("admin"))


@app.route("/delete/<int:memory_id>", methods=["POST"])
@admin_required
def delete_memory(memory_id):
    db = get_db()
    memory = db.execute(
        "SELECT * FROM memories WHERE id = ?",
        (memory_id,)
    ).fetchone()

    if memory:
        for filename in (
            memory["movie_filename"],
            memory["song_filename"],
            memory["cover_filename"]
        ):
            if filename:
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

        db.execute(
            "DELETE FROM memories WHERE id = ?",
            (memory_id,)
        )
        db.commit()

    db.close()
    flash("Memory deleted.", "success")
    return redirect(url_for("admin"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


initialize_database()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
