from fastapi import APIRouter, Depends
import pandas as pd
from db.database import engine
from routers.auth import get_current_user
from db.models import User

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def get_overview(user: User = Depends(get_current_user)):
    uid = user.id
    with engine.connect() as conn:
        missions_df = pd.read_sql(
            "SELECT id, name, detections_count, coverage_percent, status FROM missions WHERE user_id = :uid",
            conn,
            params={"uid": uid},
        )
        detections_df = pd.read_sql(
            """SELECT d.mission_id, d.confidence, d.source, d.timestamp
               FROM detections d
               JOIN missions m ON d.mission_id = m.id
               WHERE m.user_id = :uid""",
            conn,
            params={"uid": uid},
        )

    if not detections_df.empty:
        det_counts = (
            detections_df.groupby("mission_id")
            .size()
            .reset_index(name="count")
            .rename(columns={"mission_id": "id"})
        )
        det_per_mission = missions_df[["id", "name"]].merge(det_counts, on="id", how="left")
        det_per_mission["count"] = det_per_mission["count"].fillna(0).astype(int)
    else:
        det_per_mission = missions_df[["id", "name"]].copy()
        det_per_mission["count"] = missions_df["detections_count"].fillna(0).astype(int) if not missions_df.empty else []

    if not detections_df.empty:
        conf_dist = detections_df["confidence"].value_counts().to_dict()
    else:
        conf_dist = {"high": 0, "medium": 0, "low": 0}

    if not detections_df.empty:
        source_dist = detections_df["source"].value_counts().to_dict()
    else:
        source_dist = {}

    if not detections_df.empty:
        detections_df["date"] = pd.to_datetime(detections_df["timestamp"]).dt.date
        timeline = (
            detections_df.groupby("date")
            .size()
            .reset_index(name="count")
            .sort_values("date")
        )
        timeline["date"] = timeline["date"].astype(str)
        detections_timeline = timeline.to_dict("records")
    else:
        detections_timeline = []

    coverage_df = missions_df[missions_df["coverage_percent"].notna()][
        ["id", "name", "coverage_percent"]
    ].copy() if not missions_df.empty else pd.DataFrame(columns=["id", "name", "coverage_percent"])
    if not coverage_df.empty:
        coverage_df["coverage_percent"] = coverage_df["coverage_percent"].round(1)

    def label(row):
        return row["name"] if pd.notna(row["name"]) and row["name"] else f"Misión #{row['id']}"

    if not det_per_mission.empty:
        det_per_mission["label"] = det_per_mission.apply(label, axis=1)
    if not coverage_df.empty:
        coverage_df["label"] = coverage_df.apply(label, axis=1)

    return {
        "detections_per_mission": det_per_mission[["id", "label", "count"]].to_dict("records") if not det_per_mission.empty else [],
        "confidence_distribution": [{"name": k, "value": v} for k, v in conf_dist.items()],
        "source_distribution": [{"name": k, "value": v} for k, v in source_dist.items()],
        "coverage_per_mission": coverage_df[["id", "label", "coverage_percent"]].to_dict("records") if not coverage_df.empty else [],
        "detections_timeline": detections_timeline,
    }
