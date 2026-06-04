import asyncio
import json
import math
import time

import core.mission_state as ms
import core.state as state
from core.state import drone_state
from db.mission_ops import close_mission_db


def _snap_step_to_position(spc: int, cols: int, steps_per_cycle: int) -> int:
    grid = state.search_grid
    south_lat = grid.origin_lat - (grid.rows - 0.5) * grid.cell_lat
    row_f = (drone_state.lat - south_lat) / grid.cell_lat
    row = max(0, round(row_f))

    if row % 2 == 0:
        col_f = (drone_state.lng - grid.origin_lng) / grid.cell_lng - 0.5
    else:
        col_f = (cols - 0.5) - (drone_state.lng - grid.origin_lng) / grid.cell_lng

    col_f = max(0.0, min(col_f, cols - 1.0))
    pos_h = min(int(col_f * spc), (cols - 1) * spc - 1)
    return row * steps_per_cycle + max(0, pos_h)


async def run_simulation() -> None:
    grid = state.search_grid
    spc = int(grid.cell_size_m / 5.0)
    cols = grid.cols
    steps_horizontal = (cols - 1) * spc
    steps_vertical = spc
    steps_per_cycle = steps_horizontal + steps_vertical

    origin_lat = grid.origin_lat
    origin_lng = grid.origin_lng

    drone_state.mission_active = True
    was_manual = False

    while drone_state.mission_active:
        elapsed = int(time.time() - drone_state.mission_start)

        if drone_state.battery <= 0:
            drone_state.status = "landed"
            drone_state.mission_active = False
            close_mission_db()
            return

        if drone_state.real_telemetry_active:
            source = "hardware"
            current_speed = 5.0
            was_manual = True
        elif drone_state.cmd_throttle > 0:
            thrust = drone_state.cmd_throttle / 255.0
            pitch_norm = drone_state.cmd_pitch / 100.0
            roll_norm = drone_state.cmd_roll / 100.0

            speed_mps = thrust * 10.0
            drone_state.lat += (speed_mps * pitch_norm) / 111_000
            cos_lat = max(math.cos(math.radians(drone_state.lat)), 0.01)
            drone_state.lng += (speed_mps * roll_norm) / (111_000 * cos_lat)

            magnitude = min(math.sqrt(pitch_norm**2 + roll_norm**2), 1.0)
            source = "manual"
            current_speed = round(speed_mps * magnitude, 1)
            was_manual = True
        else:
            source = "sim"
            if was_manual:
                drone_state.sim_step = _snap_step_to_position(spc, cols, steps_per_cycle)
                was_manual = False

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
            current_speed = 0.0 if drone_state.sim_direction == 0 else 5.0

        drone_state.battery = max(0, drone_state.battery - 0.05)
        if drone_state.sim_direction == 0 and not drone_state.real_telemetry_active and drone_state.cmd_throttle == 0:
            drone_state.status = "hover"
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
            },
        }

        await asyncio.sleep(1)
