import pytest
from httpx import AsyncClient

from src.transactions.enums import TransactionStatusEnum
from src.users.enums import CurrencyEnum


@pytest.mark.asyncio
async def test_get_transactions_empty(client: AsyncClient):
    response = await client.get("/transactions")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_transactions_by_user_id(client: AsyncClient):
    # create user
    user_resp = await client.post("/users", json={"email": "transact@test.com"})
    assert user_resp.status_code == 200
    user_id = user_resp.json()["id"]

    # create transaction
    tx_data = {"amount": 100.0, "currency": CurrencyEnum.USD}
    tx_resp = await client.post(f"/{user_id}/transactions", json=tx_data)
    assert tx_resp.status_code == 200
    tx = tx_resp.json()

    # check response
    assert tx["user_id"] == user_id
    assert tx["amount"] == 100.0
    assert tx["currency"] == CurrencyEnum.USD
    assert tx["status"] == TransactionStatusEnum.PROCESSED
    assert "created" in tx
    assert "id" in tx

    # get transaction by user_id
    response = await client.get("/transactions", params={"user_id": user_id})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == tx["id"]


@pytest.mark.asyncio
async def test_post_transaction_success(client: AsyncClient):
    user_id = (await client.post("/users", json={"email": "tx_user@test.com"})).json()["id"]

    tx_data = {"amount": 50.5, "currency": CurrencyEnum.EUR}
    response = await client.post(f"/{user_id}/transactions", json=tx_data)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["amount"] == 50.5
    assert data["currency"] == CurrencyEnum.EUR
    assert data["status"] == TransactionStatusEnum.PROCESSED


@pytest.mark.asyncio
async def test_post_transaction_zero_amount(client: AsyncClient):
    """amount=0 → 422(BadRequestDataException)"""
    user_id = (await client.post("/users", json={"email": "zero@test.com"})).json()["id"]

    response = await client.post(f"/{user_id}/transactions", json={"amount": 0.0, "currency": CurrencyEnum.USD})
    assert response.status_code == 422
    assert "zero amount" in response.json()["detail"]


@pytest.mark.asyncio
async def test_post_transaction_missing_currency(client: AsyncClient):
    user_id = (await client.post("/users", json={"email": "no_cur@test.com"})).json()["id"]

    response = await client.post(f"/{user_id}/transactions", json={"amount": 10.0})
    assert response.status_code == 422
    assert "currency" in str(response.json())


@pytest.mark.asyncio
async def test_post_transaction_invalid_currency(client: AsyncClient):
    user_id = (await client.post("/users", json={"email": "bad_cur@test.com"})).json()["id"]

    response = await client.post(f"/{user_id}/transactions", json={"amount": 10.0, "currency": "XYZ"})
    assert response.status_code == 422
    assert "XYZ" in str(response.json()) or "currency" in str(response.json())


@pytest.mark.asyncio
async def test_patch_rollback_transaction_success(client: AsyncClient):
    user_id = (await client.post("/users", json={"email": "rollback@test.com"})).json()["id"]
    tx_id = (
        await client.post(f"/{user_id}/transactions", json={"amount": 100.0, "currency": CurrencyEnum.USD})
    ).json()["id"]

    response = await client.patch(f"/{user_id}/transactions/{tx_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tx_id
    assert data["status"] == TransactionStatusEnum.ROLL_BACKED


@pytest.mark.asyncio
async def test_patch_rollback_nonexistent_transaction(client: AsyncClient):
    user_id = (await client.post("/users", json={"email": "no_tx@test.com"})).json()["id"]

    response = await client.patch(f"/{user_id}/transactions/999999")
    assert response.status_code == 400
