from .test_commercial import login, register


def _prepare_released_order(client, headers):
    customer = client.post(
        "/api/v1/commercial/customers",
        headers=headers,
        json={"name": "Cliente Fulfillment"},
    ).json()
    product = client.post(
        "/api/v1/commercial/products",
        headers=headers,
        json={"sku": "FUL-001", "name": "Produto Fulfillment", "unit": "UN"},
    ).json()
    supplier = client.post(
        "/api/v1/commercial/suppliers",
        headers=headers,
        json={"name": "Fornecedor Fulfillment"},
    ).json()
    quote = client.post(
        "/api/v1/commercial/quotes",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": product["id"], "quantity": 2}],
        },
    ).json()
    proposal = client.post(
        "/api/v1/commercial/proposals",
        headers=headers,
        json={
            "quote_id": quote["id"],
            "supplier_id": supplier["id"],
            "items": [
                {
                    "quote_item_id": quote["items"][0]["id"],
                    "unit_price": "10.00",
                    "quantity": 2,
                }
            ],
        },
    ).json()
    order = client.post(
        f"/api/v1/orders/from-proposal/{proposal['id']}",
        headers=headers,
    ).json()
    released = client.post(
        f"/api/v1/orders/{order['id']}/release",
        headers=headers,
    )
    assert released.status_code == 200
    return order["id"], supplier["id"]


def test_supplier_order_full_lifecycle(client):
    assert register(client, "fulfillment-a", "fulfillment@test.example").status_code == 201
    token = login(client, "fulfillment@test.example")
    headers = {"Authorization": f"Bearer {token}"}

    order_id, supplier_id = _prepare_released_order(client, headers)

    created = client.post(
        f"/api/v1/supplier-orders/from-order/{order_id}",
        headers=headers,
    )
    assert created.status_code == 201
    supplier_order = created.json()
    assert supplier_order["status"] == "sent"
    assert supplier_order["supplier_id"] == supplier_id

    transitions = [
        ("confirmed", 200),
        ("preparing", 200),
        ("shipped", 200),
        ("delivered", 200),
    ]
    for next_status, expected in transitions:
        response = client.patch(
            f"/api/v1/supplier-orders/{supplier_order['id']}",
            headers=headers,
            json={"status": next_status, "external_reference": "SUP-900"},
        )
        assert response.status_code == expected

    final = client.get("/api/v1/supplier-orders", headers=headers)
    assert final.status_code == 200
    assert final.json()[0]["status"] == "delivered"


def test_supplier_order_rejects_invalid_transition_and_duplicate(client):
    assert register(client, "fulfillment-b", "fulfillment-b@test.example").status_code == 201
    token = login(client, "fulfillment-b@test.example")
    headers = {"Authorization": f"Bearer {token}"}

    order_id, _ = _prepare_released_order(client, headers)
    created = client.post(
        f"/api/v1/supplier-orders/from-order/{order_id}",
        headers=headers,
    )
    supplier_order_id = created.json()["id"]

    duplicate = client.post(
        f"/api/v1/supplier-orders/from-order/{order_id}",
        headers=headers,
    )
    assert duplicate.status_code == 409

    invalid = client.patch(
        f"/api/v1/supplier-orders/{supplier_order_id}",
        headers=headers,
        json={"status": "delivered"},
    )
    assert invalid.status_code == 409


def test_supplier_orders_are_tenant_scoped(client):
    assert register(client, "fulfillment-x", "fulfillment-x@test.example").status_code == 201
    token_x = login(client, "fulfillment-x@test.example")
    headers_x = {"Authorization": f"Bearer {token_x}"}
    order_id, _ = _prepare_released_order(client, headers_x)

    created = client.post(
        f"/api/v1/supplier-orders/from-order/{order_id}",
        headers=headers_x,
    )
    supplier_order_id = created.json()["id"]

    assert register(client, "fulfillment-y", "fulfillment-y@test.example").status_code == 201
    token_y = login(client, "fulfillment-y@test.example")
    headers_y = {"Authorization": f"Bearer {token_y}"}

    response = client.patch(
        f"/api/v1/supplier-orders/{supplier_order_id}",
        headers=headers_y,
        json={"status": "confirmed"},
    )
    assert response.status_code == 404
