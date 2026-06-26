"""Streamlit session-state helpers for authentication."""
from __future__ import annotations

import streamlit as st

from app.core.security import create_access_token, decode_token
from app.modules.users.model import User
from app.shared.enums import UserRole

_SESSION_KEY = "auth_token"
_USER_KEY = "current_user"


def login_user(user: User) -> None:
    token = create_access_token(str(user.id), extra={"role": user.role, "email": user.email})
    st.session_state[_SESSION_KEY] = token
    st.session_state[_USER_KEY] = user


def logout_user() -> None:
    st.session_state.pop(_SESSION_KEY, None)
    st.session_state.pop(_USER_KEY, None)


def get_current_user() -> User | None:
    return st.session_state.get(_USER_KEY)


def is_authenticated() -> bool:
    token = st.session_state.get(_SESSION_KEY)
    if not token:
        return False
    try:
        decode_token(token)
        return True
    except ValueError:
        return False


def require_roles(*roles: UserRole) -> bool:
    user = get_current_user()
    if not user:
        return False
    return user.role in roles


def assert_roles(*roles: UserRole) -> None:
    if not require_roles(*roles):
        st.error("Access denied.")
        st.stop()
