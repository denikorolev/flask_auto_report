from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User, UserProfile, Paragraph


admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin", methods=["POST", "GET"])
@login_required
def admin():
    
    menu = current_app.config["MENU"]
    
    users = User.query.all()
    paragraphs = Paragraph.query.all()
    profiles = UserProfile.query.all()
    # print(users[0].user_to_profiles.profile_name)
    
    return render_template("admin.html",
                           menu=menu,
                           title="Admin",
                           users=users,
                           paragraphs=paragraphs,
                           profiles=profiles)
    
    
@admin_bp.route("/delete_user/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    print(f"запрос пришел {user_id}")
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"status": "success", "message": "User deleted successfully"}), 200
    return jsonify({"status": "error", "message": "User not found"}), 404


@admin_bp.route("/delete_paragraph/<int:paragraph_id>", methods=["DELETE"])
@login_required
def delete_paragraph(paragraph_id):
    paragraph = Paragraph.query.get(paragraph_id)
    if paragraph:
        db.session.delete(paragraph)
        db.session.commit()
        return jsonify({"status": "success", "message": "Paragraph deleted successfully"}), 200
    return jsonify({"status": "error", "message": "Paragraph not found"}), 404


@admin_bp.route("/delete_profile/<int:profile_id>", methods=["DELETE"])
@login_required
def delete_profile(profile_id):
    profile = UserProfile.query.get(profile_id)
    if profile:
        db.session.delete(profile)
        db.session.commit()
        return jsonify({"status": "success", "message": "Profile deleted successfully"}), 200
    return jsonify({"status": "error", "message": "Profile not found"}), 404


@admin_bp.route("/edit_user/<int:user_id>", methods=["PUT"])
@login_required
def edit_user(user_id):
    user = User.query.get(user_id)
    if user:
        data = request.get_json()
        user.user_name = data.get("user_name", user.user_name)
        user.user_role = data.get("user_role", user.user_role)
        db.session.commit()
        return jsonify({"status": "success", "message": "User updated successfully"}), 200
    return jsonify({"status": "error", "message": "User not found"}), 404


@admin_bp.route("/edit_paragraph/<int:paragraph_id>", methods=["PUT"])
@login_required
def edit_paragraph(paragraph_id):
    paragraph = Paragraph.query.get(paragraph_id)
    if paragraph:
        data = request.get_json()
        paragraph.paragraph = data.get("paragraph", paragraph.paragraph)
        paragraph.weight = data.get("weight", paragraph.weight)
        db.session.commit()
        return jsonify({"status": "success", "message": "Paragraph updated successfully"}), 200
    return jsonify({"status": "error", "message": "Paragraph not found"}), 404


@admin_bp.route("/edit_profile/<int:profile_id>", methods=["PUT"])
@login_required
def edit_profile(profile_id):
    profile = UserProfile.query.get(profile_id)
    if profile:
        data = request.get_json()
        profile.profile_name = data.get("profile_name", profile.profile_name)
        db.session.commit()
        return jsonify({"status": "success", "message": "Profile updated successfully"}), 200
    return jsonify({"status": "error", "message": "Profile not found"}), 404



