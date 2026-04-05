import time
from collections import deque # double-ended queue (Stacks (LIFO) or Queues (FIFO))
from dataclasses import dataclass, field

@dataclass
class PerformanceMetrics:
    # FPS
    _frame_times: deque = field(default_factory=lambda: deque(maxlen=30))
    
    # Tiempos de procesamiento por etapa (ms)
    _yolo_times: deque = field(default_factory=lambda: deque(maxlen=30))
    _thermal_times: deque = field(default_factory=lambda: deque(maxlen=30))
    _fusion_times: deque = field(default_factory=lambda: deque(maxlen=30))
    _encode_times: deque = field(default_factory=lambda: deque(maxlen=30))
    _total_times: deque = field(default_factory=lambda: deque(maxlen=30))
    
    # Detecciones
    detections_total: int = 0
    detections_high: int = 0
    frames_processed: int = 0

    def record_frame(self):
        """Llamar al inicio de cada frame"""
        self._frame_times.append(time.time())

    def record_yolo(self, ms: float):
        self._yolo_times.append(ms)

    def record_thermal(self, ms: float):
        self._thermal_times.append(ms)

    def record_fusion(self, ms: float):
        self._fusion_times.append(ms)

    def record_encode(self, ms: float):
        self._encode_times.append(ms)

    def record_total(self, ms: float):
        self._total_times.append(ms)
        self.frames_processed += 1

    def record_detection(self, confidence: str):
        self.detections_total += 1
        if confidence == 'high':
            self.detections_high += 1

    @property
    def fps(self) -> float:
        if len(self._frame_times) < 2:
            return 0.0
        times = list(self._frame_times)
        elapsed = times[-1] - times[0]
        return round(len(times) / elapsed, 1) if elapsed > 0 else 0.0

    def _avg(self, dq: deque) -> float:
        return round(sum(dq) / len(dq), 1) if dq else 0.0

    def snapshot(self) -> dict:
        return {
            "fps": self.fps,
            "processing": {
                "yolo_ms":    self._avg(self._yolo_times),
                "thermal_ms": self._avg(self._thermal_times),
                "fusion_ms":  self._avg(self._fusion_times),
                "encode_ms":  self._avg(self._encode_times),
                "total_ms":   self._avg(self._total_times),
            },
            "detections": {
                "total":      self.detections_total,
                "high":       self.detections_high,
                "frames":     self.frames_processed,
                "rate": round(
                    self.detections_total / self.frames_processed * 100, 1
                ) if self.frames_processed > 0 else 0.0
            }
        }

# Instancia global
metrics = PerformanceMetrics()