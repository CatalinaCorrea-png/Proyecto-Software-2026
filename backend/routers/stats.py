from fastapi import APIRouter
import pandas as pd
from db.database import engine

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def get_overview():
    with engine.connect() as conn:
        missions_df = pd.read_sql(
            """SELECT id, name, status, started_at, ended_at,
                      initial_battery, final_battery, coverage_percent,
                      detections_count, cell_size_m, grid_rows, grid_cols
               FROM missions""",
            conn,
        )
        detections_df = pd.read_sql(
            """SELECT mission_id, source, timestamp,
                      position_altitude, rgb_confidence
               FROM detections""",
            conn,
        )

    def label(row):
        return row["name"] if pd.notna(row["name"]) and row["name"] else f"Misión #{int(row['id'])}"

    missions_df["label"] = missions_df.apply(label, axis=1)

    # ── 1. TTFD: tiempo hasta primera detección (minutos) ──────────────────────
    if not detections_df.empty and missions_df["started_at"].notna().any():
        first_det = (
            detections_df.groupby("mission_id")["timestamp"]
            .min()
            .reset_index()
            .rename(columns={"timestamp": "first_detection", "mission_id": "id"})
        )
        ttfd_df = (
            missions_df[missions_df["started_at"].notna()]
            .merge(first_det, on="id", how="inner")
        )
        ttfd_df["ttfd_min"] = (
            (
                pd.to_datetime(ttfd_df["first_detection"], utc=True) -
                pd.to_datetime(ttfd_df["started_at"], utc=True)
            ).dt.total_seconds() / 60
        ).round(1)
        ttfd_df = ttfd_df[ttfd_df["ttfd_min"] >= 0]
        ttfd = ttfd_df[["label", "ttfd_min"]].to_dict("records")
    else:
        ttfd = []

    # ── 2. Eficiencia de barrido (m²/min) ──────────────────────────────────────
    eff_mask = (
        missions_df["ended_at"].notna() &
        missions_df["started_at"].notna() &
        missions_df["coverage_percent"].notna() &
        missions_df["cell_size_m"].notna()
    )
    if eff_mask.any():
        eff_df = missions_df[eff_mask].copy()
        eff_df["duration_min"] = (
            pd.to_datetime(eff_df["ended_at"], utc=True) -
            pd.to_datetime(eff_df["started_at"], utc=True)
        ).dt.total_seconds() / 60
        eff_df = eff_df[eff_df["duration_min"] > 0]
        if not eff_df.empty:
            eff_df["m2_per_min"] = (
                eff_df["grid_rows"] * eff_df["grid_cols"] *
                eff_df["cell_size_m"] ** 2 *
                eff_df["coverage_percent"] / 100 /
                eff_df["duration_min"]
            ).round(0).fillna(0).astype(int)
            sweep_efficiency = eff_df[["label", "m2_per_min"]].to_dict("records")
        else:
            sweep_efficiency = []
    else:
        sweep_efficiency = []

    # ── 3. Densidad de detecciones (detecciones/km²) ───────────────────────────
    dens_mask = missions_df["coverage_percent"].notna() & missions_df["cell_size_m"].notna()
    if dens_mask.any():
        dens_df = missions_df[dens_mask].copy()
        dens_df["area_covered_km2"] = (
            dens_df["grid_rows"] * dens_df["grid_cols"] *
            dens_df["cell_size_m"] ** 2 *
            dens_df["coverage_percent"] / 100 / 1_000_000
        )
        dens_df = dens_df[dens_df["area_covered_km2"] > 0]
        dens_df["detections_per_km2"] = (
            dens_df["detections_count"] / dens_df["area_covered_km2"]
        ).round(2)
        detection_density = dens_df[["label", "detections_per_km2"]].to_dict("records")
    else:
        detection_density = []

    # ── 4. Consumo de batería por km² cubierto ─────────────────────────────────
    batt_mask = (
        missions_df["final_battery"].notna() &
        missions_df["coverage_percent"].notna() &
        missions_df["cell_size_m"].notna()
    )
    if batt_mask.any():
        batt_df = missions_df[batt_mask].copy()
        batt_df["battery_used"] = batt_df["initial_battery"] - batt_df["final_battery"]
        batt_df["area_covered_km2"] = (
            batt_df["grid_rows"] * batt_df["grid_cols"] *
            batt_df["cell_size_m"] ** 2 *
            batt_df["coverage_percent"] / 100 / 1_000_000
        )
        batt_df = batt_df[batt_df["area_covered_km2"] > 0]
        batt_df["battery_per_km2"] = (
            batt_df["battery_used"] / batt_df["area_covered_km2"]
        ).round(2)
        battery_per_km2 = batt_df[["label", "battery_per_km2"]].to_dict("records")
    else:
        battery_per_km2 = []

    # ── 5. Fuente de detección por misión (rgb / thermal / fusion) ─────────────
    if not detections_df.empty:
        src_pivot = (
            detections_df.groupby(["mission_id", "source"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
            .rename(columns={"mission_id": "id"})
        )
        for col in ["rgb", "thermal", "fusion"]:
            if col not in src_pivot.columns:
                src_pivot[col] = 0
        src_per_mission = (
            missions_df[["id", "label"]]
            .merge(src_pivot, on="id", how="inner")
            [["label", "rgb", "thermal", "fusion"]]
            .to_dict("records")
        )
    else:
        src_per_mission = []

    # ── 6. Altitud vs confianza RGB (scatter) ──────────────────────────────────
    scatter_df = detections_df[
        detections_df["rgb_confidence"].notna() &
        detections_df["position_altitude"].notna()
    ][["position_altitude", "rgb_confidence", "source"]].copy()
    scatter_df["rgb_confidence"] = scatter_df["rgb_confidence"].round(3)
    altitude_vs_confidence = scatter_df.to_dict("records")

    return {
        "ttfd_per_mission": ttfd,
        "sweep_efficiency": sweep_efficiency,
        "detection_density": detection_density,
        "battery_per_km2": battery_per_km2,
        "source_per_mission": src_per_mission,
        "altitude_vs_confidence": altitude_vs_confidence,
    }
