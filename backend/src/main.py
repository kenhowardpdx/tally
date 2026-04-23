from fastapi import FastAPI
from mangum import Mangum

app = FastAPI(title="Tally API", version="1.0.0")


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


handler = Mangum(app)
