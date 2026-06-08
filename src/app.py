"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import hashlib
import hmac
import secrets
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str


class LoginRequest(BaseModel):
    email: str
    password: str


users = {
    "teacher@mergington.edu": {
        "email": "teacher@mergington.edu",
        "role": "mentor",
        "password_hash": "",
    }
}

# In-memory token store (session-style auth token).
tokens = {}


def _hash_password(password: str, salt: str) -> str:
    hashed_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return hashed_bytes.hex()


def _create_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"{salt}${_hash_password(password, salt)}"


def _verify_password(password: str, password_hash: str) -> bool:
    salt, saved_hash = password_hash.split("$", maxsplit=1)
    provided_hash = _hash_password(password, salt)
    return hmac.compare_digest(saved_hash, provided_hash)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_role(role: str) -> str:
    normalized_role = role.strip().lower()
    if normalized_role not in {"student", "mentor"}:
        raise HTTPException(status_code=400, detail="Role must be student or mentor")
    return normalized_role


def get_current_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.replace("Bearer ", "", 1).strip()
    email = tokens.get(token)

    if not email or email not in users:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return users[email]


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/register")
def register_user(payload: RegisterRequest):
    email = _normalize_email(payload.email)
    role = _validate_role(payload.role)

    if "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if email in users:
        raise HTTPException(status_code=409, detail="User already exists")

    users[email] = {
        "email": email,
        "role": role,
        "password_hash": _create_password_hash(payload.password),
    }

    return {
        "message": "User registered successfully",
        "user": {
            "email": email,
            "role": role,
        },
    }


@app.post("/auth/login")
def login_user(payload: LoginRequest):
    email = _normalize_email(payload.email)
    user = users.get(email)

    if not user or not _verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = secrets.token_urlsafe(32)
    tokens[token] = email

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "role": user["role"],
        },
    }


@app.get("/auth/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "role": current_user["role"],
    }


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, current_user=Depends(get_current_user)):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can sign up for activities")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    email = current_user["email"]
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, current_user=Depends(get_current_user)):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can unregister from activities")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    email = current_user["email"]
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


users["teacher@mergington.edu"]["password_hash"] = _create_password_hash("mentor123")
