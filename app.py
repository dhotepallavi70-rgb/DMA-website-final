import os
import sqlite3
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, flash, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = "change-this-secret-key-for-production"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "dma.db")
NOTES_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "notes")
VIDEO_FOLDER = os.path.join(BASE_DIR, "static", "videos")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "DMA@2026"

ALLOWED_NOTE_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(NOTES_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            student_class TEXT NOT NULL,
            message TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            student_class TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            student_class TEXT NOT NULL,
            filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            video_type TEXT NOT NULL,
            video_url TEXT,
            filename TEXT,
            uploaded_at TEXT NOT NULL
        )
    """)

    # Demo student login
    existing = conn.execute("SELECT id FROM students WHERE username = ?", ("student1",)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO students (name, phone, student_class, username, password, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("Demo Student", "0000000000", "Class 10", "student1", "student123", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

    conn.commit()
    conn.close()


def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please login as admin first.", "error")
            return redirect(url_for("admin_login"))
        return func(*args, **kwargs)
    return wrapper


def student_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("student_logged_in"):
            flash("Please login as student first.", "error")
            return redirect(url_for("student_login"))
        return func(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    conn = get_db()
    admission_count = conn.execute("SELECT COUNT(*) AS total FROM admissions").fetchone()["total"]
    student_count = conn.execute("SELECT COUNT(*) AS total FROM students").fetchone()["total"]
    notes_count = conn.execute("SELECT COUNT(*) AS total FROM notes").fetchone()["total"]
    video_count = conn.execute("SELECT COUNT(*) AS total FROM videos").fetchone()["total"]
    conn.close()

    return render_template(
        "index.html",
        admission_count=admission_count,
        student_count=student_count,
        notes_count=notes_count,
        video_count=video_count
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/founder")
def founder():
    return render_template("founder.html")


@app.route("/courses")
def courses():
    return render_template("courses.html")


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/testimonials")
def testimonials():
    return render_template("testimonials.html")


@app.route("/videos")
def videos():
    conn = get_db()
    all_videos = conn.execute("SELECT * FROM videos ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("videos.html", videos=all_videos)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        student_class = request.form.get("student_class", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not phone or not student_class:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("contact"))

        conn = get_db()
        conn.execute(
            "INSERT INTO admissions (name, phone, student_class, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, phone, student_class, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()

        flash("Thank you! Your admission enquiry has been saved. We will contact you soon.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")


@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        student = conn.execute(
            "SELECT * FROM students WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()
        conn.close()

        if student:
            session["student_logged_in"] = True
            session["student_id"] = student["id"]
            session["student_name"] = student["name"]
            session["student_class"] = student["student_class"]
            flash("Student login successful.", "success")
            return redirect(url_for("student_dashboard"))

        flash("Invalid student username or password.", "error")

    return render_template("student_login.html")


@app.route("/student/dashboard")
@student_required
def student_dashboard():
    student_class = session.get("student_class")

    conn = get_db()
    notes = conn.execute(
        "SELECT * FROM notes WHERE student_class = ? OR student_class = 'All Classes' ORDER BY id DESC",
        (student_class,)
    ).fetchall()
    all_videos = conn.execute("SELECT * FROM videos ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("student_dashboard.html", notes=notes, videos=all_videos)


@app.route("/student/logout")
def student_logout():
    session.pop("student_logged_in", None)
    session.pop("student_id", None)
    session.pop("student_name", None)
    session.pop("student_class", None)
    flash("Student logged out successfully.", "success")
    return redirect(url_for("student_login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            flash("Admin login successful.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin username or password.", "error")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Admin logged out successfully.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db()
    admissions = conn.execute("SELECT * FROM admissions ORDER BY id DESC").fetchall()
    students = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    notes = conn.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
    videos = conn.execute("SELECT * FROM videos ORDER BY id DESC").fetchall()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        admissions=admissions,
        students=students,
        notes=notes,
        videos=videos
    )


@app.route("/admin/add-student", methods=["POST"])
@admin_required
def add_student():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    student_class = request.form.get("student_class", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not name or not student_class or not username or not password:
        flash("Please fill all required student fields.", "error")
        return redirect(url_for("admin_dashboard"))

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO students (name, phone, student_class, username, password, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (name, phone, student_class, username, password, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        flash("Student login created successfully.", "success")
    except sqlite3.IntegrityError:
        flash("Username already exists. Please choose another username.", "error")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/upload-note", methods=["POST"])
@admin_required
def upload_note():
    title = request.form.get("title", "").strip()
    student_class = request.form.get("student_class", "").strip()
    file = request.files.get("note_file")

    if not title or not student_class or not file:
        flash("Please fill all note upload fields.", "error")
        return redirect(url_for("admin_dashboard"))

    if file and allowed_file(file.filename, ALLOWED_NOTE_EXTENSIONS):
        original = secure_filename(file.filename)
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{original}"
        file.save(os.path.join(NOTES_FOLDER, filename))

        conn = get_db()
        conn.execute(
            "INSERT INTO notes (title, student_class, filename, uploaded_at) VALUES (?, ?, ?, ?)",
            (title, student_class, filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()

        flash("Note/PDF uploaded successfully.", "success")
    else:
        flash("Invalid file type. Upload PDF, DOC, DOCX, PPT or PPTX.", "error")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/add-video", methods=["POST"])
@admin_required
def add_video():
    title = request.form.get("title", "").strip()
    video_url = request.form.get("video_url", "").strip()
    video_file = request.files.get("video_file")

    if not title:
        flash("Video title is required.", "error")
        return redirect(url_for("admin_dashboard"))

    conn = get_db()

    if video_url:
        conn.execute(
            "INSERT INTO videos (title, video_type, video_url, filename, uploaded_at) VALUES (?, ?, ?, ?, ?)",
            (title, "url", video_url, None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        flash("Video link added successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    if video_file and allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
        original = secure_filename(video_file.filename)
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{original}"
        video_file.save(os.path.join(VIDEO_FOLDER, filename))

        conn.execute(
            "INSERT INTO videos (title, video_type, video_url, filename, uploaded_at) VALUES (?, ?, ?, ?, ?)",
            (title, "file", None, filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        flash("Video uploaded successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    flash("Please add YouTube/video URL or upload MP4/WEBM/MOV file.", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/download-note/<filename>")
@student_required
def download_note(filename):
    return send_from_directory(NOTES_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
else:
    init_db()
