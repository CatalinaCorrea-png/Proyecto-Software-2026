import math
import time

CELL_SIZE_METERS = 20
METERS_PER_LAT_DEGREE = 111_000

def cell_degrees(cell_size_m: float, lat: float):
    cell_lat = cell_size_m / METERS_PER_LAT_DEGREE
    cell_lng = cell_size_m / (METERS_PER_LAT_DEGREE * math.cos(math.radians(lat)))
    return cell_lat, cell_lng

CELL_LAT, CELL_LNG = cell_degrees(CELL_SIZE_METERS, -32.65)

class SearchGrid:
    def __init__(self, center_lat: float, center_lng: float,
                 rows: int = 15, cols: int = 20,
                 cell_size_m: float = CELL_SIZE_METERS):
        self.rows = rows
        self.cols = cols
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.cell_size_m = cell_size_m
        self.cell_lat, self.cell_lng = cell_degrees(cell_size_m, center_lat)

        self.origin_lat = center_lat + (rows / 2) * self.cell_lat
        self.origin_lng = center_lng - (cols / 2) * self.cell_lng

        self.cells: dict[tuple[int,int], dict] = {}
        self._init_cells()

    def _init_cells(self):
        for r in range(self.rows):
            for c in range(self.cols):
                lat = self.origin_lat - r * self.cell_lat
                lng = self.origin_lng + c * self.cell_lng
                self.cells[(r, c)] = {
                    "row": r,
                    "col": c,
                    "lat": lat,
                    "lng": lng,
                    "status": "unexplored",
                    "explored_at": None
                }

    def update_position(self, lat: float, lng: float) -> list[dict]:
        row, col = self._lat_lng_to_cell(lat, lng)

        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return []

        cell = self.cells[(row, col)]
        if cell["status"] == "unexplored":
            cell["status"] = "explored"
            cell["explored_at"] = int(time.time() * 1000)
            return [cell]

        return []

    def mark_detection(self, lat: float, lng: float) -> dict | None:
        row, col = self._lat_lng_to_cell(lat, lng)
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return None
        cell = self.cells[(row, col)]
        cell["status"] = "detection"
        return cell

    def _lat_lng_to_cell(self, lat: float, lng: float) -> tuple[int, int]:
        row = int((self.origin_lat - lat) / self.cell_lat)
        col = int((lng - self.origin_lng) / self.cell_lng)
        return row, col

    def get_all_cells(self) -> list[dict]:
        return list(self.cells.values())

    def coverage_percent(self) -> float:
        explored = sum(1 for c in self.cells.values() if c["status"] != "unexplored")
        return round((explored / len(self.cells)) * 100, 1)
