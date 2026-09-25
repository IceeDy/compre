def register(client, *, slug: str, email: str):
    return client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": f"Tenant {slug}",
            "tenant_slug": slug,
            "full_name": "Admin User",
            "email": email,
            "password": "StrongPassword123!",
        },
    )


def login(client, *, email: str):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )


def test_register_login_and_protected_routes(client):
    registered = register(client, slug="acme", email="admin@acme.test")
    assert registered.status_code == 201
    assert registered.json()["roles"] == ["admin"]

    duplicate = register(client, slug="acme", email="other@acme.test")
    assert duplicate.status_code == 409

    token_response = login(client, email="admin@acme.test")
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "admin@acme.test"

    tenant = client.get("/api/v1/tenants/me", headers=headers)
    assert tenant.status_code == 200
    assert tenant.json()["slug"] == "acme"

    admin_check = client.get("/api/v1/users/admin-check", headers=headers)
    assert admin_check.status_code == 200


def test_invalid_credentials_are_rejected(client):
    register(client, slug="beta", email="admin@beta.test")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@beta.test", "password": "wrong"},
    )
    assert response.status_code == 401


def test_tenant_isolation_is_bound_to_token(client):
    first = register(client, slug="tenant-one", email="one@example.test")
    second = register(client, slug="tenant-two", email="two@example.test")
    assert first.status_code == 201
    assert second.status_code == 201

    token_one = login(client, email="one@example.test").json()["access_token"]
    token_two = login(client, email="two@example.test").json()["access_token"]

    tenant_one = client.get(
        "/api/v1/tenants/me",
        headers={"Authorization": f"Bearer {token_one}"},
    ).json()
    tenant_two = client.get(
        "/api/v1/tenants/me",
        headers={"Authorization": f"Bearer {token_two}"},
    ).json()

    assert tenant_one["slug"] == "tenant-one"
    assert tenant_two["slug"] == "tenant-two"
    assert tenant_one["id"] != tenant_two["id"]


def test_protected_route_requires_authentication(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
