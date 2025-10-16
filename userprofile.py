from __future__ import annotations

from typing import Optional, List, Literal
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

# lightweight enums (optional)
Spending = Literal["low", "medium", "high"]
TripPace = Literal["slow", "balanced", "packed"]
Season = Literal["spring", "summer", "fall", "winter"]
Transport = Literal["walk", "public_transit", "rideshare", "car_rental"]

# --- submodels for rating-enabled history ---
class CityVisit(BaseModel):
    name: str = Field(..., description="City name.", json_schema_extra={"example": "Tokyo"})
    rating: Optional[float] = Field(
        None, ge=0, le=5, description="User rating for the city (0–5).", json_schema_extra={"example": 5.0}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "Tokyo", "rating": 5.0},
                {"name": "New York", "rating": 4.0},
            ]
        }
    }


class PlaceVisit(BaseModel):
    name: str = Field(..., description="Place/POI name.", json_schema_extra={"example": "MoMA"})
    rating: Optional[float] = Field(
        None, ge=0, le=5, description="User rating for this place (0–5).", json_schema_extra={"example": 4.5}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "MoMA", "rating": 4.5},
                {"name": "Blue Bottle Chelsea", "rating": 4.8},
            ]
        }
    }


# --- main profile model (preferences + history) ---
class UserProfile(BaseModel):
    # identifiers
    id: UUID = Field(
        default_factory=uuid4,
        description="Persistent UserProfile ID (server-generated).",
        json_schema_extra={"example": "8d6f8f5e-3f3e-4b0a-9c3a-2c0b1b2f3a44"},
    )
    user_id: UUID = Field(
        ...,
        description="ID of the user this profile belongs to.",
        json_schema_extra={"example": "11111111-2222-4333-8444-555555555555"},
    )

    # preferences
    spending_preference: Optional[Spending] = Field(
        None, description='Overall spending preference: "low" | "medium" | "high".', json_schema_extra={"example": "medium"}
    )
    daily_budget_limit: Optional[float] = Field(
        None, ge=0, description="Approximate max daily spend.", json_schema_extra={"example": 150.0}
    )
    trip_style: Optional[str] = Field(
        None, description="Primary trip style (e.g., walkable, family, outdoors, artsy).", json_schema_extra={"example": "walkable"}
    )
    trip_pace: Optional[TripPace] = Field(
        None, description='Itinerary density: "slow" | "balanced" | "packed".', json_schema_extra={"example": "balanced"}
    )
    preferred_vibes: List[str] = Field(
        default_factory=list, description="Vibe descriptors (e.g., cozy, trendy, historic).", json_schema_extra={"example": ["artsy", "cozy"]}
    )
    favorite_foods: List[str] = Field(
        default_factory=list, description="Food & drink interests.", json_schema_extra={"example": ["coffee", "ramen"]}
    )
    favorite_activities: List[str] = Field(
        default_factory=list, description="Activity interests.", json_schema_extra={"example": ["museums", "cafes"]}
    )
    favorite_seasons: List[Season] = Field(
        default_factory=list, description="Preferred travel seasons.", json_schema_extra={"example": ["fall", "spring"]}
    )
    min_trip_days: Optional[int] = Field(
        None, ge=1, description="Typical minimum trip length (days).", json_schema_extra={"example": 3}
    )
    max_trip_days: Optional[int] = Field(
        None, ge=1, description="Typical maximum trip length (days).", json_schema_extra={"example": 7}
    )

    # convenience
    home_location: Optional[str] = Field(
        None, description="Home base location (city or broader).", json_schema_extra={"example": "New York"}
    )
    nearest_airport: Optional[str] = Field(
        None, description="Nearest/home airport (IATA).", json_schema_extra={"example": "JFK"}
    )
    transport_preferences: List[Transport] = Field(
        default_factory=list, description="Preferred transport modes.", json_schema_extra={"example": ["walk", "public_transit"]}
    )
    accessibility_notes: Optional[str] = Field(
        None, description="Mobility/accessibility notes.", json_schema_extra={"example": "Prefer short walks; avoid many stairs"}
    )

    # history (with ratings)
    cities_visited: List[CityVisit] = Field(
        default_factory=list,
        description="Visited cities with optional ratings.",
        json_schema_extra={"example": [{"name": "Tokyo", "rating": 5.0}, {"name": "New York", "rating": 4.0}]},
    )
    places_visited: List[PlaceVisit] = Field(
        default_factory=list,
        description="Visited places/POIs with optional ratings.",
        json_schema_extra={"example": [{"name": "MoMA", "rating": 4.5}, {"name": "Blue Bottle Chelsea", "rating": 4.8}]},
    )

    # saved (no ratings by design)
    cities_saved: List[str] = Field(
        default_factory=list, description="Saved/wishlist cities.", json_schema_extra={"example": ["Seoul", "Lisbon"]}
    )
    places_saved: List[str] = Field(
        default_factory=list, description="Saved places/POIs.", json_schema_extra={"example": ["Brooklyn Bridge", "Lafayette Bakery SoHo"]}
    )

    # timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp (UTC).", json_schema_extra={"example": "2025-01-15T10:20:30Z"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp (UTC).", json_schema_extra={"example": "2025-01-16T12:00:00Z"}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "8d6f8f5e-3f3e-4b0a-9c3a-2c0b1b2f3a44",
                    "user_id": "11111111-2222-4333-8444-555555555555",
                    "spending_preference": "medium",
                    "daily_budget_limit": 150.0,
                    "trip_style": "walkable",
                    "trip_pace": "balanced",
                    "preferred_vibes": ["artsy", "cozy"],
                    "favorite_foods": ["coffee", "ramen"],
                    "favorite_activities": ["museums", "cafes"],
                    "favorite_seasons": ["fall", "spring"],
                    "min_trip_days": 3,
                    "max_trip_days": 7,
                    "home_location": "New York",
                    "nearest_airport": "JFK",
                    "transport_preferences": ["walk", "public_transit"],
                    "accessibility_notes": "Prefer short walks; avoid many stairs",
                    "cities_visited": [{"name": "Tokyo", "rating": 5.0}, {"name": "New York", "rating": 4.0}],
                    "places_visited": [{"name": "MoMA", "rating": 4.5}, {"name": "Blue Bottle Chelsea", "rating": 4.8}],
                    "cities_saved": ["Seoul", "Lisbon"],
                    "places_saved": ["Brooklyn Bridge", "Lafayette Bakery SoHo"],
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    }

