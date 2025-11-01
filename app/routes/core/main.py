from flask import Blueprint, render_template
from flask_login import login_required
from config import Settings

core_main_bp = Blueprint("core_main", __name__, template_folder="../../templates/core")

@core_main_bp.route("/")
@login_required
def landing():
    return render_template("core/landing.html", project_name=Settings.PROJECT_NAME, project_slug=Settings.PROJECT_SLUG)
