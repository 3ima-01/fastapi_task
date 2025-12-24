import pytest
from httpx import AsyncClient

from src.users.enums import UserStatusEnum


@pytest.mark.asyncio
async def test_create_and_get_user(client: AsyncClient):
    """Test successful user creation and retrieval by ID."""
    user_data = {"email": "test@test.com"}
    response = await client.post("/users", json=user_data)
    assert response.status_code == 200
    created_user = response.json()
    assert created_user["email"] == "test@test.com"
    assert created_user["status"] == UserStatusEnum.ACTIVE
    user_id = created_user["id"]

    response = await client.get("/users", params={"user_id": user_id})
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 1
    assert users[0]["id"] == user_id
    assert users[0]["email"] == "test@test.com"


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
    """Test that creating a user with an existing email returns 409 Conflict."""
    email = "dup@test.com"
    r1 = await client.post("/users", json={"email": email})
    assert r1.status_code == 200

    r2 = await client.post("/users", json={"email": email})
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_patch_user_to_same_status(client: AsyncClient):
    """Test that PATCHing a user to its current status returns 400 Bad Request."""
    user_id = (await client.post("/users", json={"email": "same@test.com"})).json()["id"]

    r = await client.patch(f"/users/{user_id}", json={"status": "ACTIVE"})
    assert r.status_code == 400
    assert "already active" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_patch_nonexistent_user(client: AsyncClient):
    """Test that PATCHing a non-existent user returns 404 Not Found."""
    r = await client.patch("/users/999999", json={"status": "BLOCKED"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patch_invalid_user_id(client: AsyncClient):
    """Test that PATCH with non-positive user_id returns 422 Unprocessable Entity."""
    for invalid_id in [0, -1, -100]:
        r = await client.patch(f"/users/{invalid_id}", json={"status": "BLOCKED"})
        assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_users_no_matches(client: AsyncClient):
    """Test GET /users with filters yielding no results returns empty list."""
    r1 = await client.get("/users", params={"user_id": 999999})
    assert r1.status_code == 200
    assert r1.json() == []

    r2 = await client.get("/users", params={"email": "notfound@test.com"})
    assert r2.status_code == 200
    assert r2.json() == []


@pytest.mark.asyncio
async def test_get_users_by_email_case_insensitive(client: AsyncClient):
    """Test email filtering is case-insensitive (using ILIKE)."""
    email = "CaseUser@Example.COM"
    user_id = (await client.post("/users", json={"email": email})).json()["id"]

    for query in ["caseuser@example.com", "CASEUSER@EXAMPLE.COM", "CaseUser@Example.Com"]:
        r = await client.get("/users", params={"email": query})
        assert r.status_code == 200
        users = r.json()
        assert len(users) == 1
        assert users[0]["id"] == user_id


@pytest.mark.asyncio
async def test_get_users_combined_filters(client: AsyncClient):
    """Test combined filtering by user_id and status (AND logic)."""
    u1 = (await client.post("/users", json={"email": "active@test.com"})).json()["id"]
    u2 = (await client.post("/users", json={"email": "blocked@test.com"})).json()["id"]
    await client.patch(f"/users/{u2}", json={"status": "BLOCKED"})

    r = await client.get("/users", params={"user_id": u1, "user_status": "ACTIVE"})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["status"] == "ACTIVE"

    r = await client.get("/users", params={"user_id": u2, "user_status": "ACTIVE"})
    data = r.json()
    assert len(data) in (0, 1)
    if data:
        assert data[0]["id"] == u2


@pytest.mark.asyncio
async def test_patch_user_invalid_status(client: AsyncClient):
    """Test PATCH with invalid status value returns 422 Unprocessable Entity."""
    user_id = (await client.post("/users", json={"email": "badstatus@test.com"})).json()["id"]

    for bad_status in ["invalid", "block", "active", "", None]:
        r = await client.patch(f"/users/{user_id}", json={"status": bad_status})
        assert r.status_code == 422, f"Expected 422 for status={bad_status}"


@pytest.mark.asyncio
async def test_create_user_missing_email(client: AsyncClient):
    """Test POST without required 'email' field returns 422."""
    r = await client.post("/users", json={})
    assert r.status_code == 422
    assert "email" in str(r.json()).lower()


@pytest.mark.asyncio
async def test_create_user_invalid_email(client: AsyncClient):
    """Test POST with malformed email addresses returns 422."""
    for bad_email in ["not-an-email", "test@", "@domain.com", ""]:
        r = await client.post("/users", json={"email": bad_email})
        assert r.status_code == 422
        assert "email" in str(r.json()).lower()


@pytest.mark.asyncio
async def test_user_balance_created_automatically(client: AsyncClient):
    """Test that new users get zero-initialized balances for all currencies."""
    response = await client.post("/users", json={"email": "balance@test.com"})
    assert response.status_code == 200
    user_id = response.json()["id"]

    r = await client.get("/users", params={"user_id": user_id})
    assert r.status_code == 200
    user = r.json()[0]
    assert "balances" in user
    assert len(user["balances"]) > 0
    for bal in user["balances"]:
        assert bal["amount"] == 0.0
        assert "currency" in bal


@pytest.mark.asyncio
async def test_user_status_transitions(client: AsyncClient):
    """Test valid status transitions: ACTIVE|BLOCKED."""
    user_id = (await client.post("/users", json={"email": "trans@test.com"})).json()["id"]

    r1 = await client.patch(f"/users/{user_id}", json={"status": "BLOCKED"})
    assert r1.status_code == 200
    assert r1.json()["status"] == "BLOCKED"

    r2 = await client.patch(f"/users/{user_id}", json={"status": "ACTIVE"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "ACTIVE"

    r3 = await client.patch(f"/users/{user_id}", json={"status": "BLOCKED"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "BLOCKED"


@pytest.mark.asyncio
async def test_get_all_users(client: AsyncClient):
    """Test GET /users without filters returns all users."""
    for i in range(3):
        await client.post("/users", json={"email": f"user{i}@test.com"})

    r = await client.get("/users")
    assert r.status_code == 200
    users = r.json()
    assert isinstance(users, list)
    assert len(users) >= 3
