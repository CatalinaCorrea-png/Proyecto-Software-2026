import asyncio
import json
import math
import time

import core.config as config
import core.mission_state as ms
import core.state as state
from core.state import drone_state
from db.mission_ops import close_mission_db

REVISIT_SPEED_MPS = 8.0  # tránsito hacia un punto de la cola (más rápido que el barrido)


def _step_toward(target_lat: float, target_lng: float, speed_mps: float) -> bool:
    """Acerca al dron al objetivo a `speed_mps` por tick. Devuelve True al llegar."""
    dlat_m = (target_lat - drone_state.lat) * 111_000
    cos_lat = max(math.cos(math.radians(drone_state.lat)), 0.01)
    dlng_m = (target_lng - drone_state.lng) * 111_000 * cos_lat
    dist = math.hypot(dlat_m, dlng_m)
    if dist <= speed_mps:
        drone_state.lat = target_lat
        drone_state.lng = target_lng
        return True
    drone_state.lat += (dlat_m / dist) * speed_mps / 111_000
    drone_state.lng += (dlng_m / dist) * speed_mps / (111_000 * cos_lat)
    return False


async def run_simulation() -> None:
    grid = state.search_grid
    spc = int(grid.cell_size_m / 5.0)
    cols = grid.cols
    steps_horizontal = (cols - 1) * spc
    steps_vertical = spc
    steps_per_cycle = steps_horizontal + steps_vertical
    total_sweep_steps = grid.rows * steps_per_cycle  # barrido completo de la grilla

    origin_lat = grid.origin_lat
    origin_lng = grid.origin_lng

    drone_state.mission_active = True
    drone_state.sweep_state = "sweeping"

    while drone_state.mission_active:
        elapsed = int(time.time() - drone_state.mission_start)

        if drone_state.battery <= 0:
            drone_state.status = "landed"
            drone_state.sweep_state = "idle"
            drone_state.mission_active = False
            close_mission_db()
            return

        if drone_state.real_telemetry_active:
            # Hardware real: solo leemos la telemetría que llega del dron;
            # el backend no comanda la ruta (diferido).
            source = "hardware"
            current_speed = 5.0
        else:
            source = "sim"

            # Auto-reanudación: si el operador no resuelve a tiempo, seguimos
            # solos para no drenar batería ni colgar la misión.
            holding = drone_state.sweep_state in ("awaiting_confirmation", "revisit_confirm")
            if (
                holding
                and config.DETECTION_HOLD_TIMEOUT_S > 0
                and time.time() - drone_state.pending_since >= config.DETECTION_HOLD_TIMEOUT_S
            ):
                if drone_state.sweep_state == "awaiting_confirmation":
                    # Retomar la fase interrumpida (Opción B).
                    drone_state.sweep_state = drone_state.resume_state or "sweeping"
                else:  # revisit_confirm → seguir con el próximo punto
                    drone_state.revisit_target = None
                    drone_state.sweep_state = "revisiting"
                drone_state.pending_detection = None

            if drone_state.sweep_state == "sweeping" and not drone_state.sweep_paused:
                if drone_state.sim_step >= total_sweep_steps:
                    # Barrido completo: revisitar si quedan puntos, si no volver a base.
                    drone_state.sweep_state = "revisiting" if drone_state.revisit_queue else "returning_home"
                    current_speed = 0.0
                else:
                    step = drone_state.sim_step
                    row = step // steps_per_cycle
                    pos_in_cycle = step % steps_per_cycle
                    grid_row = grid.rows - 1 - row

                    if pos_in_cycle < steps_horizontal:
                        frac = pos_in_cycle / spc
                        lat = origin_lat - (grid_row + 0.5) * grid.cell_lat
                        if row % 2 == 0:
                            lng = origin_lng + (0.5 + frac) * grid.cell_lng
                        else:
                            lng = origin_lng + (cols - 0.5 - frac) * grid.cell_lng
                    else:
                        v_frac = (pos_in_cycle - steps_horizontal + 1) / spc
                        lat = origin_lat - (grid_row + 0.5 - v_frac) * grid.cell_lat
                        if row % 2 == 0:
                            lng = origin_lng + (cols - 0.5) * grid.cell_lng
                        else:
                            lng = origin_lng + 0.5 * grid.cell_lng

                    drone_state.lat = lat
                    drone_state.lng = lng
                    drone_state.sim_step = max(0, drone_state.sim_step + drone_state.sim_direction)
                    current_speed = 5.0

            elif drone_state.sweep_state == "revisiting" and not drone_state.sweep_paused:
                if drone_state.revisit_target is None:
                    if drone_state.revisit_queue:
                        drone_state.revisit_target = drone_state.revisit_queue.pop(0)
                    else:
                        # Cola drenada: volver al punto de despegue.
                        drone_state.sweep_state = "returning_home"

                target = drone_state.revisit_target
                if target is not None:
                    arrived = _step_toward(
                        target["position"]["lat"], target["position"]["lng"], REVISIT_SPEED_MPS
                    )
                    current_speed = REVISIT_SPEED_MPS
                    if arrived:
                        # Llegamos al punto: hover y pedimos confirmación al operador.
                        drone_state.sweep_state = "revisit_confirm"
                        drone_state.pending_detection = target
                        drone_state.pending_since = time.time()
                        current_speed = 0.0
                else:
                    current_speed = 0.0

            elif drone_state.sweep_state == "returning_home" and not drone_state.sweep_paused:
                arrived = _step_toward(drone_state.home_lat, drone_state.home_lng, REVISIT_SPEED_MPS)
                current_speed = REVISIT_SPEED_MPS
                if arrived:
                    # En base: misión completa, lista para recoger el dron.
                    drone_state.sweep_state = "completed"
                    current_speed = 0.0

            else:
                # Congelado: awaiting_confirmation, revisit_confirm, pausa,
                # completed o idle.
                current_speed = 0.0

        drone_state.battery = max(0, drone_state.battery - 0.05)

        if drone_state.real_telemetry_active:
            drone_state.status = "flying"
        elif drone_state.sweep_state in ("awaiting_confirmation", "revisit_confirm") or drone_state.sweep_paused:
            drone_state.status = "hover"
        elif drone_state.sweep_state in ("revisiting", "returning_home"):
            drone_state.status = "returning"
        elif drone_state.sweep_state == "completed":
            drone_state.status = "idle"
        else:
            drone_state.status = "flying"
        drone_state.last_update = time.time()

        changed_cells = state.search_grid.update_position(drone_state.lat, drone_state.lng)
        if changed_cells and ms.grid_clients:
            grid_update = {
                "type": "grid_update",
                "cells": changed_cells,
                "coverage": state.search_grid.coverage_percent(),
            }
            for client in ms.grid_clients.copy():
                try:
                    await client.send_text(json.dumps(grid_update))
                except Exception:
                    ms.grid_clients.remove(client)

        drone_state._last_telemetry = {
            "type": "telemetry",
            "data": {
                "position": {
                    "lat": drone_state.lat,
                    "lng": drone_state.lng,
                    "altitude": drone_state.altitude,
                    "timestamp": int(time.time() * 1000),
                },
                "battery": round(drone_state.battery, 1),
                "status": drone_state.status,
                "speed": current_speed,
                "elapsed": elapsed,
                "source": source,
                "sweep_state": drone_state.sweep_state,
                "paused": drone_state.sweep_paused,
                "pending_detection": drone_state.pending_detection,
                "revisit_queue": drone_state.revisit_queue,
            },
        }

        await asyncio.sleep(1)
