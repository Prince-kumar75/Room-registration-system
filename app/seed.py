from app.database import SessionLocal, engine, Base
from app.models import Room, User
from app.auth import hash_password

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Seed Admin / Test User if not exists
        if db.query(User).count() == 0:
            demo_user = User(
                username="demouser",
                email="user@example.com",
                password_hash=hash_password("password123"),
                role="user"
            )
            admin_user = User(
                username="admin",
                email="admin@hotel.com",
                password_hash=hash_password("admin123"),
                role="admin"
            )
            db.add_all([demo_user, admin_user])
            db.commit()
            print("Demo users seeded: 'demouser' / 'password123', 'admin' / 'admin123'")

        # Seed Rooms if not exists or update prices to INR
        if db.query(Room).count() == 0:
            sample_rooms = [
                Room(
                    room_number="101",
                    room_type="Single Economy",
                    price_per_night=799.0,
                    capacity=1,
                    description="Cozy room perfect for solo travelers with high-speed WiFi and working desk.",
                    amenities="WiFi, Air Conditioning, Work Desk, Smart TV",
                    image_url="https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80",
                    is_available=True
                ),
                Room(
                    room_number="102",
                    room_type="Standard Double",
                    price_per_night=1299.0,
                    capacity=2,
                    description="Spacious double room featuring a queen bed, city views, and modern bathroom.",
                    amenities="WiFi, Queen Bed, Minibar, Air Conditioning, City View",
                    image_url="https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80",
                    is_available=True
                ),
                Room(
                    room_number="201",
                    room_type="Deluxe Suite",
                    price_per_night=1899.0,
                    capacity=2,
                    description="Luxurious suite with king-size bed, private balcony, Jacuzzi, and complimentary breakfast.",
                    amenities="King Bed, Balcony, Jacuzzi, Breakfast Included, Ocean View, WiFi",
                    image_url="https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80",
                    is_available=True
                ),
                Room(
                    room_number="202",
                    room_type="Family Suite",
                    price_per_night=2399.0,
                    capacity=4,
                    description="Two-bedroom family suite with lounge area, kitchenette, and play corner.",
                    amenities="2 Bedrooms, Kitchenette, Lounge, Breakfast Included, Free Parking",
                    image_url="https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80",
                    is_available=True
                ),
                Room(
                    room_number="301",
                    room_type="Executive Presidential Suite",
                    price_per_night=2999.0,
                    capacity=3,
                    description="Top floor penthouse suite with 360-degree skyline views, personal concierge service, and private lounge.",
                    amenities="Penthouse View, Private Bar, Jacuzzi, Concierge, Airport Transfer",
                    image_url="https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80",
                    is_available=True
                ),
            ]
            db.add_all(sample_rooms)
            db.commit()
            print("Sample rooms seeded successfully in INR (₹799 - ₹2999).")
        else:
            # Sync existing rooms to the new ₹799 - ₹2999 price range
            inr_prices = {"101": 799.0, "102": 1299.0, "201": 1899.0, "202": 2399.0, "301": 2999.0}
            rooms = db.query(Room).all()
            for room in rooms:
                if room.room_number in inr_prices:
                    room.price_per_night = inr_prices[room.room_number]
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
