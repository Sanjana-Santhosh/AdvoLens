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
    upvote_count: int = 0
    priority_score: int = 0
    comment_count: int = 0
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
                       'caption', 'tags', 'created_at', 'upvote_count', 'priority_score']:
                obj_dict[key] = getattr(data, key, None)
            
            # Set defaults for engagement fields
            obj_dict['upvote_count'] = obj_dict.get('upvote_count') or 0
            obj_dict['priority_score'] = obj_dict.get('priority_score') or 0
            
            # Count comments if relationship is loaded
            comments = getattr(data, 'comments', None)
            obj_dict['comment_count'] = len(comments) if comments else 0
            
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


class IssueCreateResponse(IssueResponse):
    """Extended response for issue creation that includes tracking token"""
    tracking_token: str
    duplicate_of: Optional[int] = None
    notification_message: str = "Save your tracking token to receive updates on your report!"

    @classmethod
    def from_issue(cls, issue, tracking_token: str, duplicate_of: Optional[int] = None):
        """Create response from Issue ORM model"""
        # Get base data using parent's validator logic
        base_data = IssueResponse.extract_coordinates(issue)
        
        return cls(
            **base_data,
            tracking_token=tracking_token,
            duplicate_of=duplicate_of
        )
