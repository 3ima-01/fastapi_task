import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import create_db_and_tables, get_async_session
from src.transactions.routers import router as transactions_router
from src.users.routers.users import router as users_router

app = FastAPI()
app.include_router(users_router)
app.include_router(transactions_router)


@app.on_event("startup")
async def on_startup(session: AsyncSession = Depends(get_async_session)):
    await create_db_and_tables()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7999, reload=True)
