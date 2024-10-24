from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User, UserProfile, ReportParagraph


admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin", methods=["POST", "GET"])
@login_required
def admin():
    users = User.query.all()
    paragraphs = ReportParagraph.query.all()
    menu = current_app.config["MENU"]
    return render_template("admin.html",
                           menu=menu,
                           title="Admin",
                           users=users,
                           paragraphs=paragraphs)