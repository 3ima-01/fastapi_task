import httpx
import pytest

from src.transactions.enums import TransactionStatusEnum
from src.users.enums import CurrencyEnum


@pytest.mark.asyncio
class TestTransactions:
    base_url = "/transactions"

    async def test_get_transactions_empty(self, client: httpx.AsyncClient):
        response = await client.get(self.base_url)
        assert response.status_code == httpx.codes.OK
        assert response.json() == []

    async def test_get_transactions_by_user_id(self, client: httpx.AsyncClient):
        # create user
        user_resp = await client.post("/users", json={"email": "transact@test.com"})
        assert user_resp.status_code == httpx.codes.OK
        user_id = user_resp.json()["id"]

        # create transaction
        tx_data = {"amount": 100.0, "currency": CurrencyEnum.USD}
        tx_resp = await client.post(f"transactions/{user_id}", json=tx_data)
        assert tx_resp.status_code == httpx.codes.OK
        tx = tx_resp.json()

        # check response
        assert tx["user_id"] == user_id
        assert tx["amount"] == 100.0
        assert tx["currency"] == CurrencyEnum.USD
        assert tx["status"] == TransactionStatusEnum.PROCESSED
        assert "created" in tx
        assert "id" in tx

        # get transaction by user_id
        response = await client.get(self.base_url, params={"user_id": user_id})
        assert response.status_code == httpx.codes.OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == tx["id"]

    async def test_post_transaction_success(self, client: httpx.AsyncClient):
        user_id = (await client.post("/users", json={"email": "tx_user@test.com"})).json()["id"]

        tx_data = {"amount": 50.5, "currency": CurrencyEnum.EUR}
        response = await client.post(f"{self.base_url}/{user_id}", json=tx_data)
        assert response.status_code == httpx.codes.OK
        data = response.json()
        assert data["user_id"] == user_id
        assert data["amount"] == 50.5
        assert data["currency"] == CurrencyEnum.EUR
        assert data["status"] == TransactionStatusEnum.PROCESSED

    async def test_post_transaction_zero_amount(self, client: httpx.AsyncClient):
        """amount=0 → 422(BadRequestDataException)"""
        user_id = (await client.post("/users", json={"email": "zero@test.com"})).json()["id"]

        response = await client.post(f"{self.base_url}/{user_id}", json={"amount": 0.0, "currency": CurrencyEnum.USD})
        assert response.status_code == httpx.codes.UNPROCESSABLE_ENTITY
        assert "zero amount" in response.json()["detail"]

    async def test_post_transaction_missing_currency(self, client: httpx.AsyncClient):
        user_id = (await client.post("/users", json={"email": "no_cur@test.com"})).json()["id"]

        response = await client.post(f"{self.base_url}/{user_id}", json={"amount": 10.0})
        assert response.status_code == httpx.codes.UNPROCESSABLE_ENTITY
        assert "currency" in str(response.json())

    async def test_post_transaction_invalid_currency(self, client: httpx.AsyncClient):
        user_id = (await client.post("/users", json={"email": "bad_cur@test.com"})).json()["id"]
        response = await client.post(f"{self.base_url}/{user_id}", json={"amount": 10.0, "currency": "XYZ"})
        assert response.status_code == httpx.codes.UNPROCESSABLE_ENTITY
        assert "XYZ" in str(response.json()) or "currency" in str(response.json())

    async def test_patch_rollback_transaction_success(self, client: httpx.AsyncClient):
        user_id = (await client.post("/users", json={"email": "rollback@test.com"})).json()["id"]
        tx_id = (
            await client.post(f"{self.base_url}/{user_id}", json={"amount": 100.0, "currency": CurrencyEnum.USD})
        ).json()["id"]

        response = await client.patch(f"{self.base_url}/{user_id}/{tx_id}")
        assert response.status_code == httpx.codes.OK
        data = response.json()
        assert data["id"] == tx_id
        assert data["status"] == TransactionStatusEnum.ROLL_BACKED

    async def test_patch_rollback_nonexistent_transaction(self, client: httpx.AsyncClient):
        user_id = (await client.post("/users", json={"email": "no_tx@test.com"})).json()["id"]

        response = await client.patch(f"{self.base_url}/{user_id}/999999")
        assert response.status_code == httpx.codes.BAD_REQUEST
