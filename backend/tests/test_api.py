import asyncio
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app, lifespan


@pytest.mark.asyncio
async def test_health():
    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/health")
            assert res.status_code == 200
            assert res.json() == {"status": "ok"}

            # Test login with seeded admin
            login_res = await client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "admin123"},
            )
            print("Login response status:", login_res.status_code)
            assert login_res.status_code == 200
            data = login_res.json()
            assert "access_token" in data
            assert data["role"] == "admin"
            print("Authenticated admin successfully!")


if __name__ == "__main__":
    asyncio.run(test_health())

