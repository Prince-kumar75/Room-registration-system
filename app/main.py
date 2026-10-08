from fastapi import FastAPI, Depends, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Optional

from app.database import engine, Base, get_db
from app.models import User, Room, Booking
from app.auth import hash_password, verify_password, get_current_user_from_cookie
from app.seed import seed_database

# Initialize Database tables and Seed data
Base.metadata.create_all(bind=engine)
seed_database()

app = FastAPI(title="Room Registration & Booking System")

# Static files and Template configuration
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# Helper to render templates with current_user & request context
def render(template_name: str, request: Request, current_user: Optional[User], context: dict = None):
    ctx = {
        "request": request,
        "current_user": current_user,
    }
    if context:
        ctx.update(context)
    return templates.TemplateResponse(request=request, name=template_name, context=ctx)


# -------------------------------------------------------------
# Home & Room Catalog Routes
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
@app.get("/rooms", response_class=HTMLResponse)
def view_available_rooms(
    request: Request,
    room_type: Optional[str] = None,
    min_capacity: Optional[int] = None,
    max_price: Optional[float] = None,
    msg: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    query = db.query(Room).filter(Room.is_available == True)

    if room_type:
        query = query.filter(Room.room_type == room_type)
    if min_capacity:
        query = query.filter(Room.capacity >= min_capacity)
    if max_price:
        query = query.filter(Room.price_per_night <= max_price)

    rooms = query.all()

    return render("rooms.html", request, current_user, {
        "rooms": rooms,
        "selected_type": room_type,
        "selected_capacity": min_capacity,
        "selected_max_price": max_price,
        "msg": msg,
        "error": error
    })


# -------------------------------------------------------------
# Select Room & Room Details
# -------------------------------------------------------------
@app.get("/rooms/{room_id}", response_class=HTMLResponse)
def select_room_detail(
    room_id: int,
    request: Request,
    msg: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        return RedirectResponse(url="/rooms?error=Room+not+found", status_code=status.HTTP_303_SEE_OTHER)

    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    return render("room_detail.html", request, current_user, {
        "room": room,
        "today": today,
        "tomorrow": tomorrow,
        "msg": msg,
        "error": error
    })


# -------------------------------------------------------------
# Book Room
# -------------------------------------------------------------
@app.post("/rooms/{room_id}/book")
def book_room(
    room_id: int,
    check_in_date: str = Form(...),
    check_out_date: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/login?error=Please+login+to+book+a+room", status_code=status.HTTP_303_SEE_OTHER)

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room or not room.is_available:
        return RedirectResponse(url="/rooms?error=Room+is+no+longer+available", status_code=status.HTTP_303_SEE_OTHER)

    try:
        in_date = datetime.strptime(check_in_date, "%Y-%m-%d").date()
        out_date = datetime.strptime(check_out_date, "%Y-%m-%d").date()
    except ValueError:
        return RedirectResponse(url=f"/rooms/{room_id}?error=Invalid+date+format", status_code=status.HTTP_303_SEE_OTHER)

    if out_date <= in_date:
        return RedirectResponse(
            url=f"/rooms/{room_id}?error=Check-out+date+must+be+after+Check-in+date",
            status_code=status.HTTP_303_SEE_OTHER
        )

    nights = (out_date - in_date).days
    total_price = nights * room.price_per_night

    new_booking = Booking(
        user_id=current_user.id,
        room_id=room.id,
        check_in_date=in_date,
        check_out_date=out_date,
        total_price=total_price,
        status="BOOKED"
    )

    db.add(new_booking)
    db.commit()

    return RedirectResponse(
        url=f"/history?msg=Room+#{room.room_number}+booked+successfully!",
        status_code=status.HTTP_303_SEE_OTHER
    )


# -------------------------------------------------------------
# Check-in Action
# -------------------------------------------------------------
@app.post("/bookings/{booking_id}/checkin")
def checkin_room(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == current_user.id).first()
    if not booking:
        return RedirectResponse(url="/history?error=Booking+not+found", status_code=status.HTTP_303_SEE_OTHER)

    if booking.status != "BOOKED":
        return RedirectResponse(
            url=f"/history?error=Cannot+check-in.+Current+status:+{booking.status}",
            status_code=status.HTTP_303_SEE_OTHER
        )

    booking.status = "CHECKED_IN"
    db.commit()

    return RedirectResponse(
        url=f"/history?msg=Checked+in+to+Room+#{booking.room.room_number}+successfully!",
        status_code=status.HTTP_303_SEE_OTHER
    )


# -------------------------------------------------------------
# Check-out Action
# -------------------------------------------------------------
@app.post("/bookings/{booking_id}/checkout")
def checkout_room(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == current_user.id).first()
    if not booking:
        return RedirectResponse(url="/history?error=Booking+not+found", status_code=status.HTTP_303_SEE_OTHER)

    if booking.status != "CHECKED_IN":
        return RedirectResponse(
            url=f"/history?error=Cannot+check-out.+Current+status:+{booking.status}",
            status_code=status.HTTP_303_SEE_OTHER
        )

    booking.status = "CHECKED_OUT"
    db.commit()

    return RedirectResponse(
        url=f"/history?msg=Checked+out+from+Room+#{booking.room.room_number}+successfully.+Thank+you+for+staying!",
        status_code=status.HTTP_303_SEE_OTHER
    )


# -------------------------------------------------------------
# Cancel Booking
# -------------------------------------------------------------
@app.post("/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == current_user.id).first()
    if not booking:
        return RedirectResponse(url="/history?error=Booking+not+found", status_code=status.HTTP_303_SEE_OTHER)

    if booking.status != "BOOKED":
        return RedirectResponse(
            url=f"/history?error=Only+active+un-checked-in+bookings+can+be+cancelled",
            status_code=status.HTTP_303_SEE_OTHER
        )

    booking.status = "CANCELLED"
    db.commit()

    return RedirectResponse(
        url="/history?msg=Booking+cancelled+successfully",
        status_code=status.HTTP_303_SEE_OTHER
    )


# -------------------------------------------------------------
# Booking History View
# -------------------------------------------------------------
@app.get("/history", response_class=HTMLResponse)
def view_booking_history(
    request: Request,
    msg: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/login?error=Please+login+to+view+your+booking+history", status_code=status.HTTP_303_SEE_OTHER)

    bookings = db.query(Booking).filter(Booking.user_id == current_user.id).order_by(Booking.created_at.desc()).all()

    return render("history.html", request, current_user, {
        "bookings": bookings,
        "msg": msg,
        "error": error
    })


# -------------------------------------------------------------
# Admin / Master All Bookings View
# -------------------------------------------------------------
@app.get("/admin/bookings", response_class=HTMLResponse)
def view_all_bookings(
    request: Request,
    status_filter: Optional[str] = None,
    msg: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/login?error=Please+login+to+access+all+bookings", status_code=status.HTTP_303_SEE_OTHER)

    query = db.query(Booking)
    if status_filter:
        query = query.filter(Booking.status == status_filter)

    bookings = query.order_by(Booking.created_at.desc()).all()

    return render("admin_bookings.html", request, current_user, {
        "bookings": bookings,
        "selected_status": status_filter,
        "msg": msg,
        "error": error
    })


# -------------------------------------------------------------
# Authentication Routes (Register, Login, Logout)
# -------------------------------------------------------------
@app.get("/register", response_class=HTMLResponse)
def register_page(
    request: Request,
    error: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    if current_user:
        return RedirectResponse(url="/rooms", status_code=status.HTTP_303_SEE_OTHER)
    return render("register.html", request, current_user, {"error": error})


@app.post("/register")
def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return RedirectResponse(
            url="/register?error=Username+or+Email+already+exists",
            status_code=status.HTTP_303_SEE_OTHER
        )

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()

    response = RedirectResponse(url="/rooms?msg=Account+created+successfully!+Logged+in.", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_session", value=str(user.id), httponly=True)
    return response


@app.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    msg: Optional[str] = None,
    error: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    if current_user:
        return RedirectResponse(url="/rooms", status_code=status.HTTP_303_SEE_OTHER)
    return render("login.html", request, current_user, {"msg": msg, "error": error})


@app.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(user.password_hash, password):
        return RedirectResponse(
            url="/login?error=Invalid+username+or+password",
            status_code=status.HTTP_303_SEE_OTHER
        )

    response = RedirectResponse(url="/rooms?msg=Welcome+back!+Logged+in+successfully.", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_session", value=str(user.id), httponly=True)
    return response


@app.get("/logout")
def logout_user():
    response = RedirectResponse(url="/login?msg=Logged+out+successfully", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="user_session")
    return response
