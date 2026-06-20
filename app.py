from datetime import datetime

import psycopg2
from flask import Flask, redirect, render_template, request, session
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, template_folder="public")
app.secret_key = "keyboard_cat"


# ====== DB ======

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="journal",
        user="postgres",
        password="admin",
        port="5432",
    )


# ====== AUTH ======

@app.route("/", methods=["GET", "POST"])
def register_page():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Username and password are required"
        else:
            hashed = generate_password_hash(password)
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s);",
                    (username, hashed),
                )
                conn.commit()
                return redirect("/login")
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                error = "Username already exists"
            except Exception as e:
                print(f"Register error: {e}")
                error = "Server error"
            finally:
                cur.close()
                conn.close()

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login_page():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Username and password are required"
        else:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if not user or not check_password_hash(user["password"], password):
                error = "Invalid username or password"
            else:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect("/journal")

    return render_template("login.html", error=error)


@app.route("/auth/logout")
def logout():
    session.clear()
    return redirect("/login")


# ====== JOURNAL ======

@app.route("/journal", methods=["GET", "POST"])
def journal_page():
    if "user_id" not in session:
        return redirect("/login")

    error = None

    if request.method == "POST":
        action = request.form.get("action")
        entry_date = request.form.get("entry_date", "")
        content = request.form.get("content", "").strip()

        try:
            parsed = datetime.strptime(entry_date, "%Y-%m-%d").date()
        except ValueError:
            error = "Invalid date format"
            parsed = None

        if parsed and action == "create":
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO journal_entries (user_id, content, entry_date) VALUES (%s, %s, %s);",
                    (session["user_id"], content, parsed),
                )
                conn.commit()
            except Exception as e:
                print(f"Create error: {e}")
                error = "Could not save entry"
            finally:
                cur.close()
                conn.close()

        elif parsed and action == "update":
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE journal_entries SET content = %s WHERE entry_date = %s AND user_id = %s;",
                    (content, parsed, session["user_id"]),
                )
                conn.commit()
            except Exception as e:
                print(f"Update error: {e}")
                error = "Could not update entry"
            finally:
                cur.close()
                conn.close()

        elif parsed and action == "delete":
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    "DELETE FROM journal_entries WHERE entry_date = %s AND user_id = %s;",
                    (parsed, session["user_id"]),
                )
                conn.commit()
            except Exception as e:
                print(f"Delete error: {e}")
                error = "Could not delete entry"
            finally:
                cur.close()
                conn.close()

        return redirect("/journal")

    # GET — load all entries
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM journal_entries WHERE user_id = %s ORDER BY entry_date DESC;",
        (session["user_id"],),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    entries = [
        {**r, "entry_date": r["entry_date"].strftime("%Y-%m-%d")}
        for r in rows
    ]

    return render_template("journal.html", entries=entries, error=error, username=session["username"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
