"""Authorization decorators for role-based access control (RBAC).

`role_required("admin")` protects a route so only authenticated users whose role
matches are allowed. Unauthenticated users are redirected to the login page;
authenticated users with the wrong role get a friendly 403 page.
"""
from functools import wraps

from flask import abort
from flask_login import current_user

from app.extensions import login_manager


def role_required(*roles: str):
    """Restrict a view to users holding one of the given roles."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
