from fastapi import FastAPI

from src.transactions.routers import router as transactions_router
from src.users.routers.users import router as users_router

app = FastAPI()
app.include_router(users_router)
app.include_router(transactions_router)
