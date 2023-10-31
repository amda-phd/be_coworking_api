from fastapi.testclient import TestClient
import pytest
import json

from src.main import app
from src.db import connect_to_mongodb, seed_mongodb

@pytest.fixture
def test_db():
    return connect_to_mongodb(app, testing = True)

@pytest.fixture
def seed_db():
    f = open("tests/seed.json")
    return seed_mongodb(test_db, json.load(f))

@pytest.fixture
def client():
    return TestClient(app)

## Running this test first is a bit important, as it happens before the test_db() fixture is called, triggering the 503 error
def test_unhealthy_db(client):
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["detail"] == "MongoDB unavailable"

@pytest.mark.asyncio
async def test_healthy_db(client, test_db):
    pre_docs = await test_db["health"].count_documents({})
    assert pre_docs == 0
    response = client.get("/health")
    assert response.status_code == 204
    post_docs = await test_db["health"].count_documents({})
    assert post_docs == pre_docs + 1
    # assert response.json() == None

ok_room = {
    "opening": "09:00",
    "closing": "17:00",
    "capacity": 5
}
id_room: None
@pytest.mark.asyncio
async def test_create_room_success(client, test_db):
    # Providing a valid id number
    response = client.post("/rooms", json = { **ok_room, "id": 1 })
    assert response.status_code == 200, response.text
    new_room = response.json()
    assert new_room["id"] == 1

    # Letting the model create the right id
    response = client.post("/rooms", json = ok_room)
    assert response.status_code == 200, response.text
    new_room = response.json()
    id_room = new_room["id"]
    db_entry = await test_db["rooms"].find_one({ "id": id_room })
    assert db_entry is not None
    assert id_room == 2
    for key in ok_room:
        assert new_room[key] == ok_room[key]
        assert db_entry[key] == ok_room[key]

    
async def create_room_validation_error(room, client, db):
    pre_docs = await db["rooms"].count_documents({})
    response = client.post("/rooms", json = room)
    assert response.status_code == 422, response.text
    post_docs = await db["rooms"].count_documents({})
    assert pre_docs == post_docs

@pytest.mark.asyncio
async def test_create_room_validation_errors(client, test_db):
    # Make sure we have at least one item in the mocked database to trigger the "Invalid id" error
    client.post("/rooms", json = ok_room)
    rooms = [
        { **ok_room, "capacity": -7 }, # Negative capacity
        { **ok_room, "closing": "08:50" }, # Closing time happening before than opening time
        { **ok_room, "opening": "notwhatIwasexpecting" }, # Opening or closing time not in the right format
        { **ok_room, "id": 1 } # Propose an id that is already being used
    ]
    for room in rooms:
        await create_room_validation_error(room, client, test_db)

@pytest.mark.asyncio
async def test_query_rooms(client, test_db, seed_db):
    docs = await test_db["rooms"].count_documents({})
    response = client.get("/rooms")
    assert response.status_code == 200, response.text
    rooms = response.json()
    assert len(rooms) == docs