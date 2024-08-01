from fastapi import FastAPI
from app.api.v1 import router as api_v1_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="FastAPI|WebScraper", version="1.0.0")

# Allow all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def index():
    return {"response":"Hello!, World"}
