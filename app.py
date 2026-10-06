import os
import secrets
from functools import wraps

import psycopg
from flask import Flask, flash, redirect, render_template, request, session, url_for
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "development-only-change-this-secret"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower()
        == "true",
    )
    def get_db_connection():
        return psycopg.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            dbname=os.environ.get("POSTGRES_DB", "loginapp"),
            user=os.environ.get("POSTGRES_USER", "loginapp"),
            password=os.environ.get("POSTGRES_PASSWORD", "localdevpassword"),
            row_factory=dict_row,
        )

    def csrf_protected(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if request.method == "POST":
                submitted_token = request.form.get("csrf_token", "")
                session_token = session.get("csrf_token", "")
                if not session_token or not secrets.compare_digest(
                    submitted_token, session_token
                ):
                    return "Invalid form token. Please refresh and try again.", 400
            return view(*args, **kwargs)

        return wrapped

    @app.context_processor
    def inject_csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return {"csrf_token": session["csrf_token"]}

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in to continue.", "info")
                return redirect(url_for("login"))
            return view(*args, **kwargs)

        return wrapped

    @app.get("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    @csrf_protected
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not username or not email or not password:
                flash("Please complete every field.", "error")
            elif len(username) > 80 or len(email) > 254:
                flash("Username or email is too long.", "error")
            elif len(password) < 8:
                flash("Use a password with at least 8 characters.", "error")
            else:
                try:
                    with get_db_connection() as connection:
                        connection.execute(
                            """
                            INSERT INTO users (username, email, password_hash)
                            VALUES (%s, %s, %s)
                            """,
                            (username, email, generate_password_hash(password)),
                        )
                    flash("Account created. You can now sign in.", "success")
                    return redirect(url_for("login"))
                except psycopg.errors.UniqueViolation:
                    flash("That username or email is already registered.", "error")

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    @csrf_protected
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            with get_db_connection() as connection:
                user = connection.execute(
                    "SELECT id, username, password_hash FROM users WHERE email = %s",
                    (email,),
                ).fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                flash("Welcome back!", "success")
                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "error")

        return render_template("login.html")

    @app.get("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html", username=session["username"])

    @app.post("/logout")
    @csrf_protected
    @login_required
    def logout():
        session.clear()
        flash("You have been signed out.", "info")
        return redirect(url_for("login"))

    return app


app = create_app()
