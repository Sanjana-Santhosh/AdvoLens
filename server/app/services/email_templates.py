"""
Email Templates for AdvoLens

Builds branded HTML email bodies for department notifications.
"""

from typing import Optional


def build_new_issue_email(
    issue_id: int,
    caption: str,
    department: str,
    tags: list,
    lat: Optional[float],
    lon: Optional[float],
    image_url: str,
) -> str:
    """Build branded HTML email for a new issue alert."""
    dept_label = department.replace("_", " ").title()
    tags_html = "".join(
        f'<span style="background:#e5e7eb;padding:3px 8px;border-radius:4px;'
        f'font-size:12px;margin-right:4px;">{t}</span>'
        for t in (tags or [])
    )
    maps_link = (
        f'<a href="https://maps.google.com/?q={lat},{lon}" target="_blank">📍 View on Google Maps</a>'
        if lat is not None and lon is not None
        else "📍 Location not available"
    )
    coords_text = (
        f"{abs(lat):.4f}° {'N' if lat >= 0 else 'S'}, {abs(lon):.4f}° {'E' if lon >= 0 else 'W'}"
        if lat is not None and lon is not None
        else "—"
    )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body{{font-family:Arial,sans-serif;line-height:1.6;color:#333;margin:0;padding:0;background:#f3f4f6}}
    .wrap{{max-width:600px;margin:24px auto;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1)}}
    .hdr{{background:#2563eb;color:#fff;padding:24px 28px}}
    .hdr h2{{margin:0 0 4px 0;font-size:20px}}
    .hdr p{{margin:0;opacity:.85;font-size:14px}}
    .body{{background:#fff;padding:28px}}
    .row{{margin-bottom:14px}}
    .label{{font-weight:bold;color:#374151;font-size:13px;margin-bottom:2px}}
    .val{{color:#1f2937;font-size:14px}}
    .img-wrap{{margin-bottom:18px;border-radius:8px;overflow:hidden;border:1px solid #e5e7eb}}
    .img-wrap img{{width:100%;max-height:260px;object-fit:cover;display:block}}
    .btn{{display:inline-block;background:#2563eb;color:#fff;padding:11px 22px;
          border-radius:6px;text-decoration:none;font-weight:bold;font-size:14px;margin-top:8px}}
    .ftr{{background:#1f2937;color:#9ca3af;text-align:center;padding:16px;font-size:12px}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hdr">
      <h2>🔍 AdvoLens — Issue Alert</h2>
      <p>Issue #{issue_id} · {dept_label}</p>
    </div>
    <div class="body">
      <div class="img-wrap">
        <img src="{image_url}" alt="Issue photo" />
      </div>
      <div class="row">
        <div class="label">📌 Description</div>
        <div class="val">{caption or 'No description provided'}</div>
      </div>
      <div class="row">
        <div class="label">🏛️ Department</div>
        <div class="val">{dept_label}</div>
      </div>
      <div class="row">
        <div class="label">🏷️ Tags</div>
        <div class="val">{tags_html or '—'}</div>
      </div>
      <div class="row">
        <div class="label">📍 Coordinates</div>
        <div class="val">{coords_text}<br>{maps_link}</div>
      </div>
      <div class="row">
        <div class="label">🆔 Issue ID</div>
        <div class="val">#{issue_id}</div>
      </div>
      <p style="text-align:center;margin-top:24px">
        <a class="btn" href="https://advolens.vercel.app/admin/dashboard">View Full Issue →</a>
      </p>
    </div>
    <div class="ftr">AdvoLens — Civic Issue Management Platform</div>
  </div>
</body>
</html>"""


def build_status_change_email(
    issue_id: int,
    department: str,
    new_status: str,
    caption: str,
) -> str:
    """Build HTML email for a status change notification."""
    dept_label = department.replace("_", " ").title()
    status_emoji = {
        "Open": "🔴",
        "In Progress": "🟡",
        "Resolved": "✅",
        "Closed": "⬛",
    }.get(new_status, "📌")
    badge_bg = {
        "Resolved": "#dcfce7", "In Progress": "#fef3c7"
    }.get(new_status, "#fee2e2")
    badge_color = {
        "Resolved": "#166534", "In Progress": "#92400e"
    }.get(new_status, "#991b1b")

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body{{font-family:Arial,sans-serif;line-height:1.6;color:#333;margin:0;padding:0;background:#f3f4f6}}
    .wrap{{max-width:600px;margin:24px auto;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1)}}
    .hdr{{background:#2563eb;color:#fff;padding:24px 28px}}
    .hdr h2{{margin:0 0 4px 0;font-size:20px}}
    .body{{background:#fff;padding:28px}}
    .badge{{display:inline-block;padding:7px 16px;border-radius:20px;font-weight:bold;
            background:{badge_bg};color:{badge_color};font-size:15px}}
    .btn{{display:inline-block;background:#2563eb;color:#fff;padding:11px 22px;
          border-radius:6px;text-decoration:none;font-weight:bold;font-size:14px;margin-top:16px}}
    .ftr{{background:#1f2937;color:#9ca3af;text-align:center;padding:16px;font-size:12px}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hdr">
      <h2>{status_emoji} Issue #{issue_id} — Status Updated</h2>
    </div>
    <div class="body">
      <p><strong>New Status:</strong> <span class="badge">{status_emoji} {new_status}</span></p>
      <p><strong>Department:</strong> {dept_label}</p>
      <p><strong>Description:</strong> {caption or 'No description'}</p>
      <p style="text-align:center">
        <a class="btn" href="https://advolens.vercel.app/admin/dashboard">View in Dashboard →</a>
      </p>
    </div>
    <div class="ftr">AdvoLens — Civic Issue Management Platform</div>
  </div>
</body>
</html>"""
