from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


def create_user(email: str, name: str, password: str, role: UserRole) -> bool:
    db = SessionLocal()
    try:
        users = UserRepository(db)
        if users.get_by_email(email):
            return False
        users.add(
            User(
                email=email,
                full_name=name,
                hashed_password=hash_password(password),
                role=role,
            ),
        )
        return True
    finally:
        db.close()


def main() -> int:
    created_admin = create_user(
        "admin@example.com",
        "Admin User",
        "StrongPassword123",
        UserRole.ADMIN,
    )
    created_user = create_user(
        "user@example.com",
        "Example User",
        "StrongPassword123",
        UserRole.USER,
    )
    print(f"Admin user {'created' if created_admin else 'already exists'}: admin@example.com")
    print(f"Normal user {'created' if created_user else 'already exists'}: user@example.com")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
