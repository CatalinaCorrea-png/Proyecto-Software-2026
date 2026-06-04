import pytest
from modules.mapping.grid import SearchGrid, cell_degrees


# ─── cell_degrees ────────────────────────────────────────────────────────────

# Verifica que cell_degrees devuelva valores positivos para cualquier
# tamaño de celda y latitud válidos
def test_cell_degrees_returns_positive_values():
    cell_lat, cell_lng = cell_degrees(20.0, -33.0)
    assert cell_lat > 0
    assert cell_lng > 0


# Verifica que en latitudes medias (fuera del ecuador) se necesiten más grados
# de longitud que de latitud para cubrir la misma distancia en metros,
# ya que los meridianos convergen hacia los polos
def test_cell_degrees_lng_greater_than_lat_at_midlatitude():
    cell_lat, cell_lng = cell_degrees(20.0, -33.0)
    assert cell_lng > cell_lat


# ─── SearchGrid — construcción ───────────────────────────────────────────────

# Verifica que el grid genere exactamente rows × cols celdas
def test_grid_has_correct_cell_count():
    grid = SearchGrid(-33.0, -71.0, rows=5, cols=8)
    assert len(grid.cells) == 5 * 8


# Verifica que los atributos rows y cols del grid coincidan
# con los parámetros pasados al constructor
def test_grid_stores_rows_and_cols():
    grid = SearchGrid(-33.0, -71.0, rows=5, cols=8)
    assert grid.rows == 5
    assert grid.cols == 8


# Verifica que el centro del grid almacene exactamente las coordenadas
# pasadas al constructor
def test_grid_center_matches_params():
    grid = SearchGrid(-33.0, -71.0, rows=5, cols=8)
    assert grid.center_lat == -33.0
    assert grid.center_lng == -71.0


# Verifica que todas las celdas comiencen en estado "unexplored"
# antes de que el drone haya sobrevolado la zona
def test_all_cells_start_unexplored():
    grid = SearchGrid(-33.0, -71.0, rows=3, cols=3)
    for cell in grid.cells.values():
        assert cell["status"] == "unexplored"


# Verifica que la cobertura inicial sea 0.0% ya que ninguna celda fue explorada
def test_coverage_percent_zero_initially():
    grid = SearchGrid(-33.0, -71.0, rows=4, cols=4)
    assert grid.coverage_percent() == 0.0


# ─── update_position ────────────────────────────────────────────────────────

# Verifica que sobrevolar el centro del grid marque esa celda como "explored"
# y que update_position retorne la celda actualizada
def test_update_position_marks_center_cell_explored():
    grid = SearchGrid(-33.0, -71.0, rows=10, cols=10, cell_size_m=100.0)
    updates = grid.update_position(grid.center_lat, grid.center_lng)
    assert len(updates) == 1
    assert updates[0]["status"] == "explored"


# Verifica que pasar coordenadas completamente fuera del grid
# retorne lista vacía sin modificar el estado
def test_update_position_outside_grid_returns_empty():
    grid = SearchGrid(-33.0, -71.0, rows=5, cols=5, cell_size_m=20.0)
    updates = grid.update_position(0.0, 0.0)  # muy lejos del grid
    assert updates == []


# Verifica que sobrevolar una celda ya explorada no genere una segunda
# actualización — el drone ya cubrió esa zona
def test_update_position_same_cell_twice_returns_empty_second_time():
    grid = SearchGrid(-33.0, -71.0, rows=10, cols=10, cell_size_m=100.0)
    first = grid.update_position(grid.center_lat, grid.center_lng)
    second = grid.update_position(grid.center_lat, grid.center_lng)
    assert len(first) == 1
    assert len(second) == 0


# ─── mark_detection ─────────────────────────────────────────────────────────

# Verifica que marcar una detección en una coordenada válida cambie
# el estado de la celda a "detection"
def test_mark_detection_sets_status_to_detection():
    grid = SearchGrid(-33.0, -71.0, rows=10, cols=10, cell_size_m=100.0)
    cell = grid.mark_detection(grid.center_lat, grid.center_lng)
    assert cell is not None
    assert cell["status"] == "detection"


# Verifica que mark_detection en coordenadas fuera del grid retorne None
# sin lanzar excepción
def test_mark_detection_outside_grid_returns_none():
    grid = SearchGrid(-33.0, -71.0, rows=5, cols=5, cell_size_m=20.0)
    result = grid.mark_detection(0.0, 0.0)
    assert result is None


# ─── coverage_percent ───────────────────────────────────────────────────────

# Verifica que la cobertura aumente tras explorar al menos una celda
def test_coverage_percent_increases_after_exploring_one_cell():
    grid = SearchGrid(-33.0, -71.0, rows=10, cols=10, cell_size_m=100.0)
    grid.update_position(grid.center_lat, grid.center_lng)
    assert grid.coverage_percent() > 0.0


# Verifica que las celdas marcadas como "detection" también cuenten
# en el porcentaje de cobertura (no son "unexplored")
def test_coverage_counts_detection_cells():
    grid = SearchGrid(-33.0, -71.0, rows=10, cols=10, cell_size_m=100.0)
    grid.mark_detection(grid.center_lat, grid.center_lng)
    assert grid.coverage_percent() > 0.0
