from fastapi.testclient import TestClient
import pytest
import asyncio

from src.main import app
from src.db import connect_to_mongodb

@pytest.fixture
def setup_db():
    return connect_to_mongodb(app, True)

@pytest.fixture
def client():
    return TestClient(app)

## Running this test first is a bit important, as it happens before the setup_db() fixture is called, triggering the 503 error
def test_unhealthy_db(client):
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["detail"] == "MongoDB unavailable"

@pytest.mark.asyncio
async def test_healthy_db(client, setup_db):
    pre_docs = await setup_db["health"].count_documents({})
    assert pre_docs == 0
    response = client.get("/health")
    assert response.status_code == 204
    post_docs = await setup_db["health"].count_documents({})
    assert post_docs == pre_docs + 1
    # assert response.json() == None



# Run the tests
if __name__ == '__main__':
    asyncio.run(test_unhealthy_db())
    asyncio.run(test_healthy_db())