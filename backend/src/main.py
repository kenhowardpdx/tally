from fastapi import FastAPI
from mangum import Mangum

from src.routers import bills, forecast, frequencies, users

app = FastAPI(title="Tally API", version="1.0.0")

app.include_router(bills.router)
app.include_router(forecast.router)
app.include_router(frequencies.router)
app.include_router(users.router)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


handler = Mangum(app)
