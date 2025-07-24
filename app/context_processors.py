# app/context_processors.py

from flask import request, session
from flask_security import current_user
from app.utils.menu_constructor import build_menu
from app.utils.profile_constructor import ProfileSettingsManager
from app.models.models import UserProfile
from app.utils.logger import logger


def inject_menu():
    excluded_endpoints = {"error", "security.login", "security.logout", "main.index", "profile_settings.new_profile_creation"}
    if request.endpoint in excluded_endpoints:
        return {}
    return {"menu": build_menu()}


def inject_user_settings():
    excluded_endpoints = {
        "error", "security.login", "security.logout", "custom_logout",
        "main.index"
    }
    if request.endpoint in excluded_endpoints:
        return {}
    profile_settings = ProfileSettingsManager.load_profile_settings()
    if not profile_settings:
        logger.warning("No profile settings found, returning empty dict")
        return {"user_settings": {}}
    return {"user_settings": profile_settings}


def inject_app_info(version):
    def _processor():
        return {"app_info": {"version": version, "author": "radiologary ltd"}}
    return _processor


def inject_user_rank():
    if not current_user.is_authenticated:
        return {"user_max_rank": 0}
    user_max_rank = current_user.get_max_rank()
    if not user_max_rank:
        user_max_rank = 0
    return {"user_max_rank": user_max_rank}


def inject_current_profile_data():
    if request.path.startswith('/static/') or not current_user.is_authenticated:
        return {"profiles": None}
    user_profiles = UserProfile.get_user_profiles(current_user.id)
    if not user_profiles:
        return {"profiles": None}
    profiles = []
    for profile in user_profiles:
        profiles.append({
            "id": profile.id,
            "profile_name": profile.profile_name,
            "description": profile.description,
            "is_default": profile.default_profile,
            "is_active": (
                session.get("profile_id") is not None and
                profile.id == int(session["profile_id"])
            )
        })
    return {"profiles": profiles}