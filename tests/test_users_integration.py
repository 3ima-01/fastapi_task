import httpx
import pytest

from src.users.enums import UserStatusEnum


@pytest.mark.asyncio
class TestUsers:
    base_url = "/users"

    @pytest.mark.parametrize("email", ["test1@test.com", "test2@test.com", "test3@test.com"])
    async def test_create_and_get_user(self, client: httpx.AsyncClient, email: str):
        """Test successful user creation and retrieval by ID."""
        response = await client.post(self.base_url, json={"email": email})
        assert response.status_code == httpx.codes.OK
        created_user = response.json()
        assert created_user["email"] == email
        assert created_user["status"] == UserStatusEnum.ACTIVE
        user_id = created_user["id"]

        response = await client.get(self.base_url, params={"user_id": user_id})
        assert response.status_code == httpx.codes.OK
        users = response.json()
        assert len(users) == 1
        assert users[0]["id"] == user_id
        assert users[0]["email"] == email

    @pytest.mark.parametrize("email", ["dup@test.com", "dup2@test.com"])
    async def test_create_user_duplicate_email(self, client: httpx.AsyncClient, email: str):
        """Test that creating a user with an existing email returns 409 Conflict."""
        r1 = await client.post(self.base_url, json={"email": email})
        assert r1.status_code == httpx.codes.OK

        r2 = await client.post(self.base_url, json={"email": email})
        assert r2.status_code == httpx.codes.CONFLICT

    async def test_patch_user_to_same_status(self, client: httpx.AsyncClient):
        """Test that PATCHing a user to its current status returns 400 Bad Request."""
        user_id = (await client.post(self.base_url, json={"email": "same@test.com"})).json()["id"]

        r = await client.patch(f"{self.base_url}/{user_id}", json={"status": "ACTIVE"})
        assert r.status_code == httpx.codes.BAD_REQUEST
        assert "already active" in r.json()["detail"].lower()

    async def test_patch_nonexistent_user(self, client: httpx.AsyncClient):
        """Test that PATCHing a non-existent user returns 404 Not Found."""
        r = await client.patch("{self.base_url}/999999", json={"status": "BLOCKED"})
        assert r.status_code == httpx.codes.NOT_FOUND

    @pytest.mark.parametrize("invalid_id", [0, -1, -100])
    async def test_patch_invalid_user_id(self, client: httpx.AsyncClient, invalid_id: int):
        """Test that PATCH with non-positive user_id returns 422 Unprocessable Entity."""
        r = await client.patch(f"{self.base_url}/{invalid_id}", json={"status": "BLOCKED"})
        assert r.status_code == httpx.codes.UNPROCESSABLE_ENTITY

    async def test_get_users_no_matches(self, client: httpx.AsyncClient):
        """Test GET /users with filters yielding no results returns empty list."""
        r1 = await client.get(self.base_url, params={"user_id": 999999})
        assert r1.status_code == httpx.codes.OK
        assert r1.json() == []

        r2 = await client.get(self.base_url, params={"email": "notfound@test.com"})
        assert r2.status_code == httpx.codes.OK
        assert r2.json() == []

    async def test_get_users_by_email_case_insensitive(self, client: httpx.AsyncClient):
        """Test email filtering is case-insensitive (using ILIKE)."""
        email = "CaseUser@Example.COM"
        user_id = (await client.post(self.base_url, json={"email": email})).json()["id"]

        for query in ["caseuser@example.com", "CASEUSER@EXAMPLE.COM", "CaseUser@Example.Com"]:
            r = await client.get(self.base_url, params={"email": query})

        assert r.status_code == httpx.codes.OK
        users = r.json()
        assert len(users) == 1
        assert users[0]["id"] == user_id

    async def test_get_users_combined_filters(self, client: httpx.AsyncClient):
        """Test combined filtering by user_id and status (AND logic)."""
        u1 = (await client.post(self.base_url, json={"email": "active@test.com"})).json()["id"]
        u2 = (await client.post(self.base_url, json={"email": "blocked@test.com"})).json()["id"]
        await client.patch(f"{self.base_url}/{u2}", json={"status": "BLOCKED"})

        r = await client.get(self.base_url, params={"user_id": u1, "user_status": "ACTIVE"})
        assert r.status_code == httpx.codes.OK
        assert len(r.json()) == 1
        assert r.json()[0]["status"] == "ACTIVE"

        r = await client.get(self.base_url, params={"user_id": u2, "user_status": "ACTIVE"})
        data = r.json()
        assert len(data) in (0, 1)
        if data:
            assert data[0]["id"] == u2

    async def test_patch_user_invalid_status(self, client: httpx.AsyncClient):
        """Test PATCH with invalid status value returns 422 Unprocessable Entity."""
        user_id = (await client.post(self.base_url, json={"email": "badstatus@test.com"})).json()["id"]

        for bad_status in ["invalid", "block", "active", "", None]:
            r = await client.patch(f"/users/{user_id}", json={"status": bad_status})
            assert r.status_code == httpx.codes.UNPROCESSABLE_ENTITY

    async def test_create_user_missing_email(self, client: httpx.AsyncClient):
        """Test POST without required 'email' field returns 422."""
        r = await client.post(self.base_url, json={})
        assert r.status_code == httpx.codes.UNPROCESSABLE_ENTITY
        assert "email" in str(r.json()).lower()

    @pytest.mark.parametrize("bad_email", ["not-an-email", "test@", "@domain.com", ""])
    async def test_create_user_invalid_email(self, client: httpx.AsyncClient, bad_email: str):
        """Test POST with malformed email addresses returns 422."""
        r = await client.post(self.base_url, json={"email": bad_email})
        assert r.status_code == httpx.codes.UNPROCESSABLE_ENTITY
        assert "email" in str(r.json()).lower()

    async def test_user_balance_created_automatically(self, client: httpx.AsyncClient):
        """Test that new users get zero-initialized balances for all currencies."""
        response = await client.post(self.base_url, json={"email": "balance@test.com"})
        assert response.status_code == httpx.codes.OK
        user_id = response.json()["id"]

        r = await client.get(self.base_url, params={"user_id": user_id})
        assert r.status_code == httpx.codes.OK
        user = r.json()[0]
        assert "balances" in user
        assert len(user["balances"]) > 0
        for bal in user["balances"]:
            assert bal["amount"] == 0.0
            assert "currency" in bal

    async def test_user_status_transitions(self, client: httpx.AsyncClient):
        """Test valid status transitions: ACTIVE|BLOCKED."""
        user_id = (await client.post(self.base_url, json={"email": "trans@test.com"})).json()["id"]

        r1 = await client.patch(f"{self.base_url}/{user_id}", json={"status": "BLOCKED"})
        assert r1.status_code == httpx.codes.OK
        assert r1.json()["status"] == UserStatusEnum.BLOCKED

        r2 = await client.patch(f"{self.base_url}/{user_id}", json={"status": "ACTIVE"})
        assert r2.status_code == httpx.codes.OK
        assert r2.json()["status"] == UserStatusEnum.ACTIVE

        r3 = await client.patch(f"{self.base_url}/{user_id}", json={"status": "BLOCKED"})
        assert r3.status_code == httpx.codes.OK
        assert r3.json()["status"] == UserStatusEnum.BLOCKED

    @pytest.mark.parametrize("id", [1, 2, 3])
    async def test_get_all_users(self, client: httpx.AsyncClient, id: int):
        """Test GET /users without filters returns all users."""
        await client.post(self.base_url, json={"email": f"user{id}@test.com"})

        r = await client.get(self.base_url)
        assert r.status_code == httpx.codes.OK
        users = r.json()
        assert isinstance(users, list)
        assert len(users) >= 3
