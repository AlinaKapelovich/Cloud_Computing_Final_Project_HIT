"""Shared Flask extension instances.

Extensions are created here (unbound) and initialised inside the application factory
with `init_app`. Keeping them in their own module avoids circular imports between the
factory, controllers and models.
"""
from flask_login import LoginManager
from flask_wtf import CSRFProtect

# Session-based authentication (login/logout, current_user, role checks).
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

# CSRF protection applied to every POST form rendered from our templates.
csrf = CSRFProtect()
