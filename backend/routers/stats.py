from fastapi import APIRouter
import pandas as pd
from db.database import engine

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def get_overview():
    with engine.connect() as conn:
        missions_df = pd.read_sql(
            "SELECT id, name, detections_count, coverage_percent, status FROM missions",
            conn,
        )
        detections_df = pd.read_sql(
            "SELECT mission_id, confidence, source, timestamp FROM detections", conn
        )

    # Detections per mission — use actual count from detections table per mission
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
        det_per_mission["count"] = missions_df["detections_count"].fillna(0).astype(int)

    # Confidence distribution across all detections
    if not detections_df.empty:
        conf_dist = detections_df["confidence"].value_counts().to_dict()
    else:
        conf_dist = {"high": 0, "medium": 0, "low": 0}

    # Source distribution (rgb / thermal / fusion)
    if not detections_df.empty:
        source_dist = detections_df["source"].value_counts().to_dict()
    else:
        source_dist = {}

    # Detections over time — grouped by day
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

    # Coverage per mission — only completed missions with coverage data
    coverage_df = missions_df[missions_df["coverage_percent"].notna()][
        ["id", "name", "coverage_percent"]
    ].copy()
    coverage_df["coverage_percent"] = coverage_df["coverage_percent"].round(1)

    def label(row):
        return row["name"] if pd.notna(row["name"]) and row["name"] else f"Misión #{row['id']}"

    det_per_mission["label"] = det_per_mission.apply(label, axis=1)
    coverage_df["label"] = coverage_df.apply(label, axis=1)

    return {
        "detections_per_mission": det_per_mission[["id", "label", "count"]].to_dict("records"),
        "confidence_distribution": [
            {"name": k, "value": v} for k, v in conf_dist.items()
        ],
        "source_distribution": [
            {"name": k, "value": v} for k, v in source_dist.items()
        ],
        "coverage_per_mission": coverage_df[["id", "label", "coverage_percent"]].to_dict("records"),
        "detections_timeline": detections_timeline,
    }
