from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from app.api.endpoints import router, ROADException
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for ROADSense project",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(ROADException)
async def road_exception_handler(request: Request, exc: ROADException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )

app.include_router(router, prefix=settings.API_V1_STR)

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            if not event:
                await websocket.send_json({"error": "missing event type"})
            elif event == "ping":
                await websocket.send_json({"event": "pong"})
            else:
                await websocket.send_json({"error": f"unknown event: {event}"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": "invalid payload"})
            await websocket.close()
        except:
            pass

@app.on_event("startup")
def startup_event():
    # Pre-load data on startup
    from app.data.repository import repository
    repository.load_data()
