import math
import time

# 20 metros en grados decimales (aproximado, válido para latitudes medias)
CELL_SIZE_METERS = 20
METERS_PER_LAT_DEGREE = 111_000
 # ajustado para Buenos Aires
# METERS_PER_LNG_DEGREE = 111_000 * math.cos(math.radians(-34.6)) 
# dinámico según la latitud real
METERS_PER_LNG_DEGREE = 111_000 * math.cos(math.radians(-32.6))  # Aconcagua

CELL_LAT = CELL_SIZE_METERS / METERS_PER_LAT_DEGREE
CELL_LNG = CELL_SIZE_METERS / METERS_PER_LNG_DEGREE

class SearchGrid:
    def __init__(self, center_lat: float, center_lng: float, rows: int = 15, cols: int = 20):
        """
        Crea una grilla centrada en un punto.
        Por defecto 15x20 celdas = área de 300x400 metros
        """
        self.rows = rows
        self.cols = cols
        self.center_lat = center_lat
        self.center_lng = center_lng

        # Esquina superior izquierda
        self.origin_lat = center_lat + (rows / 2) * CELL_LAT
        self.origin_lng = center_lng - (cols / 2) * CELL_LNG

        # Estado de cada celda: None = sin explorar, timestamp = cuándo fue explorada
        self.cells: dict[tuple[int,int], dict] = {}
        self._init_cells()

    def _init_cells(self):
        for r in range(self.rows):
            for c in range(self.cols):
                lat = self.origin_lat - r * CELL_LAT  # ← decrece hacia el sur
                lng = self.origin_lng + c * CELL_LNG  # ← crece hacia el este
                self.cells[(r, c)] = {
                    "row": r,
                    "col": c,
                    "lat": lat,
                    "lng": lng,
                    "status": "unexplored",
                    "explored_at": None
                }

    def update_position(self, lat: float, lng: float) -> list[dict]:
        """
        Recibe posición GPS del drone.
        Marca la celda correspondiente como explorada.
        Retorna lista de celdas que cambiaron (para enviar al frontend).
        """
        row, col = self._lat_lng_to_cell(lat, lng)

        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return []  # fuera de la grilla

        cell = self.cells[(row, col)]
        if cell["status"] == "unexplored":
            cell["status"] = "explored"
            cell["explored_at"] = int(time.time() * 1000)
            return [cell]  # solo retorna si hubo cambio

        return []

    def mark_detection(self, lat: float, lng: float) -> dict | None:
        """Marca una celda como que tuvo una detección"""
        row, col = self._lat_lng_to_cell(lat, lng)
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return None
        cell = self.cells[(row, col)]
        cell["status"] = "detection"
        return cell

    def _lat_lng_to_cell(self, lat: float, lng: float) -> tuple[int, int]:
        row = int((self.origin_lat - lat) / CELL_LAT)
        col = int((lng - self.origin_lng) / CELL_LNG)
        return row, col

    def get_all_cells(self) -> list[dict]:
        return list(self.cells.values())

    def coverage_percent(self) -> float:
        explored = sum(1 for c in self.cells.values() if c["status"] != "unexplored")
        return round((explored / len(self.cells)) * 100, 1)