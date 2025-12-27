from sqlalchemy.orm import Session
from app.models.issue import Issue
from geoalchemy2.elements import WKTElement


def create_issue(db: Session, title: str | None, description: str | None, image_url: str, lat: float, lon: float):
    # PostGIS uses (lon, lat) order in WKT
    location_wkt = f"POINT({lon} {lat})"

    db_issue = Issue(
        title=title,
        description=description,
        image_url=image_url,
        location=WKTElement(location_wkt, srid=4326),
        status="Open",
    )
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    return db_issue


def get_issues(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Issue).offset(skip).limit(limit).all()


def get_issue(db: Session, issue_id: int):
    return db.query(Issue).filter(Issue.id == issue_id).first()
