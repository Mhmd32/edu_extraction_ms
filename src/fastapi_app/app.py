import hashlib
import logging
import os
import pathlib
import uuid
from datetime import datetime
from typing import Optional

from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.sql import func
from sqlmodel import Session, select

from .models import Question, Restaurant, Review, User, engine

# Setup logger and Azure Monitor:
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor()


# Setup FastAPI app:
app = FastAPI()
parent_path = pathlib.Path(__file__).parent.parent
app.mount("/mount", StaticFiles(directory=parent_path / "static"), name="static")
templates = Jinja2Templates(directory=parent_path / "templates")
templates.env.globals["prod"] = os.environ.get("RUNNING_IN_PRODUCTION", False)
# Use relative path for url_for, so that it works behind a proxy like Codespaces
templates.env.globals["url_for"] = app.url_path_for


# Dependency to get the database session
def get_db_session():
    with Session(engine) as session:
        yield session


# ===== Pydantic Models for User Management =====

class UserCreate(BaseModel):
    username: str
    display_name: Optional[str] = None
    password: str
    is_admin: bool = False
    is_active: bool = True


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    display_name: Optional[str] = None
    is_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    id: uuid.UUID
    username: str
    display_name: Optional[str] = None
    is_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ===== Utility Functions =====

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    if password is None or password == "":
        raise HTTPException(status_code=400, detail="Password is required.")
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session: Session = Depends(get_db_session)):
    logger.info("root called")
    statement = (
        select(Restaurant, func.avg(Review.rating).label("avg_rating"), func.count(Review.id).label("review_count"))
        .outerjoin(Review, Review.restaurant == Restaurant.id)
        .group_by(Restaurant.id)
    )
    results = session.exec(statement).all()

    restaurants = []
    for restaurant, avg_rating, review_count in results:
        restaurant_dict = restaurant.dict()
        restaurant_dict["avg_rating"] = avg_rating
        restaurant_dict["review_count"] = review_count
        restaurant_dict["stars_percent"] = round((float(avg_rating) / 5.0) * 100) if review_count > 0 else 0
        restaurants.append(restaurant_dict)

    return templates.TemplateResponse("index.html", {"request": request, "restaurants": restaurants})


@app.get("/create", response_class=HTMLResponse)
async def create_restaurant(request: Request):
    logger.info("Request for add restaurant page received")
    return templates.TemplateResponse("create_restaurant.html", {"request": request})


@app.post("/add", response_class=RedirectResponse)
async def add_restaurant(
    request: Request, restaurant_name: str = Form(...), street_address: str = Form(...), description: str = Form(...),
    session: Session = Depends(get_db_session)
):
    logger.info("name: %s address: %s description: %s", restaurant_name, street_address, description)
    restaurant = Restaurant()
    restaurant.name = restaurant_name
    restaurant.street_address = street_address
    restaurant.description = description
    session.add(restaurant)
    session.commit()
    session.refresh(restaurant)

    return RedirectResponse(url=app.url_path_for("details", id=restaurant.id), status_code=status.HTTP_303_SEE_OTHER)


@app.get("/details/{id}", response_class=HTMLResponse)
async def details(request: Request, id: int, session: Session = Depends(get_db_session)):
    restaurant = session.exec(select(Restaurant).where(Restaurant.id == id)).first()
    reviews = session.exec(select(Review).where(Review.restaurant == id)).all()

    review_count = len(reviews)

    avg_rating = 0
    if review_count > 0:
        avg_rating = sum(review.rating for review in reviews if review.rating is not None) / review_count

    restaurant_dict = restaurant.dict()
    restaurant_dict["avg_rating"] = avg_rating
    restaurant_dict["review_count"] = review_count
    restaurant_dict["stars_percent"] = round((float(avg_rating) / 5.0) * 100) if review_count > 0 else 0

    return templates.TemplateResponse(
        "details.html", {"request": request, "restaurant": restaurant_dict, "reviews": reviews}
    )


@app.post("/review/{id}", response_class=RedirectResponse)
async def add_review(
    request: Request,
    id: int,
    user_name: str = Form(...),
    rating: str = Form(...),
    review_text: str = Form(...),
    session: Session = Depends(get_db_session),
):
    review = Review()
    review.restaurant = id
    review.review_date = datetime.now()
    review.user_name = user_name
    review.rating = int(rating)
    review.review_text = review_text
    session.add(review)
    session.commit()

    return RedirectResponse(url=app.url_path_for("details", id=id), status_code=status.HTTP_303_SEE_OTHER)


# ===== User Management Endpoints =====

@app.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(user_data: UserCreate, session: Session = Depends(get_db_session)):
    """Create a new user."""
    logger.info("Creating new user: %s", user_data.username)
    
    # Check if username already exists
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash the password
    password_hash = hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        id=uuid.uuid4(),
        username=user_data.username,
        display_name=user_data.display_name,
        password_hash=password_hash,
        is_admin=user_data.is_admin,
        is_active=user_data.is_active,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return new_user


@app.get("/users", response_model=list[UserResponse])
async def list_users(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session)
):
    """List all users with pagination."""
    logger.info("Listing users with limit=%d, offset=%d", limit, offset)
    
    statement = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    users = session.exec(statement).all()
    
    return users


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    session: Session = Depends(get_db_session)
):
    """Update an existing user."""
    logger.info("Updating user: %s", user_id)
    
    # Find the user
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields if provided
    if user_data.display_name is not None:
        user.display_name = user_data.display_name
    
    if user_data.password is not None:
        user.password_hash = hash_password(user_data.password)
    
    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.now()
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


@app.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, session: Session = Depends(get_db_session)):
    """Authenticate a user and return user information."""
    logger.info("Login attempt for username: %s", login_data.username)
    
    # Find user by username
    user = session.exec(select(User).where(User.username == login_data.username)).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    # Verify password
    password_hash = hash_password(login_data.password)
    if password_hash != user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Return user information (excluding password_hash)
    return LoginResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
