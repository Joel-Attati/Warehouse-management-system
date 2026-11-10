"""Smoke tests for backend models and schemas."""
import pytest
from app.models.user import UserRole
from app.schemas.user import UserBase


def test_user_schema():
    u = UserBase(
        username="testuser",
        email="test@example.com",
        role=UserRole.staff,
    )
    assert u.username == "testuser"
    assert u.role == UserRole.staff

