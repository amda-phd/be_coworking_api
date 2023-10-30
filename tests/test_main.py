from fastapi.testclient import TestClient
import pytest
import asyncio

from src.main import app
from src.db import connect_to_mongodb, close_mongodb_connection

@pytest.fixture
def setup_db():
    return connect_to_mongodb(app, True)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_healthy_db(client, setup_db):
    pre_docs = await setup_db["health"].count_documents({})
    response = client.get("/health")
    assert response.status_code == 204
    post_docs = await setup_db["health"].count_documents({})
    assert post_docs == pre_docs + 1
    # assert response.json() == None

@pytest.mark.asyncio
async def test_unhealthy_db(client):
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["detail"] == "MongoDB unavailable"

# Run the tests
if __name__ == '__main__':
    asyncio.run(test_healthy_db())
    asyncio.run(test_unhealthy_db())