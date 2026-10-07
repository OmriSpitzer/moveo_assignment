from dotenv import load_dotenv
import os
from pathlib import Path

"""
    Server entry point.
"""

# load environment variables
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes.agent_routes import router
from data.manager import DataManager

# initialize the data manager
DataManager.init()

# create the FastAPI app
app = FastAPI()
app.include_router(router, prefix="/api")

# Browser and editor probes request these on the process port
@app.get("/json/version")
def json_version():
    return {"message": "Weather Risk API"}

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.is_dir():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="client")
else:
    @app.get("/")
    def api_root():
        return {"message": "Weather Risk API", "health": "/api/health", "hubs": "/api/hubs"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", os.getenv("DEFAULT_HOST"))
    port = int(os.getenv("PORT", os.getenv("DEFAULT_PORT")))

    print(f"Server is running on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
    
