from sqlalchemy.orm import Session

from app.models.entities import Location


class LocationService:
    def get_or_create(
        self,
        db: Session,
        name: str,
        latitude: float,
        longitude: float,
        district: str | None = None,
        state: str | None = None,
    ) -> Location:
        loc = (
            db.query(Location)
            .filter(Location.name == name, Location.latitude == latitude, Location.longitude == longitude)
            .first()
        )
        if loc:
            return loc
        loc = Location(
            name=name,
            district=district,
            state=state,
            latitude=latitude,
            longitude=longitude,
        )
        db.add(loc)
        db.commit()
        db.refresh(loc)
        return loc

    def search_db(self, db: Session, q: str) -> list[Location]:
        return (
            db.query(Location)
            .filter(Location.name.ilike(f"%{q}%"))
            .limit(10)
            .all()
        )

    def default_vijayawada(self, db: Session) -> Location | None:
        return db.query(Location).filter(Location.name == "Vijayawada").first()
