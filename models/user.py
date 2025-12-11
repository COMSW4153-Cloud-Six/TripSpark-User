# create the user 
from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from .userprofile import UserProfile  


# --- Base model ---
class UserBase(BaseModel):
    full_name: str = Field(
        ...,
        description="Full name of the registered user.",
        example="Jane Doe",
    )
    email: str = Field(
        ...,
        description="Unique email address of the user.",
        example="jane.doe@example.com",
    )
    home_city: Optional[str] = Field(
        None,
        description="User's home or base city.",
        example="New York",
    )
    country: Optional[str] = Field(
        None,
        description="Country of residence.",
        example="USA",
    )
    profile_photo_url: Optional[str] = Field(
        None,
        description=(
            "Optional link to user's avatar or profile picture. "
            "If not provided, no picture is required."
        ),
        example=None,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "full_name": "Jane Doe",
                    "email": "jane.doe@example.com",
                    "home_city": "New York",
                    "country": "USA",
                    "profile_photo_url": None,
                }
            ]
        }
    }

UserCreate = UserBase

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, description="Updated full name of the user.")
    email: Optional[str] = Field(None, description="Updated email address.")
    home_city: Optional[str] = Field(None, description="Updated home city.")
    country: Optional[str] = Field(None, description="Updated country.")
    profile_photo_url: Optional[str] = Field(
        None,
        description="Updated profile photo URL. If not provided, no picture is required.",
        example=None,
    )
    profile: Optional[dict] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "full_name": "Jane D.",
                    "home_city": "Los Angeles",
                    "country": "USA",
                    "profile_photo_url": None,
                }
            ]
        }
    }

# --- Read model ---
class UserRead(UserBase):
    """Model returned when reading a user."""
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the user.",
        json_schema_extra={"example": "11111111-2222-4333-8444-555555555555"},
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Account creation timestamp (UTC).",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-01-16T12:00:00Z"},
    )
    # Relationship: one User → one UserProfile
    profile: Optional[UserProfile] = Field(
        None,
        description="Associated travel profile containing preferences and history.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "11111111-2222-4333-8444-555555555555",
                "full_name": "Jane Doe",
                "email": "jane.doe@example.com",
                "home_city": "New York",
                "country": "USA",
                "profile_photo_url": None,
                "created_at": "2025-01-15T10:20:30Z",
                "updated_at": "2025-01-16T12:00:00Z",
                "profile": {
                    "id": "8d6f8f5e-3f3e-4b0a-9c3a-2c0b1b2f3a44",
                    "user_id": "11111111-2222-4333-8444-555555555555",
                    "spending_preference": "medium",
                    "trip_style": "walkable",
                    "preferred_vibes": ["artsy", "cozy"],
                    "favorite_foods": ["coffee", "ramen"],
                    "cities_visited": [{"name": "Tokyo", "rating": 5.0}],
                    "cities_saved": ["Seoul", "Lisbon"],
                },
            }
        }
    }
