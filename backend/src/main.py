from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from src.api import (
    accounts,
    bills,
    cycle_overrides,
    dashboard,
    demo,
    forecast,
    me,
    transactions,
    windfalls,
)
from src.core.auth import get_current_user

app = FastAPI()

app.include_router(accounts.router)
app.include_router(bills.router)
app.include_router(cycle_overrides.router)
app.include_router(dashboard.router)
app.include_router(demo.router)
app.include_router(forecast.router)
app.include_router(me.router)
app.include_router(transactions.router)
app.include_router(windfalls.router)

# Only needed for local dev: the frontend (:5173) and backend (:8000) run on
# different origins there. In prod they share an origin via CloudFront's
# /api/v1/* routing (see infra/main.tf's cloudfront module), so this is a no-op.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/api/v1/me")
def read_current_user(user: dict = Depends(get_current_user)):
    # Auth0 access tokens for a custom API audience don't carry profile claims
    # like email by default (that needs a custom Auth0 Action) - only `sub` is
    # guaranteed to be present here.
    return {"sub": user["sub"]}

handler = Mangum(app)