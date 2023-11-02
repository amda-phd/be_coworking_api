from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder

import pytest
import json

import pytest_asyncio

from src.main import app
from src.db import connect_to_mongodb

@pytest.fixture
def test_db():
    return connect_to_mongodb(app, testing = True)

@pytest_asyncio.fixture
async def seed_db(test_db):
    f = open("tests/seed.json")
    data = json.load(f)
    for key in data:
        collection = test_db[key]
        await collection.insert_many(jsonable_encoder(data[key]))
    return

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
    assert response.status_code == 200
    post_docs = await test_db["health"].count_documents({})
    assert post_docs == pre_docs + 1
    data = response.json()
    assert data["health"] == 'ok'

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
    assert response.status_code == 201, response.text
    new_room = response.json()
    assert new_room["id"] == 1

    # Letting the model create the right id
    response = client.post("/rooms", json = ok_room)
    assert response.status_code == 201, response.text
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

@pytest.mark.asyncio
async def test_room_availability(client, test_db, seed_db):
    booking = await test_db["bookings"].find_one({})
    response = client.get(f"/rooms/{booking['id_room']}/availability?time={booking['start']}")
    assert response.status_code == 200, response.text
    assert not response.json()

    response = client.get(f"/rooms/{booking['id_room']}/availability?time=2023-07-18T10:10Z")
    assert response.status_code == 200, response.text
    assert not response.json()

    response = client.get(f"/rooms/{booking['id_room']}/availability?time=2023-08-18T10:10Z")
    assert response.status_code == 200, response.text
    assert response.json()

    response = client.get(f"/rooms/7/availability?time={booking['start']}")
    assert response.status_code == 404, response.text

    response = client.get(f"/rooms/{booking['id_room']}/availability?time=2023-07-18T10:10")
    assert response.status_code == 422, response.text

@pytest.mark.asyncio
async def test_query_bookings(client, test_db, seed_db):
    response = client.get("/bookings")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 10

    bookings = await test_db["bookings"].count_documents({})
    response = client.get(f"/bookings?lim={bookings}")
    assert response.status_code == 200, response.text
    assert len(response.json()) == bookings

    id_client = 1
    id_room = 2
    bookings = await test_db["bookings"].count_documents({ "id_client": id_client })
    response = client.get(f"/bookings?id_client={id_client}")
    assert response.status_code == 200, response.text
    assert len(response.json()) == bookings

    bookings = await test_db["bookings"].count_documents({ "id_client": id_client, "id_room": id_room })
    response = client.get(f"/bookings?id_client={id_client}&id_room={id_room}")
    assert response.status_code == 200, response.text
    assert len(response.json()) == bookings

    response = client.get(f"/bookings?id_client=7&id_room={id_room}")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 0

ok_booking = {
    "id_room": 1,
    "id_client": 1,
    "start": "2024-08-21T10:00Z",
    "end": "2024-08-21T14:30Z"
}
@pytest.mark.asyncio
async def test_create_booking_success(client, test_db, seed_db):
    pre_bookings = await test_db["bookings"].count_documents({})
    response = client.post("/bookings", json = ok_booking)
    assert response.status_code == 201, response.text
    post_bookings = await test_db["bookings"].count_documents({})
    assert post_bookings == pre_bookings + 1

@pytest.mark.asyncio
async def test_create_booking_errors(client, test_db, seed_db):
    pre_docs = await test_db["bookings"].count_documents({})

    # Non existent entities
    response = client.post("/bookings", json = { **ok_booking, "id_room": 10 })
    assert response.status_code == 404, response.text

    response = client.post("/bookings", json = { **ok_booking, "id_client": 10 })
    assert response.status_code == 404, response.text

    # Wrong hours
    response = client.post("/bookings", json = { **ok_booking, "start": "2023-07-18T10:10Z", "end": "2023-07-18T11:00Z" })
    assert response.status_code == 422, response.text

    response = client.post("/bookings", json = { **ok_booking, "start": ok_booking["end"], "end": ok_booking["start"] })
    assert response.status_code == 422, response.text
    post_docs = await test_db["bookings"].count_documents({})
    assert pre_docs == post_docs

    # Overlapping bookings
    response = client.post("/bookings", json = ok_booking)
    response = client.post("/bookings", json = { **ok_booking, "start": "2024-08-21T10:10Z", "end": "2024-08-21T11:00Z" })
    assert response.status_code == 409, response.text

    response = client.post("/bookings", json = { **ok_booking, "start": "2024-08-21T14:25Z", "end": "2024-08-21T15:00Z" })
    assert response.status_code == 409, response.text

    response = client.post("/bookings", json = { **ok_booking, "start": "2024-08-21T14:25Z", "end": "2024-08-21T15:00Z" })
    assert response.status_code == 409, response.text

    # Bookings out of the room's opening hours
    response = client.post("/bookings", json = { **ok_booking, "start": "2024-08-21T06:00Z" })
    assert response.status_code == 406, response.text

    response = client.post("/bookings", json = { **ok_booking, "start": "2024-08-21T21:00Z", "end": "2024-08-21T23:00Z" })
    assert response.status_code == 406, response.text

    response = client.post("/bookings", json = { **ok_booking, "end": "2024-08-21T23:00Z" })
    assert response.status_code == 406, response.text
