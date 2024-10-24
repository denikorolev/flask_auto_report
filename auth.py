# auth.py

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User, UserProfile

auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", title="login")
    
    # POST: обрабатываем данные логина
    user_email = request.json.get("email")
    password = request.json.get("password")
    print(user_email,password)
    
    
    user = User.query.filter_by(user_email=user_email).first()
    if user and user.check_password(password):
        login_user(user)
        if current_user.is_authenticated:
            print("user logged in")
        return jsonify({"status": "success", "message": "You was logged in successfully"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401


@auth_bp.route('/signup', methods=["POST","GET"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", title="signup")
    data = request.json
    user_email = data.get("email")
    user_name = data.get("username")
    password = data.get("password")
    
    try:
        user = User.create(email=user_email, username=user_name, password=password)
        
        # Создание профиля "Default" для нового пользователя
        UserProfile.create(user_id=user.id, profile_name="Default", description="default")
        
        return jsonify({"status": "success", "message": "Account created successfully"}), 201
    except ValueError as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 400



@auth_bp.route("/logout")
@login_required
def logout():
    print("logged out")
    session.pop('profile_id', None)
    logout_user()
    return redirect(url_for("auth.login"))



