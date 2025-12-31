"""
Analytics API endpoints for hotspots and geo-clustering.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import StringIO
import csv
from datetime import datetime

from app.core.database import get_db
from app.ml.geo_clustering import calculate_hotspots, get_cluster_summary
from app.models.issue import Issue

router = APIRouter()


@router.get("/hotspots")
def get_hotspots(
    eps_meters: int = Query(100, ge=10, le=1000, description="Cluster radius in meters"),
    min_samples: int = Query(3, ge=2, le=10, description="Minimum issues to form a cluster"),
    status: str | None = Query("Open", description="Filter by status (Open, In Progress, Resolved, or null for all)"),
    db: Session = Depends(get_db)
):
    """
    Get geographic hotspots of issue clusters using DBSCAN algorithm.
    
    - **eps_meters**: Maximum distance between points in a cluster (default 100m)
    - **min_samples**: Minimum number of issues to form a hotspot (default 3)
    - **status**: Filter by issue status (default: Open)
    
    Returns list of hotspots with center coordinates, issue counts, and department breakdown.
    """
    # Handle "null" string or empty status
    status_filter = status if status and status.lower() != "null" else None
    
    hotspots = calculate_hotspots(
        db, 
        eps_meters=eps_meters, 
        min_samples=min_samples,
        status_filter=status_filter
    )
    
    return {
        "hotspots": hotspots,
        "count": len(hotspots),
        "params": {
            "eps_meters": eps_meters,
            "min_samples": min_samples,
            "status_filter": status_filter
        }
    }


@router.get("/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Get analytics summary including hotspot overview and department breakdown.
    """
    summary = get_cluster_summary(db)
    return summary


@router.get("/heatmap-data")
def get_heatmap_data(
    status: str | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    Get issue locations formatted for heatmap visualization.
    Returns array of [lon, lat, intensity] for Mapbox heatmap layer.
    """
    from app.models.issue import Issue
    from geoalchemy2.shape import to_shape
    
    query = db.query(Issue)
    if status:
        query = query.filter(Issue.status == status)
    
    issues = query.all()
    
    heatmap_points = []
    for issue in issues:
        try:
            point = to_shape(issue.location)
            # [lon, lat, intensity] - intensity could be based on priority/upvotes
            heatmap_points.append([point.x, point.y, 1])
        except Exception:
            continue
    
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [p[0], p[1]]
                },
                "properties": {
                    "intensity": p[2]
                }
            }
            for p in heatmap_points
        ]
    }


@router.get("/export/issues")
def export_issues_csv(
    status: str | None = Query(None, description="Filter by status"),
    department: str | None = Query(None, description="Filter by department"),
    db: Session = Depends(get_db)
):
    """
    Export all issues to CSV for admin reporting.
    """
    from geoalchemy2.shape import to_shape
    
    query = db.query(Issue)
    
    if status:
        query = query.filter(Issue.status == status)
    if department:
        query = query.filter(Issue.department == department)
    
    issues = query.order_by(Issue.priority_score.desc()).all()
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        'ID', 
        'Status', 
        'Department', 
        'Caption', 
        'Tags', 
        'Upvotes',
        'Priority Score',
        'Created At',
        'Latitude',
        'Longitude'
    ])
    
    # Data rows
    for issue in issues:
        # Extract coordinates
        lat, lon = None, None
        try:
            if issue.location:
                point = to_shape(issue.location)
                lat, lon = point.y, point.x
        except Exception:
            pass
        
        # Get department value
        dept = issue.department.value if hasattr(issue.department, 'value') else str(issue.department)
        
        writer.writerow([
            issue.id,
            issue.status,
            dept,
            issue.caption or "",
            ",".join(issue.tags or []),
            issue.upvote_count or 0,
            issue.priority_score or 0,
            issue.created_at.strftime("%Y-%m-%d %H:%M") if issue.created_at else "",
            lat or "",
            lon or ""
        ])
    
    output.seek(0)
    
    filename = f"advolens_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/priority-issues")
def get_priority_issues(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get top priority issues sorted by priority score.
    """
    from geoalchemy2.shape import to_shape
    
    issues = db.query(Issue).filter(
        Issue.status.in_(["Open", "In Progress"])
    ).order_by(Issue.priority_score.desc()).limit(limit).all()
    
    result = []
    for issue in issues:
        # Extract coordinates
        lat, lon = None, None
        try:
            if issue.location:
                point = to_shape(issue.location)
                lat, lon = point.y, point.x
        except Exception:
            pass
        
        dept = issue.department.value if hasattr(issue.department, 'value') else str(issue.department)
        
        result.append({
            "id": issue.id,
            "caption": issue.caption,
            "status": issue.status,
            "department": dept,
            "upvote_count": issue.upvote_count or 0,
            "priority_score": issue.priority_score or 0,
            "tags": issue.tags,
            "lat": lat,
            "lon": lon,
            "created_at": issue.created_at.isoformat() if issue.created_at else None
        })
    
    return {"issues": result, "count": len(result)}
