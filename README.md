# Welcome Yard - Room Registration System

A full-stack **Room Registration & Booking System** built with **FastAPI**, **SQLAlchemy**, **PostgreSQL** (with dynamic SQLite fallback for easy local execution), and **HTML/CSS (Jinja2)**.

---

## 🌟 Key Features

- **User Authentication**: Register & Login with secure password hashing (PBKDF2) and session cookies.
- **Available Rooms View**: Browse rooms with dynamic filters (Room type, Guest capacity, and Maximum price in ₹).
- **Interactive Room Booking**: Select check-in and check-out dates with real-time night and total cost calculation.
- **Check-in & Check-out**: One-click check-in and check-out status tracking.
- **My Bookings History**: Guest view to track active and past reservations.
- **Master Admin View**: Hotel staff dashboard at `/admin/bookings` to monitor all guest registrations across the hotel.
- **Dual Database Support**: Seamless PostgreSQL support with automatic SQLite fallback (`sqlite:///./room_registration.db`) for zero-setup local execution.

---

## 🛠️ Tech Stack

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ORM / Database**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) & [PostgreSQL](https://www.postgresql.org/) / SQLite
- **Template Engine**: [Jinja2](https://jinja.palletsprojects.com/)
- **Styling**: Modern CSS3 & FontAwesome Icons

---

## 🚀 Quick Start Instructions

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Prince-kumar75/Room-registration-system.git
cd Room-registration-system
pip install -r requirements.txt
```

### 2. Run Application
```bash
python run.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser!

### 3. Demo Credentials
- **Demo User**: `demouser` | Password: `password123`
- **Admin**: `admin` | Password: `admin123`

---

## 🧪 Running Automated Tests
```bash
python -m pytest test_app.py
```
