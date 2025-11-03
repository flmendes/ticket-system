from fastapi.applications import FastAPI
from pydantic.main import BaseModel
from starlette.exceptions import HTTPException
import json
import httpx
import os


app = FastAPI(title="Ticket Sale Service")

VACANCY_URL = os.getenv("VACANCY_URL", "http://localhost:8001")

class PurchaseRequest(BaseModel):
    qty: int

class PurchaseResponse(BaseModel):
    success: bool
    remaining: int
    message: str | None = None


async def reserve_vacancy(qty: int) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{VACANCY_URL}/reserve",
            json={"qty": qty},
            timeout=5.0,
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code = resp.status_code,
                detail=f"Vacancy service error: {resp.text}"
            )
        return resp.json()

@app.post("/purchase", response_model=PurchaseResponse)
async def purchase_ticket(req: PurchaseRequest):
    if req.qty <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be > 0")

    result = await reserve_vacancy(req.qty)

    if result["success"]:
        return PurchaseResponse(
            success=True,
            remaining=result["remaining"],
            message="Purchase sucessful!"
        )

    return PurchaseResponse(success=False, remaining=result["remaining"])
