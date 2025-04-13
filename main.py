from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import engine
import models
from routes import landlord_routes, property_routes, room_routes, tenant_routes, payment_routes, electricity_routes
from fastapi.staticfiles import StaticFiles

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Property Management API",
    description="FastAPI implementation of Property Management System",
    version="1.0.0"
)

# app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(landlord_routes.router)
app.include_router(property_routes.router)
app.include_router(room_routes.router)
app.include_router(tenant_routes.router)
app.include_router(payment_routes.router)
app.include_router(electricity_routes.router)

# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Property Management API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)