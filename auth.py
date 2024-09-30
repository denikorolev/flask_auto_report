# auth.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(user_email=user_email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid credentials", "error")
    return render_template("login.html", title="LogIn")

@auth_bp.route("/logout")
@login_required
def logout():
    session.pop('profile_id', None)
    logout_user()
    return redirect(url_for("auth.login"))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_role = "user"
        user_email = request.form["email"]
        user_name = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(user_email=user_email).first():
            flash("Email already exists", "error")
            return redirect(url_for("auth.signup"))
        # Create object of class user and then create pass-hash
        user = User(user_email=user_email, user_name=user_name, user_role=user_role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully", "success")
        return redirect(url_for("auth.login"))
    return render_template("signup.html", title="SignUp")
