import argparse
import sys

from pydantic import BaseModel, EmailStr, Field, ValidationError

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


class AdminInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=255)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = AdminInput(email=args.email, password=args.password, name=args.name)
    except ValidationError as exc:
        print(f"Invalid input: {exc.errors()[0]['msg']}", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        users = UserRepository(db)
        if users.get_by_email(payload.email):
            print(f"User already exists: {payload.email}", file=sys.stderr)
            return 1
        user = User(
            email=payload.email,
            full_name=payload.name,
            hashed_password=hash_password(payload.password),
            role=UserRole.ADMIN,
        )
        users.add(user)
        print(f"Admin user created: {payload.email}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
