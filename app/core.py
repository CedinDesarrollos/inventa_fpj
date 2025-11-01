from sqlalchemy import func
from .models import User

def load_user_by_email(email: str):
    if not email:
        return None
    return User.query.filter(func.lower(User.email) == email.lower()).first()

def load_user_by_username(username: str):
    if not username:
        return None
    return User.query.filter(func.lower(User.username) == username.lower()).first()

def load_user_by_login(login_str: str):
    """Busca por username/login/user y opcionalmente por email."""
    if not login_str:
        return None
    s = login_str.strip().lower()

    conds = []
    if hasattr(User, "username"):
        conds.append(func.lower(User.username) == s)
    if hasattr(User, "login"):
        conds.append(func.lower(User.login) == s)
    if hasattr(User, "user"):
        conds.append(func.lower(User.user) == s)
    # Si el input parece email y existe la columna email, también probamos por email
    if "@" in s and hasattr(User, "email"):
        conds.append(func.lower(User.email) == s)

    if not conds:
        # Fallback: si solo tenemos email, intentamos igual por email
        if hasattr(User, "email"):
            return User.query.filter(func.lower(User.email) == s).first()
        return None

    return User.query.filter(or_(*conds)).first()
