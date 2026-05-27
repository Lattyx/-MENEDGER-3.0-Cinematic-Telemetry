import asyncio
import json
import logging
import threading
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import webview
from system_monitor import SystemMonitor

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("MenedgerServer")

app = FastAPI(
    title="Menedger System Monitor API",
    description="Backend API serving real-time system performance stats over WebSockets.",
    version="1.1.0"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the resource engine
monitor = SystemMonitor()

class KillProcessRequest(BaseModel):
    pid: int

# Direct root requests to static frontend
@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/static/index.html")

# System specs endpoint
@app.get("/api/system-info")
async def get_system_info():
    try:
        return monitor.static_info
    except Exception as e:
        logger.error(f"Error fetching system static info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load system specs: {str(e)}"
        )

# Realtime process list endpoint
@app.get("/api/processes")
async def get_processes():
    try:
        return monitor.get_process_list()
    except Exception as e:
        logger.error(f"Error fetching processes list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch processes: {str(e)}"
        )

# Process termination endpoint
@app.post("/api/processes/kill")
async def kill_process(req: KillProcessRequest):
    success, msg = monitor.terminate_process(req.pid)
    if not success:
        logger.warning(f"Process termination failed: {msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    logger.info(f"Process terminated successfully: {req.pid}")
    return {"status": "success", "message": msg}

# ==========================================================================
# UTILITY OPTIMIZATION REST ENDPOINTS (PORTFOLIO GEMS)
# ==========================================================================

@app.post("/api/actions/flush-dns")
async def flush_dns():
    """Triggers Windows ipconfig /flushdns action."""
    success, msg = monitor.flush_dns_cache()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg
        )
    return {"status": "success", "message": msg}

@app.post("/api/actions/clear-temp")
async def clear_temp():
    """Safely cleans up temporary cache files in local TEMP folders."""
    success, msg, reclaimed_mb = monitor.clear_local_temp_files()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg
        )
    return {"status": "success", "message": msg, "reclaimed_mb": reclaimed_mb}

# Active WebSocket connections list to handle clean broadcasting
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Active channels: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Active channels: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    update_interval = 1.0
    disconnect_event = asyncio.Event()
    
    async def listen_client():
        nonlocal update_interval
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    payload = json.loads(data)
                    if "interval" in payload:
                        new_interval = float(payload["interval"])
                        if 0.5 <= new_interval <= 10.0:
                            update_interval = new_interval
                            logger.info(f"Updated WebSocket polling interval to {update_interval}s")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Received malformed WS message: {e}")
        except WebSocketDisconnect:
            disconnect_event.set()
        except Exception as e:
            logger.error(f"Error in client listener: {e}")
            disconnect_event.set()

    async def send_metrics():
        try:
            while not disconnect_event.is_set():
                metrics = monitor.get_realtime_metrics()
                await websocket.send_json(metrics)
                try:
                    await asyncio.wait_for(disconnect_event.wait(), timeout=update_interval)
                except asyncio.TimeoutError:
                    pass
        except WebSocketDisconnect:
            disconnect_event.set()
        except Exception as e:
            if not disconnect_event.is_set():
                logger.error(f"Error in metrics sender: {e}")
            disconnect_event.set()

    listener_task = asyncio.create_task(listen_client())
    sender_task = asyncio.create_task(send_metrics())

    await disconnect_event.wait()
    
    logger.info("WebSocket channel terminated cleanly.")
    
    listener_task.cancel()
    sender_task.cancel()
    
    # Wait for tasks to clean up
    try:
        await asyncio.gather(listener_task, sender_task, return_exceptions=True)
    except Exception:
        pass
        
    manager.disconnect(websocket)

# Mount frontend files (index.html, style.css, app.js)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================================================
# BACKGROUND FASTAPI SERVER RUNNER
# ==========================================================================

def run_server():
    """Runs the FastAPI server using Uvicorn on a background thread."""
    import uvicorn
    logger.info("Launching FastAPI ASGI server on background thread...")
    # Using log_level='warning' to avoid spamming the console while pywebview runs
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

# ==========================================================================
# PYWEBVIEW NATIVE JAVASCRIPT BRIDGING API (PORTFOLIO GEM)
# ==========================================================================

class DesktopApi:
    """Exposes native window controller APIs to JavaScript frontend."""
    def __init__(self):
        self.is_maximized = False

    def minimize(self):
        """Minimizes the frameless window."""
        try:
            if webview.windows:
                webview.windows[0].minimize()
                return {"status": "success"}
        except Exception as e:
            logger.error(f"Error minimizing window: {e}")
        return {"status": "error"}

    def toggle_maximize(self):
        """Toggles maximize and restore native window states."""
        try:
            if webview.windows:
                w = webview.windows[0]
                if self.is_maximized:
                    w.restore()
                else:
                    w.maximize()
                self.is_maximized = not self.is_maximized
                return {"status": "success"}
        except Exception as e:
            logger.error(f"Error toggling maximize: {e}")
        return {"status": "error"}

    def close(self):
        """Closes the desktop app."""
        try:
            if webview.windows:
                webview.windows[0].destroy()
                return {"status": "success"}
        except Exception as e:
            logger.error(f"Error closing window: {e}")
        return {"status": "error"}

if __name__ == "__main__":
    # 1. Spawn FastAPI Uvicorn Server in background daemon thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 2. Rest briefly to let background thread bind server socket successfully
    time.sleep(1.0)
    
    # 3. Expose JS-API object
    desktop_api = DesktopApi()
    
    # 4. Construct frameless, transparent native Edge/WebView2 window
    logger.info("Launching pywebview frameless transparent Edge engine...")
    webview.create_window(
        title="MENEDGER",
        url="http://127.0.0.1:8000",
        width=1340,
        height=880,
        resizable=True,
        frameless=True,      # Borderless window
        transparent=True,    # Transparent bleed-through support
        js_api=desktop_api   # Exposes window controls (minimize, close) to JS
    )
    
    # 5. Boot Edge/WebView2 eventloop (runs in the main thread)
    webview.start()
