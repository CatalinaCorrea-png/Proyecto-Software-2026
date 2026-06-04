import pytest


# Verifica que reset_mission actualice correctamente la posición GPS
# y la altitud del drone según los parámetros recibidos
def test_reset_mission_updates_position():
    from core.state import drone_state, reset_mission
    reset_mission(lat=-33.5, lng=-71.2, altitude=30.0, rows=10, cols=10, cell_size_m=15.0)
    assert drone_state.lat == -33.5
    assert drone_state.lng == -71.2
    assert drone_state.altitude == 30.0


# Verifica que reset_mission restaure la batería al 100% y el estado a "idle",
# independientemente de los valores que tenía antes de la llamada
def test_reset_mission_restores_battery_and_status():
    from core.state import drone_state, reset_mission
    drone_state.battery = 45.0
    drone_state.status = "flying"
    reset_mission(lat=-33.0, lng=-71.0, altitude=25.0, rows=10, cols=10, cell_size_m=20.0)
    assert drone_state.battery == 100.0
    assert drone_state.status == "idle"


# Verifica que reset_mission limpie todos los contadores de simulación
# (pasos, dirección, comandos de control) y desactive la misión en curso
def test_reset_mission_clears_sim_state():
    from core.state import drone_state, reset_mission
    drone_state.mission_active = True
    drone_state.sim_step = 99
    drone_state.sim_direction = -1
    drone_state.cmd_throttle = 500
    drone_state.cmd_pitch = 100
    drone_state.cmd_roll = -100
    reset_mission(lat=-33.0, lng=-71.0, altitude=25.0, rows=10, cols=10, cell_size_m=20.0)
    assert drone_state.mission_active == False
    assert drone_state.sim_step == 0
    assert drone_state.sim_direction == 1
    assert drone_state.cmd_throttle == 0
    assert drone_state.cmd_pitch == 0
    assert drone_state.cmd_roll == 0


# Verifica que reset_mission retorne un SearchGrid con las dimensiones
# exactas que se pasaron como parámetros (filas y columnas)
def test_reset_mission_returns_grid_with_correct_dimensions():
    from core.state import reset_mission
    grid = reset_mission(lat=-33.0, lng=-71.0, altitude=20.0, rows=5, cols=8, cell_size_m=10.0)
    assert grid.rows == 5
    assert grid.cols == 8


# Verifica que un DroneState recién instanciado tenga los valores por defecto esperados:
# batería llena, estado idle, misión inactiva y contadores en cero
def test_drone_state_default_values():
    from core.state import DroneState
    state = DroneState()
    assert state.battery == 100.0
    assert state.status == "idle"
    assert state.mission_active == False
    assert state.real_telemetry_active == False
    assert state.sim_step == 0
    assert state.sim_direction == 1
