from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from modules.drone.simulator import simulate_telemetry
import json

app = FastAPI(title="AeroSearch AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "AeroSearch AI online"}

@app.websocket("/ws/mission")
async def mission_websocket(websocket: WebSocket):
    await websocket.accept()  # ← acepta la conexión del cliente
    print("🔌 Cliente conectado")
    try:
        async for message in simulate_telemetry():  # ← consume el generador
            await websocket.send_text(json.dumps(message)) # ← manda cada mensaje
    except WebSocketDisconnect:
        print("❌ Cliente desconectado") # ← si el cliente cierra, limpia