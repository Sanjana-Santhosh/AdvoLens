"""
DBSCAN-based geographic clustering for hotspot detection.
"""
import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape

from app.models.issue import Issue


def calculate_hotspots(
    db: Session, 
    eps_meters: int = 100, 
    min_samples: int = 3,
    status_filter: str | None = "Open"
) -> list[dict]:
    """
    Find issue hotspots using DBSCAN clustering algorithm.
    
    Args:
        db: Database session
        eps_meters: Maximum distance between points in a cluster (default 100m)
        min_samples: Minimum issues to form a hotspot (default 3)
        status_filter: Filter by status (default "Open", None for all)
    
    Returns:
        List of hotspot dictionaries with center coordinates and issue counts,
        sorted by issue count descending.
    """
    # Build query
    query = db.query(Issue)
    if status_filter:
        query = query.filter(Issue.status == status_filter)
    
    issues = query.all()
    
    if len(issues) < min_samples:
        return []
    
    # Extract coordinates from PostGIS geometry
    coords = []
    issue_ids = []
    issue_data = []
    
    for issue in issues:
        try:
            point = to_shape(issue.location)
            coords.append([point.y, point.x])  # lat, lon for haversine
            issue_ids.append(issue.id)
            issue_data.append({
                "id": issue.id,
                "caption": issue.caption,
                "status": issue.status,
                "department": issue.department
            })
        except Exception:
            continue  # Skip issues without valid geometry
    
    if len(coords) < min_samples:
        return []
    
    coords_array = np.array(coords)
    
    # Convert meters to approximate degrees for DBSCAN
    # At equator: 1 degree ≈ 111km, but haversine metric uses radians
    # For haversine metric, we need epsilon in radians
    earth_radius_km = 6371.0
    eps_km = eps_meters / 1000.0
    eps_radians = eps_km / earth_radius_km
    
    # Run DBSCAN with haversine metric (expects radians)
    coords_radians = np.radians(coords_array)
    clustering = DBSCAN(
        eps=eps_radians, 
        min_samples=min_samples, 
        metric='haversine'
    ).fit(coords_radians)
    
    # Group results by cluster
    hotspots = []
    unique_labels = set(clustering.labels_)
    
    for cluster_id in unique_labels:
        if cluster_id == -1:  # Skip noise points
            continue
        
        # Get indices of points in this cluster
        cluster_mask = clustering.labels_ == cluster_id
        cluster_coords = coords_array[cluster_mask]
        cluster_issue_ids = [issue_ids[i] for i, is_member in enumerate(cluster_mask) if is_member]
        cluster_issues = [issue_data[i] for i, is_member in enumerate(cluster_mask) if is_member]
        
        # Calculate centroid
        center_lat = float(cluster_coords[:, 0].mean())
        center_lon = float(cluster_coords[:, 1].mean())
        
        # Get department distribution
        dept_counts = {}
        for issue in cluster_issues:
            dept = issue.get("department", "unknown")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        hotspots.append({
            "cluster_id": int(cluster_id),
            "center": {
                "lat": center_lat, 
                "lon": center_lon
            },
            "issue_count": len(cluster_issue_ids),
            "issue_ids": cluster_issue_ids,
            "departments": dept_counts,
            "primary_department": max(dept_counts, key=dept_counts.get) if dept_counts else None
        })
    
    # Sort by issue count descending
    return sorted(hotspots, key=lambda x: x['issue_count'], reverse=True)


def get_cluster_summary(db: Session) -> dict:
    """
    Get a summary of all clusters for analytics dashboard.
    """
    hotspots = calculate_hotspots(db, eps_meters=100, min_samples=3)
    
    total_clustered_issues = sum(h['issue_count'] for h in hotspots)
    
    return {
        "total_hotspots": len(hotspots),
        "total_clustered_issues": total_clustered_issues,
        "hotspots": hotspots[:10],  # Top 10 hotspots
        "department_breakdown": _aggregate_departments(hotspots)
    }


def _aggregate_departments(hotspots: list[dict]) -> dict:
    """Aggregate department counts across all hotspots."""
    total = {}
    for hotspot in hotspots:
        for dept, count in hotspot.get("departments", {}).items():
            total[dept] = total.get(dept, 0) + count
    return total
