# app/blueprints/support.py

from flask import Blueprint, render_template, request, session, redirect, url_for
from flask_security import roles_required, auth_required, logout_user
from logger import logger



support_bp = Blueprint("support", __name__)


@support_bp.route("/playground", methods=["GET", "POST"])
@auth_required()
@roles_required("superadmin")
def playground():
    logger.info("Playground route accessed")
    if request.method == "POST":
        logger.info("Playground POST request received")
    return render_template(
        "playground.html",
        title="Playground"
    )

    
@support_bp.route("/error", methods=["POST", "GET"])
def error():
    print("inside error route")
    message = request.args.get("message") or "no message"
    return render_template("errors/error.html",
                           message=message)
    
    
