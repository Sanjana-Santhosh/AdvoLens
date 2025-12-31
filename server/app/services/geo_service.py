"""
Geo-spatial service for proximity detection using PostGIS.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement
from geoalchemy2.types import Geography

from app.models.issue import Issue


def find_nearby_issues(
    db: Session, 
    lat: float, 
    lon: float, 
    radius_meters: int = 50,
    exclude_issue_id: int | None = None
) -> list[Issue]:
    """
    Find issues within radius using PostGIS ST_DWithin.
    
    Args:
        db: Database session
        lat: Latitude of the point
        lon: Longitude of the point
        radius_meters: Search radius in meters (default 50m)
        exclude_issue_id: Optional issue ID to exclude from results
    
    Returns:
        List of Issue objects within the radius
    """
    # Create WKT point (note: PostGIS uses lon, lat order)
    point = WKTElement(f'POINT({lon} {lat})', srid=4326)
    
    # Build query with ST_DWithin for geographic distance in meters
    query = db.query(Issue).filter(
        func.ST_DWithin(
            func.cast(Issue.location, Geography),
            func.cast(point, Geography),
            radius_meters
        )
    )
    
    # Exclude specific issue if provided (useful when updating)
    if exclude_issue_id:
        query = query.filter(Issue.id != exclude_issue_id)
    
    return query.all()


def calculate_distance_meters(
    db: Session,
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
) -> float:
    """
    Calculate distance between two points in meters using PostGIS.
    """
    point1 = WKTElement(f'POINT({lon1} {lat1})', srid=4326)
    point2 = WKTElement(f'POINT({lon2} {lat2})', srid=4326)
    
    result = db.execute(
        func.ST_Distance(
            func.cast(point1, Geography),
            func.cast(point2, Geography)
        )
    ).scalar()
    
    return float(result) if result else 0.0
