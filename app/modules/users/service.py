from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def create(self, data: UserCreate, actor: str = "system") -> User:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ValueError(f"Email {data.email!r} already registered")
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            province=data.province,
            district=data.district,
            subdistrict=data.subdistrict,
            created_by=actor,
            updated_by=actor,
        )
        return await self.repo.create(user)

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.repo.get_by_email(email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def update(self, user: User, data: UserUpdate, actor: str = "system") -> User:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)
        user.updated_by = actor
        return await self.repo.update(user)
