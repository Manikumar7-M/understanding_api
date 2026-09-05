import os
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "users.db")))


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    gender: str = Field(min_length=1, max_length=50)
    place: str = Field(min_length=1, max_length=100)


class User(UserCreate):
    id: int
    created_at: str


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """Create the table and add the original record only on first run."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with closing(get_connection()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL CHECK (age >= 0),
                gender TEXT NOT NULL,
                place TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0:
            connection.execute(
                "INSERT INTO users (name, age, gender, place) VALUES (?, ?, ?, ?)",
                ("Mani Kumar", 24, "male", "India"),
            )

        connection.commit()


initialize_database()
app = FastAPI()


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/users", response_model=list[User])
@app.get("/m", response_model=list[User], include_in_schema=False)
def list_users():
    with closing(get_connection()) as connection:
        rows = connection.execute(
            "SELECT id, name, age, gender, place, created_at FROM users ORDER BY id DESC"
        ).fetchall()

    return [dict(row) for row in rows]


@app.post("/users", response_model=User, status_code=201)
@app.post("/postList", response_model=User, status_code=201, include_in_schema=False)
def create_user(user: UserCreate):
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (name, age, gender, place)
            VALUES (?, ?, ?, ?)
            """,
            (user.name.strip(), user.age, user.gender.strip(), user.place.strip()),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id, name, age, gender, place, created_at FROM users WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return dict(row)


@app.get("/s")
def sample_message():
    return {"Hello": "Salaar", "prabahs": "rebel"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
