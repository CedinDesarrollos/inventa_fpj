from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from ...core import load_user_by_login 

core_auth_bp = Blueprint("core_auth", __name__, template_folder="../../templates/core")

@core_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_str = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        user = load_user_by_login(login_str)
        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect(url_for("core_main.landing"))

        flash("Credenciales inválidas", "danger")

    return render_template("core/login.html")

@core_auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("core_auth.login"))
