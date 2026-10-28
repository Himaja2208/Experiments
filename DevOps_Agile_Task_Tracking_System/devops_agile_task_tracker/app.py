from functools import wraps
from datetime import date
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "task_tracker.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-for-a-real-deployment")
app.config["DATABASE"] = DATABASE

TASK_STATUSES = ["To Do", "In Progress", "Done"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
BUG_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'member'))
    );
    CREATE TABLE IF NOT EXISTS sprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        goal TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Planned'
    );
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        priority TEXT NOT NULL DEFAULT 'Medium',
        status TEXT NOT NULL DEFAULT 'To Do',
        assignee_id INTEGER,
        sprint_id INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY(assignee_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY(sprint_id) REFERENCES sprints(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS bugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        severity TEXT NOT NULL DEFAULT 'Medium',
        status TEXT NOT NULL DEFAULT 'Open',
        assignee_id INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY(assignee_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)
    count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Project Admin", "admin@example.com", generate_password_hash("Admin123!"), "admin")
        )
        db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Demo Member", "member@example.com", generate_password_hash("Member123!"), "member")
        )
    db.commit()
    db.close()


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id:
        g.user = get_db().execute(
            "SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        if g.user["role"] != "admin":
            flash("Only an administrator can perform that action.", "danger")
            return redirect(url_for("dashboard"))
        return view(**kwargs)
    return wrapped_view


@app.route("/")
def index():
    if g.user:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.", "danger")
        else:
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Welcome, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    task_counts = {
        "total": db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
        "todo": db.execute("SELECT COUNT(*) FROM tasks WHERE status='To Do'").fetchone()[0],
        "progress": db.execute("SELECT COUNT(*) FROM tasks WHERE status='In Progress'").fetchone()[0],
        "done": db.execute("SELECT COUNT(*) FROM tasks WHERE status='Done'").fetchone()[0],
        "bugs": db.execute("SELECT COUNT(*) FROM bugs WHERE status NOT IN ('Resolved','Closed')").fetchone()[0],
    }
    if g.user["role"] == "admin":
        recent_tasks = db.execute("""
            SELECT tasks.*, users.name AS assignee, sprints.name AS sprint
            FROM tasks LEFT JOIN users ON tasks.assignee_id=users.id
            LEFT JOIN sprints ON tasks.sprint_id=sprints.id
            ORDER BY tasks.id DESC LIMIT 6
        """).fetchall()
    else:
        recent_tasks = db.execute("""
            SELECT tasks.*, users.name AS assignee, sprints.name AS sprint
            FROM tasks LEFT JOIN users ON tasks.assignee_id=users.id
            LEFT JOIN sprints ON tasks.sprint_id=sprints.id
            WHERE tasks.assignee_id=? ORDER BY tasks.id DESC LIMIT 6
        """, (g.user["id"],)).fetchall()
    return render_template("dashboard.html", counts=task_counts, tasks=recent_tasks)


@app.route("/tasks")
@login_required
def tasks():
    db = get_db()
    status = request.args.get("status", "")
    sql = """
        SELECT tasks.*, users.name AS assignee, sprints.name AS sprint
        FROM tasks LEFT JOIN users ON tasks.assignee_id=users.id
        LEFT JOIN sprints ON tasks.sprint_id=sprints.id
    """
    params = []
    clauses = []
    if g.user["role"] != "admin":
        clauses.append("tasks.assignee_id=?")
        params.append(g.user["id"])
    if status in TASK_STATUSES:
        clauses.append("tasks.status=?")
        params.append(status)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY tasks.id DESC"
    rows = db.execute(sql, params).fetchall()
    members = db.execute("SELECT id, name FROM users WHERE role='member' ORDER BY name").fetchall()
    sprints = db.execute("SELECT id, name FROM sprints ORDER BY id DESC").fetchall()
    return render_template("tasks.html", tasks=rows, members=members, sprints=sprints,
                           statuses=TASK_STATUSES, priorities=PRIORITIES, filter_status=status)


@app.route("/tasks/create", methods=["POST"])
@admin_required
def create_task():
    title = request.form.get("title", "").strip()
    if not title:
        flash("Task title is required.", "danger")
        return redirect(url_for("tasks"))
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium")
    if priority not in PRIORITIES:
        priority = "Medium"
    assignee_id = request.form.get("assignee_id") or None
    sprint_id = request.form.get("sprint_id") or None
    db = get_db()
    db.execute("""INSERT INTO tasks
        (title, description, priority, status, assignee_id, sprint_id, created_at)
        VALUES (?, ?, ?, 'To Do', ?, ?, ?)""",
        (title, description, priority, assignee_id, sprint_id, date.today().isoformat()))
    db.commit()
    flash("Task created successfully.", "success")
    return redirect(url_for("tasks"))


@app.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def update_task_status(task_id):
    status = request.form.get("status", "")
    if status not in TASK_STATUSES:
        flash("Invalid task status.", "danger")
        return redirect(url_for("tasks"))
    db = get_db()
    task = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if task is None:
        flash("Task not found.", "danger")
    elif g.user["role"] != "admin" and task["assignee_id"] != g.user["id"]:
        flash("You can only update tasks assigned to you.", "danger")
    else:
        db.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
        db.commit()
        flash("Task status updated.", "success")
    return redirect(request.referrer or url_for("tasks"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@admin_required
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    db.commit()
    flash("Task deleted.", "info")
    return redirect(url_for("tasks"))


@app.route("/sprints")
@login_required
def sprints():
    db = get_db()
    rows = db.execute("""
        SELECT sprints.*,
        COUNT(tasks.id) AS task_count,
        SUM(CASE WHEN tasks.status='Done' THEN 1 ELSE 0 END) AS done_count
        FROM sprints LEFT JOIN tasks ON tasks.sprint_id=sprints.id
        GROUP BY sprints.id ORDER BY sprints.id DESC
    """).fetchall()
    return render_template("sprints.html", sprints=rows)


@app.route("/sprints/create", methods=["POST"])
@admin_required
def create_sprint():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Sprint name is required.", "danger")
        return redirect(url_for("sprints"))
    goal = request.form.get("goal", "").strip()
    start_date = request.form.get("start_date", "")
    end_date = request.form.get("end_date", "")
    status = request.form.get("status", "Planned")
    if status not in ["Planned", "Active", "Completed"]:
        status = "Planned"
    if start_date and end_date and end_date < start_date:
        flash("End date cannot be earlier than start date.", "danger")
        return redirect(url_for("sprints"))
    db = get_db()
    db.execute("INSERT INTO sprints (name, goal, start_date, end_date, status) VALUES (?, ?, ?, ?, ?)",
               (name, goal, start_date, end_date, status))
    db.commit()
    flash("Sprint created successfully.", "success")
    return redirect(url_for("sprints"))


@app.route("/bugs")
@login_required
def bugs():
    db = get_db()
    if g.user["role"] == "admin":
        rows = db.execute("""
            SELECT bugs.*, users.name AS assignee FROM bugs
            LEFT JOIN users ON bugs.assignee_id=users.id ORDER BY bugs.id DESC
        """).fetchall()
    else:
        rows = db.execute("""
            SELECT bugs.*, users.name AS assignee FROM bugs
            LEFT JOIN users ON bugs.assignee_id=users.id
            WHERE bugs.assignee_id=? ORDER BY bugs.id DESC
        """, (g.user["id"],)).fetchall()
    members = db.execute("SELECT id, name FROM users WHERE role='member' ORDER BY name").fetchall()
    return render_template("bugs.html", bugs=rows, members=members,
                           severities=SEVERITIES, statuses=BUG_STATUSES)


@app.route("/bugs/create", methods=["POST"])
@login_required
def create_bug():
    title = request.form.get("title", "").strip()
    if not title:
        flash("Bug title is required.", "danger")
        return redirect(url_for("bugs"))
    description = request.form.get("description", "").strip()
    severity = request.form.get("severity", "Medium")
    if severity not in SEVERITIES:
        severity = "Medium"
    assignee_id = request.form.get("assignee_id") or None
    if g.user["role"] != "admin":
        assignee_id = g.user["id"]
    db = get_db()
    db.execute("""INSERT INTO bugs (title, description, severity, status, assignee_id, created_at)
                  VALUES (?, ?, ?, 'Open', ?, ?)""",
               (title, description, severity, assignee_id, date.today().isoformat()))
    db.commit()
    flash("Bug reported successfully.", "success")
    return redirect(url_for("bugs"))


@app.route("/bugs/<int:bug_id>/status", methods=["POST"])
@login_required
def update_bug_status(bug_id):
    status = request.form.get("status", "")
    if status not in BUG_STATUSES:
        flash("Invalid bug status.", "danger")
        return redirect(url_for("bugs"))
    db = get_db()
    bug = db.execute("SELECT * FROM bugs WHERE id=?", (bug_id,)).fetchone()
    if bug is None:
        flash("Bug not found.", "danger")
    elif g.user["role"] != "admin" and bug["assignee_id"] != g.user["id"]:
        flash("You can only update bugs assigned to you.", "danger")
    else:
        db.execute("UPDATE bugs SET status=? WHERE id=?", (status, bug_id))
        db.commit()
        flash("Bug status updated.", "success")
    return redirect(url_for("bugs"))


@app.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter a name, valid email, and password of at least 8 characters.", "danger")
        else:
            try:
                db.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'member')",
                           (name, email, generate_password_hash(password)))
                db.commit()
                flash("Team member added.", "success")
                return redirect(url_for("users"))
            except sqlite3.IntegrityError:
                flash("That email address is already registered.", "danger")
    rows = db.execute("SELECT id, name, email, role FROM users ORDER BY id").fetchall()
    return render_template("users.html", users=rows)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
