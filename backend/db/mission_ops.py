from datetime import datetime, timezone

import core.mission_state as ms
import core.state as state
from core.state import drone_state
from db.database import SessionLocal
from db.models import Detection as DetectionModel, GridCell as GridCellModel, Mission as MissionModel


def close_orphan_missions() -> None:
    db = SessionLocal()
    try:
        orphans = db.query(MissionModel).filter(MissionModel.status == "active").all()
        for m in orphans:
            m.status = "aborted"
            m.ended_at = datetime.now(timezone.utc)
            m.detections_count = len(m.detections)
        if orphans:
            db.commit()
            print(f"⚠️  {len(orphans)} misión(es) huérfana(s) marcadas como 'aborted'")
    finally:
        db.close()


def close_mission_db() -> None:
    if not ms.active_mission_id:
        return
    db = SessionLocal()
    try:
        m = db.query(MissionModel).filter(MissionModel.id == ms.active_mission_id).first()
        if m:
            m.ended_at = datetime.now(timezone.utc)
            m.status = "completed"
            m.final_battery = round(drone_state.battery, 1)
            m.coverage_percent = state.search_grid.coverage_percent()
            m.detections_count = db.query(DetectionModel).filter(
                DetectionModel.mission_id == ms.active_mission_id
            ).count()
            for cell in state.search_grid.cells.values():
                if cell["status"] != "unexplored":
                    db.add(GridCellModel(
                        mission_id=ms.active_mission_id,
                        row=cell["row"],
                        col=cell["col"],
                        cell_lat=cell["lat"],
                        cell_lng=cell["lng"],
                        status=cell["status"],
                        explored_at=datetime.fromtimestamp(
                            cell["explored_at"] / 1000, tz=timezone.utc
                        ) if cell["explored_at"] else None,
                    ))
            db.commit()
    except Exception as e:
        print(f"DB error closing mission: {e}")
        db.rollback()
    finally:
        db.close()
    ms.active_mission_id = None
