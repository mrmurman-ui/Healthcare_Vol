"""Integration tests — UserService against in-memory SQLite."""
import pytest
import pytest_asyncio

from app.modules.users.schema import UserCreate, UserUpdate
from app.modules.users.service import UserService
from app.shared.enums import UserRole


@pytest_asyncio.fixture
async def user_service(session):
    return UserService(session)


@pytest.mark.asyncio
async def test_create_user(user_service):
    user = await user_service.create(
        UserCreate(
            email="test@example.com",
            password="TestPass1!",
            full_name="Test User",
            role=UserRole.VOLUNTEER,
        )
    )
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.role == UserRole.VOLUNTEER
    assert user.hashed_password != "TestPass1!"


@pytest.mark.asyncio
async def test_duplicate_email_raises(user_service):
    data = UserCreate(email="dup@example.com", password="pw", full_name="Dup")
    await user_service.create(data)
    with pytest.raises(ValueError, match="already registered"):
        await user_service.create(data)


@pytest.mark.asyncio
async def test_authenticate_success(user_service):
    await user_service.create(
        UserCreate(email="auth@example.com", password="MyPwd123", full_name="Auth User")
    )
    user = await user_service.authenticate("auth@example.com", "MyPwd123")
    assert user is not None
    assert user.email == "auth@example.com"


@pytest.mark.asyncio
async def test_authenticate_wrong_password(user_service):
    await user_service.create(
        UserCreate(email="wp@example.com", password="correct", full_name="WP")
    )
    result = await user_service.authenticate("wp@example.com", "wrong")
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_unknown_email(user_service):
    result = await user_service.authenticate("nobody@example.com", "pass")
    assert result is None


@pytest.mark.asyncio
async def test_update_user(user_service):
    user = await user_service.create(
        UserCreate(email="upd@example.com", password="pw", full_name="Old Name")
    )
    updated = await user_service.update(user, UserUpdate(full_name="New Name"))
    assert updated.full_name == "New Name"
