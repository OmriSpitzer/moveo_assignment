from dotenv import load_dotenv
from fastapi import FastAPI
from routes.agent_routes import router
from data.manager import DataManager
import os

"""
    Server entry point.
"""

# load environment variables
load_dotenv()

# initialize the data manager
DataManager.init()

# create the FastAPI app
app = FastAPI()
app.include_router(router, prefix="/api")

# Browser and editor probes request these on the process port
@app.get("/")
def api_root():
    return {"message": "Weather Risk API", "health": "/api/health", "hubs": "/api/hubs"}

@app.get("/json/version")
def json_version():
    return {"message": "Weather Risk API"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", os.getenv("DEFAULT_HOST"))
    port = int(os.getenv("PORT", os.getenv("DEFAULT_PORT")))

    print(f"Server is running on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
    
