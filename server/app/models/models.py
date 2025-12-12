from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.core.database import Base

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=False)
    status = Column(String, default="Open")  # Open, In Progress, Resolved
    
    # GeoAlchemy2 Geometry column for PostGIS
    # We use 'POINT' with SRID 4326 (standard GPS lat/lon)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Note: We will add User and Embedding models later!
