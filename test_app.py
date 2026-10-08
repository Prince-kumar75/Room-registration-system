import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.seed import seed_database

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield

def test_home_and_rooms_page():
    response = client.get("/rooms")
    assert response.status_code == 200
    assert "Available Rooms" in response.text

def test_user_registration_and_login():
    unique_id = str(uuid.uuid4())[:8]
    username = f"user_{unique_id}"
    email = f"user_{unique_id}@example.com"
    
    # Register new user
    reg_response = client.post(
        "/register",
        data={"username": username, "email": email, "password": "mypassword"},
        follow_redirects=False
    )
    assert reg_response.status_code == 303
    assert "user_session" in reg_response.cookies

    # Login user
    login_response = client.post(
        "/login",
        data={"username": username, "password": "mypassword"},
        follow_redirects=False
    )
    assert login_response.status_code == 303
    assert "user_session" in login_response.cookies

def test_full_room_booking_flow():
    # 1. Login demouser
    login_res = client.post(
        "/login",
        data={"username": "demouser", "password": "password123"},
        follow_redirects=False
    )
    session_id = login_res.cookies.get("user_session")
    
    # Set cookie directly on TestClient
    client.cookies.set("user_session", session_id)

    # 2. View Room 1 Details
    room_res = client.get("/rooms/1")
    assert room_res.status_code == 200
    assert "Single Economy" in room_res.text

    # 3. Book Room
    book_res = client.post(
        "/rooms/1/book",
        data={"check_in_date": "2026-10-10", "check_out_date": "2026-10-13"},
        follow_redirects=False
    )
    assert book_res.status_code == 303
    assert "history" in book_res.headers["location"]

    # 4. View Booking History
    history_res = client.get("/history")
    assert history_res.status_code == 200
    assert "Booking #" in history_res.text

    # Extract latest booking ID from DB to check-in and check-out
    db = SessionLocal()
    booking = db.query(app.models.Booking if hasattr(app, 'models') else __import__('app.models').models.Booking).order_by(__import__('app.models').models.Booking.id.desc()).first()
    booking_id = booking.id
    db.close()

    # 5. Check-in
    checkin_res = client.post(f"/bookings/{booking_id}/checkin", follow_redirects=False)
    assert checkin_res.status_code == 303

    # 6. Check-out
    checkout_res = client.post(f"/bookings/{booking_id}/checkout", follow_redirects=False)
    assert checkout_res.status_code == 303

    # 7. Confirm History shows Checked Out
    history_final = client.get("/history")
    assert history_final.status_code == 200
    assert "Checked Out" in history_final.text
