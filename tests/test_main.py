from fastapi.testclient import TestClient
import pytest
import asyncio

from src.main import app
from src.db import connect_to_mongodb

@pytest.fixture
def db():
    return connect_to_mongodb()

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client, db):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["API"]

# Run the tests
if __name__ == '__main__':
    asyncio.run(test_health())