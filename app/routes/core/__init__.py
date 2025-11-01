from flask_login import current_user
from ...database import login_manager
from ...models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def load_user_by_email(email: str):
    return User.query.filter_by(email=email).first()
