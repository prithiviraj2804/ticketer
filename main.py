from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import asyncio
from monitor import TicketMonitor
from config import load_config

monitor = TicketMonitor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background task
    task = asyncio.create_task(monitor.start_monitoring())
    yield
    # Shutdown
    monitor.stop_monitoring()
    await task

app = FastAPI(title="Ticket Monitor API", lifespan=lifespan)

@app.get("/")
def read_root():
    return {
        "status": "running",
        "last_check_status": monitor.last_check_status,
        "last_check_time": monitor.last_check_time,
        "config": {
            "check_interval": monitor.config.check_interval,
            "url": monitor.config.url # Careful exposing full URL if sensitive, but here it's fine
        }
    }

@app.post("/check")
async def trigger_check(background_tasks: BackgroundTasks):
    """Manually trigger a check (runs in background)."""
    background_tasks.add_task(monitor.check_tickets)
    return {"message": "Check triggered in background"}

@app.get("/config")
def get_config():
    return monitor.config
