
from getpass import getpass

from app import create_app
from app.extensions import db
from app.models import Admin


app = create_app()


def create_admin():
    with app.app_context():
        # Check whether an admin already exists
        existing_admin = db.session.scalar(
            db.select(Admin)
        )

        if existing_admin:
            print("An admin account already exists.")
            print("No new account was created.")
            return

        username = input("Choose an admin username: ").strip()

        if not username:
            print("Username cannot be empty.")
            return

        password = getpass("Choose an admin password: ")
        confirm_password = getpass("Confirm your password: ")

        if len(password) < 9:
            print("Password must be at least 9 characters long.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        admin = Admin(username=username)
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        print(f"Admin account '{username}' created successfully.")


if __name__ == "__main__":
    create_admin()
