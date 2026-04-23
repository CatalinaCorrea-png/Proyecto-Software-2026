import cv2
from core.config import CAMERA_SOURCE, CAMERA_INDEX

def open_camera() -> cv2.VideoCapture | None:
    source, use_dshow = CAMERA_INDEX.get(CAMERA_SOURCE, (None, False))
    
    if source is None:
        print("📷 Modo sintético")
        return None
    
    # String = URL / int = index de camara local
    if isinstance(source, str):
        cap = cv2.VideoCapture(source) # sin CAP_DSHOW para URLs
    else:
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW if use_dshow else cv2.CAP_ANY)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            print(f"✅ Cámara: {CAMERA_SOURCE} (índice o url: {source})")
            return cap
        cap.release()

    print(f"⚠️ No se pudo abrir {CAMERA_SOURCE}, usando sintético")
    return None
