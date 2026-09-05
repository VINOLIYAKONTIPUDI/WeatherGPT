from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.entities import Alert, Location, User, UserLocation, UserRole, LanguageCode
from app.db.session import Base, engine


SEED_LOCATIONS = [
    {
        "name": "Vijayawada",
        "district": "NTR",
        "state": "Andhra Pradesh",
        "latitude": 16.5062,
        "longitude": 80.6480,
    },
    {
        "name": "Hyderabad",
        "district": "Hyderabad",
        "state": "Telangana",
        "latitude": 17.3850,
        "longitude": 78.4867,
    },
    {
        "name": "Visakhapatnam",
        "district": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "latitude": 17.6868,
        "longitude": 83.2185,
    },
    {
        "name": "New Delhi",
        "district": "New Delhi",
        "state": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090,
    },
    {
        "name": "Mumbai",
        "district": "Mumbai",
        "state": "Maharashtra",
        "latitude": 19.0760,
        "longitude": 72.8777,
    },
    {
        "name": "Chennai",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "latitude": 13.0827,
        "longitude": 80.2707,
    },
    {
        "name": "Kolkata",
        "district": "Kolkata",
        "state": "West Bengal",
        "latitude": 22.5726,
        "longitude": 88.3639,
    },
    {
        "name": "Bengaluru",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "latitude": 12.9716,
        "longitude": 77.5946,
    },
]


def init_db(db: Session) -> None:
    Base.metadata.create_all(bind=engine)
    if db.query(Location).count() == 0:
        for loc in SEED_LOCATIONS:
            db.add(Location(**loc))
        db.commit()

    if db.query(User).filter(User.phone == "9999999999").first() is None:
        demo_users = [
            User(
                name="Demo Public User",
                phone="9999999999",
                email="public@demo.weathergpt.in",
                role=UserRole.public,
                preferred_language=LanguageCode.en,
            ),
            User(
                name="Demo Researcher",
                phone="9999999998",
                email="researcher@demo.weathergpt.in",
                role=UserRole.researcher,
                preferred_language=LanguageCode.en,
            ),
            User(
                name="Demo Disaster Manager",
                phone="9999999997",
                email="disaster@demo.weathergpt.in",
                role=UserRole.disaster_manager,
                preferred_language=LanguageCode.en,
            ),
            User(
                name="Demo Admin",
                phone="9999999996",
                email="admin@demo.weathergpt.in",
                role=UserRole.admin,
                preferred_language=LanguageCode.en,
            ),
        ]
        db.add_all(demo_users)
        db.commit()
        vja = db.query(Location).filter(Location.name == "Vijayawada").first()
        if vja:
            for user in demo_users:
                db.add(UserLocation(user_id=user.id, location_id=vja.id, is_primary=True))
            db.commit()

    if db.query(Alert).count() == 0:
        vja = db.query(Location).filter(Location.name == "Vijayawada").first()
        now = datetime.utcnow()
        db.add(
            Alert(
                alert_type="cyclone",
                severity="severe",
                title="[DEMO DATA] Cyclone warning — coastal Andhra Pradesh",
                description=(
                    "[DEMO DATA] A simulated severe cyclonic storm is approaching the "
                    "Andhra Pradesh coast. Heavy rainfall and strong winds expected near Vijayawada. "
                    "This is demonstration data, not an official IMD warning."
                ),
                affected_location="Vijayawada",
                district="NTR",
                latitude=vja.latitude if vja else 16.5,
                longitude=vja.longitude if vja else 80.6,
                start_time=now,
                end_time=now + timedelta(hours=48),
                source="DEMO / mock IMD feed",
                cyclone_path={
                    "points": [
                        {"lat": 14.5, "lon": 84.2, "t": "T+0"},
                        {"lat": 15.4, "lon": 82.8, "t": "T+12"},
                        {"lat": 16.2, "lon": 81.4, "t": "T+24"},
                        {"lat": 16.5, "lon": 80.6, "t": "T+36"},
                    ]
                },
                warning_zones={
                    "orange": ["Krishna", "NTR", "Guntur", "West Godavari"],
                    "yellow": ["Prakasam", "East Godavari"],
                },
                is_demo=True,
            )
        )
        db.add(
            Alert(
                alert_type="heatwave",
                severity="moderate",
                title="[DEMO DATA] Heatwave watch — inland Andhra Pradesh",
                description="[DEMO DATA] Daytime temperatures may exceed 40°C. Stay hydrated. Demonstration data only.",
                affected_location="Vijayawada",
                district="NTR",
                latitude=16.5062,
                longitude=80.6480,
                start_time=now,
                end_time=now + timedelta(hours=24),
                source="DEMO / mock IMD feed",
                is_demo=True,
            )
        )
        db.commit()
