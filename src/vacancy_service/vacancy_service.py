from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio

app = FastAPI(title="Vacancy Control Service")

class Stock:
    """In-memory estoque com lock atômico."""
    def __init__(self, total:int):
        self.total = total
        self.lock = asyncio.Lock()

    async def reserve(self, qty:int) -> bool:
        async with self.lock:
            if self.total >= qty:
                self.total -= qty
                return True
            return False

    async def current(self) -> int:
        async with self.lock:
            return self.total

stock = Stock(total=1000)

class ReserveRequest(BaseModel):
    qty: int

class ReserveResponse(BaseModel):
    success: bool
    remaining: int

class AvailableResponse(BaseModel):
    qty: int

@app.get("/available", response_model=AvailableResponse)
async def get_available() -> int:
    return AvailableResponse(qty= await stock.current())

@app.post("/reserve", response_model=ReserveResponse)
async def reserve_ticket(req: ReserveRequest):
    if req.qty <= 0:
        raise HTTPException(status = 400, detail="Qty must be > 0")

    ok = await stock.reserve(req.qty)
    return ReserveResponse(success=ok, remaining=await stock.current())
