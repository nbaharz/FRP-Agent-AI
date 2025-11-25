import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from app.main import app
from app.database.db_session import SessionLocal
from app.database.models import User
from app.services.token_service import create_access_token
import uuid

@pytest.mark.asyncio
async def test_chat_and_end_session_flow():
    db = SessionLocal()

    uid = str(uuid.uuid4())
    user = User(
        id=f"test_user_{uid}",
        email=f"test_{uid}@test.com",
        username=f"user_{uid}",
        password="123"
    )
    db.add(user)
    db.commit()

    token = create_access_token({"sub": user.id})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_chat = await ac.post(
            "/api/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "Hello Elara!"},
        )
        assert res_chat.status_code == status.HTTP_200_OK

        res_end = await ac.post(
            "/api/end-session",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_end.status_code == status.HTTP_200_OK

    db.query(User).filter(User.id == user.id).delete()
    db.commit()
    db.close()
