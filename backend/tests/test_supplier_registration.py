from .test_commercial import login, register


def test_supplier_registration_is_asynchronous_and_blocks_only_order_release(client):
    assert register(client, "registration-a", "registration@test.example").status_code == 201
    token = login(client, "registration@test.example")
    headers = {"Authorization": f"Bearer {token}"}

    customer = client.post(
        "/api/v1/commercial/customers", headers=headers, json={"name": "Cliente Registro"}
    ).json()
    product = client.post(
        "/api/v1/commercial/products",
        headers=headers,
        json={"sku": "REG-001", "name": "Produto Registro", "unit": "UN"},
    ).json()
    supplier = client.post(
        "/api/v1/commercial/suppliers", headers=headers, json={"name": "Fornecedor Registro"}
    ).json()
    quote = client.post(
        "/api/v1/commercial/quotes",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": product["id"], "quantity": 3}],
        },
    ).json()
    proposal = client.post(
        "/api/v1/commercial/proposals",
        headers=headers,
        json={
            "quote_id": quote["id"],
            "supplier_id": supplier["id"],
            "items": [
                {"quote_item_id": quote["items"][0]["id"], "unit_price": "7.50", "quantity": 3}
            ],
        },
    )
    assert proposal.status_code == 201

    order = client.post(
        f"/api/v1/orders/from-proposal/{proposal.json()['id']}", headers=headers
    )
    assert order.status_code == 201

    registration = client.post(
        "/api/v1/supplier-registrations",
        headers=headers,
        json={
            "supplier_id": supplier["id"],
            "customer_id": customer["id"],
            "requested_fields": ["document", "billing_address"],
        },
    )
    assert registration.status_code == 201
    registration_id = registration.json()["id"]

    blocked = client.post(
        f"/api/v1/orders/{order.json()['id']}/release", headers=headers
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["statuses"] == ["requested"]

    under_review = client.patch(
        f"/api/v1/supplier-registrations/{registration_id}",
        headers=headers,
        json={"status": "under_review", "external_reference": "SUP-123"},
    )
    assert under_review.status_code == 200

    approved = client.patch(
        f"/api/v1/supplier-registrations/{registration_id}",
        headers=headers,
        json={"status": "approved", "external_reference": "SUP-123"},
    )
    assert approved.status_code == 200

    released = client.post(
        f"/api/v1/orders/{order.json()['id']}/release", headers=headers
    )
    assert released.status_code == 200
    assert released.json()["status"] == "released"


def test_supplier_registration_is_tenant_scoped(client):
    assert register(client, "registration-x", "registration-x@test.example").status_code == 201
    token_x = login(client, "registration-x@test.example")
    headers_x = {"Authorization": f"Bearer {token_x}"}

    customer = client.post(
        "/api/v1/commercial/customers", headers=headers_x, json={"name": "Cliente X"}
    ).json()
    supplier = client.post(
        "/api/v1/commercial/suppliers", headers=headers_x, json={"name": "Fornecedor X"}
    ).json()

    assert register(client, "registration-y", "registration-y@test.example").status_code == 201
    token_y = login(client, "registration-y@test.example")
    headers_y = {"Authorization": f"Bearer {token_y}"}

    response = client.post(
        "/api/v1/supplier-registrations",
        headers=headers_y,
        json={"supplier_id": supplier["id"], "customer_id": customer["id"]},
    )
    assert response.status_code == 404
