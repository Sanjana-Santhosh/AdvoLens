from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Any
from datetime import datetime


class IssueBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class IssueCreate(IssueBase):
    pass


class IssueResponse(IssueBase):
    id: int
    image_url: str
    status: str
    caption: Optional[str] = None
    tags: Optional[List[str]] = None
    department: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def extract_coordinates(cls, data: Any) -> Any:
        """Extract lat/lon from PostGIS geometry if present"""
        if hasattr(data, '__dict__'):
            # It's an ORM model
            obj_dict = {}
            for key in ['id', 'title', 'description', 'image_url', 'status', 
                       'caption', 'tags', 'created_at']:
                obj_dict[key] = getattr(data, key, None)
            
            # Extract department value
            department = getattr(data, 'department', None)
            if department is not None:
                obj_dict['department'] = department.value if hasattr(department, 'value') else str(department)
            else:
                obj_dict['department'] = None
            
            # Extract coordinates from PostGIS geometry
            location = getattr(data, 'location', None)
            if location is not None:
                try:
                    # Import here to avoid circular imports
                    from geoalchemy2.shape import to_shape
                    point = to_shape(location)
                    obj_dict['lon'] = point.x
                    obj_dict['lat'] = point.y
                except Exception:
                    obj_dict['lat'] = None
                    obj_dict['lon'] = None
            else:
                obj_dict['lat'] = None
                obj_dict['lon'] = None
            
            return obj_dict
        return data
