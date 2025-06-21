# app/context_processors.py

from flask import request, g
from flask_security import current_user
from menu_constructor import build_menu
from profile_constructor import ProfileSettingsManager
from models import UserProfile


def inject_menu():
    excluded_endpoints = {"error", "security.login", "security.logout", "main.index"}
    if request.endpoint in excluded_endpoints:
        return {}
    return {"menu": build_menu()}


def inject_user_settings():
    excluded_endpoints = {
        "error", "security.login", "security.logout", "custom_logout",
        "main.index", "profile_settings.create_profile"
    }
    if request.endpoint in excluded_endpoints:
        return {}

    user_settings = g.get("profile_settings", None)
    if not user_settings:
        user_settings = ProfileSettingsManager.load_profile_settings()
    return {"user_settings": user_settings}


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
                getattr(g, "current_profile", None) and
                profile.id == g.current_profile.id
            )
        })
    return {"profiles": profiles}