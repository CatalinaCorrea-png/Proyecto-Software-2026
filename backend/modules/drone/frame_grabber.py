import glob
import os
import threading
import time

import cv2
import numpy as np
import requests

from core.config import CAMERA_FLIP, CAMERA_INDEX, CAMERA_SOURCE


class FrameGrabber:
    def __init__(self):
        self._cap: cv2.VideoCapture | None = None
        self._stream_url: str | None = None
        self._frame: np.ndarray | None = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self.frame_w = 640
        self.frame_h = 480

    def start(self) -> bool:
        source, use_dshow = CAMERA_INDEX.get(CAMERA_SOURCE, (None, False))

        if source is None:
            print("📷 Modo sintético")
            return False

        if CAMERA_SOURCE == "video":
            self._running = True
            self._thread = threading.Thread(
                target=self._video_reader_loop, args=(source,), daemon=True
            )
            self._thread.start()
            print(f"✅ Video: {source}")
            return True

        if isinstance(source, str):
            self._stream_url = source
            self._running = True
            self._thread = threading.Thread(target=self._mjpeg_reader_loop, daemon=True)
            self._thread.start()
            print(f"✅ Cámara: {CAMERA_SOURCE} (url: {source}) — conectando...")
            return True

        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW if use_dshow else cv2.CAP_ANY)
        if not cap.isOpened():
            print(f"⚠️ No se pudo abrir {CAMERA_SOURCE}, usando sintético")
            return False
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0:
            cap.release()
            print(f"⚠️ No se pudo leer de {CAMERA_SOURCE}, usando sintético")
            return False
        self._cap = cap
        self._frame = frame
        self.frame_w = frame.shape[1]
        self.frame_h = frame.shape[0]
        self._running = True
        self._thread = threading.Thread(target=self._cv2_reader_loop, daemon=True)
        self._thread.start()
        print(f"✅ Cámara: {CAMERA_SOURCE} (índice: {source})")
        return True

    def _mjpeg_reader_loop(self):
        while self._running:
            resp = None
            try:
                resp = requests.get(self._stream_url, stream=True, timeout=(5, 10))
                buf = b''
                for chunk in resp.iter_content(chunk_size=4096):
                    if not self._running:
                        break
                    buf += chunk
                    while True:
                        start = buf.find(b'\xff\xd8')
                        if start == -1:
                            buf = b''
                            break
                        end = buf.find(b'\xff\xd9', start)
                        if end == -1:
                            buf = buf[start:]
                            break
                        jpg = buf[start:end + 2]
                        buf = buf[end + 2:]
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            with self._lock:
                                self._frame = frame
            except Exception as e:
                print(f"⚠️ MJPEG stream error: {e}, reconectando en 2s...")
            finally:
                if resp:
                    try:
                        resp.close()
                    except Exception:
                        pass
            time.sleep(2)

    def _cv2_reader_loop(self):
        while self._running and self._cap is not None:
            ret, frame = self._cap.read()
            if ret and frame is not None:
                with self._lock:
                    self._frame = frame

    def _video_reader_loop(self, path: str):
        """Lee videos de media/videos/ en rotación, o una URL de YouTube en loop."""
        if "youtube.com/" in path or "youtu.be/" in path:
            try:
                import yt_dlp
                ydl_opts = {"format": "best[height<=720]", "quiet": True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(path, download=False)
                    path = info["url"]
            except ImportError:
                print("yt-dlp no instalado. pip install yt-dlp")
                return
            except Exception as e:
                print(f"Error obteniendo URL de YouTube: {e}")
                return
            playlist = [path]
        else:
            video_dir = os.path.dirname(path) or "media/videos"
            exts = (".mp4", ".avi", ".mkv", ".mov", ".webm")
            playlist = sorted(
                f for f in glob.glob(os.path.join(video_dir, "*"))
                if os.path.splitext(f)[1].lower() in exts
            )
            if not playlist:
                print(f"No hay videos en {video_dir}")
                return

        idx = 0
        while self._running:
            video = playlist[idx % len(playlist)]
            cap = cv2.VideoCapture(video)
            if not cap.isOpened():
                print(f"No se pudo abrir: {video}, saltando...")
                idx += 1
                time.sleep(1)
                continue

            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            delay = 1.0 / fps
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if w and h:
                self.frame_w = w
                self.frame_h = h
            print(f"Reproduciendo: {os.path.basename(video)}")

            while self._running:
                ret, frame = cap.read()
                if not ret:
                    break
                with self._lock:
                    self._frame = frame
                time.sleep(delay)

            cap.release()
            idx += 1

    def grab(self) -> np.ndarray | None:
        with self._lock:
            if self._frame is None:
                return None
            frame = self._frame.copy()
        if CAMERA_FLIP:
            frame = cv2.flip(frame, -1)
        return frame

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
            self._cap = None


_instance: FrameGrabber | None = None


def get_grabber() -> FrameGrabber:
    global _instance
    if _instance is None:
        _instance = FrameGrabber()
        _instance.start()
    return _instance


def stop_grabber() -> None:
    global _instance
    if _instance is not None:
        _instance.stop()
        _instance = None
