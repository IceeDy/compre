def register(client, slug, email):
    return client.post("/api/v1/auth/register", json={
        "tenant_name": slug.title(), "tenant_slug": slug, "full_name": "Admin",
        "email": email, "password": "StrongPassword123!",
    })


def login(client, email):
    return client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPassword123!"}).json()["access_token"]


def test_commercial_flow_is_tenant_scoped(client):
    assert register(client, "commerce-a", "a@test.example").status_code == 201
    token = login(client, "a@test.example")
    headers = {"Authorization": f"Bearer {token}"}

    customer = client.post("/api/v1/commercial/customers", headers=headers, json={"name": "Cliente A"})
    assert customer.status_code == 201
    product = client.post("/api/v1/commercial/products", headers=headers, json={
        "sku": "SKU-001", "name": "Produto A", "unit": "UN", "reference_price": "10.00"
    })
    assert product.status_code == 201

    quote = client.post("/api/v1/commercial/quotes", headers=headers, json={
        "customer_id": customer.json()["id"],
        "items": [{"product_id": product.json()["id"], "quantity": 10}],
    })
    assert quote.status_code == 201
    assert quote.json()["status"] == "draft"

    submitted = client.post(f"/api/v1/commercial/quotes/{quote.json()['id']}/submit", headers=headers)
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "submitted"

    supplier = client.post("/api/v1/commercial/suppliers", headers=headers, json={"name": "Fornecedor A"})
    assert supplier.status_code == 201

    proposal = client.post("/api/v1/commercial/proposals", headers=headers, json={
        "quote_id": quote.json()["id"],
        "supplier_id": supplier.json()["id"],
        "items": [{
            "quote_item_id": quote.json()["items"][0]["id"],
            "unit_price": "8.50",
            "quantity": 10,
        }],
    })
    assert proposal.status_code == 201
    assert proposal.json()["total"] == "85.00"

    order = client.post(
        f"/api/v1/orders/from-proposal/{proposal.json()['id']}",
        headers=headers,
    )
    assert order.status_code == 201
    assert order.json()["total"] == "85.00"


def test_cross_tenant_resources_are_rejected(client):
    assert register(client, "tenant-x", "x@test.example").status_code == 201
    token_x = login(client, "x@test.example")
    headers_x = {"Authorization": f"Bearer {token_x}"}
    customer = client.post("/api/v1/commercial/customers", headers=headers_x, json={"name": "Private Customer"})
    customer_id = customer.json()["id"]

    assert register(client, "tenant-y", "y@test.example").status_code == 201
    token_y = login(client, "y@test.example")
    headers_y = {"Authorization": f"Bearer {token_y}"}

    product_y = client.post("/api/v1/commercial/products", headers=headers_y, json={
        "sku": "Y-001", "name": "Product Y", "unit": "UN"
    })
    quote = client.post("/api/v1/commercial/quotes", headers=headers_y, json={
        "customer_id": customer_id,
        "items": [{"product_id": product_y.json()["id"], "quantity": 1}],
    })
    assert quote.status_code == 404


def test_quote_engine_compares_best_mix_and_nonresponsive_suppliers(client):
    assert register(client, "engine-a", "engine@test.example").status_code == 201
    token = login(client, "engine@test.example")
    headers = {"Authorization": f"Bearer {token}"}

    customer = client.post(
        "/api/v1/commercial/customers", headers=headers, json={"name": "Cliente Engine"}
    ).json()
    product_a = client.post(
        "/api/v1/commercial/products",
        headers=headers,
        json={"sku": "A-001", "name": "Produto A", "unit": "UN", "reference_price": "12.00"},
    ).json()
    product_b = client.post(
        "/api/v1/commercial/products",
        headers=headers,
        json={"sku": "B-001", "name": "Produto B", "unit": "UN", "reference_price": "20.00"},
    ).json()

    quote = client.post(
        "/api/v1/commercial/quotes",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "items": [
                {"product_id": product_a["id"], "quantity": 10, "target_price": "11.00"},
                {"product_id": product_b["id"], "quantity": 5, "target_price": "19.00"},
            ],
        },
    ).json()

    supplier_a = client.post(
        "/api/v1/commercial/suppliers", headers=headers, json={"name": "Fornecedor A"}
    ).json()
    supplier_b = client.post(
        "/api/v1/commercial/suppliers", headers=headers, json={"name": "Fornecedor B"}
    ).json()
    supplier_c = client.post(
        "/api/v1/commercial/suppliers", headers=headers, json={"name": "Fornecedor C"}
    ).json()

    requested = client.post(
        f"/api/v1/commercial/quotes/{quote['id']}/supplier-requests",
        headers=headers,
        json={"supplier_ids": [supplier_a["id"], supplier_b["id"], supplier_c["id"]]},
    )
    assert requested.status_code == 200
    assert len(requested.json()) == 3

    items = quote["items"]
    proposal_a = client.post(
        "/api/v1/commercial/proposals",
        headers=headers,
        json={
            "quote_id": quote["id"],
            "supplier_id": supplier_a["id"],
            "items": [
                {"quote_item_id": items[0]["id"], "unit_price": "10.00", "quantity": 10},
                {"quote_item_id": items[1]["id"], "unit_price": "21.00", "quantity": 5},
            ],
        },
    )
    assert proposal_a.status_code == 201

    proposal_b = client.post(
        "/api/v1/commercial/proposals",
        headers=headers,
        json={
            "quote_id": quote["id"],
            "supplier_id": supplier_b["id"],
            "items": [
                {"quote_item_id": items[0]["id"], "unit_price": "9.50", "quantity": 10},
                {"quote_item_id": items[1]["id"], "unit_price": "19.00", "quantity": 5},
            ],
        },
    )
    assert proposal_b.status_code == 201

    comparison = client.get(
        f"/api/v1/commercial/quotes/{quote['id']}/comparison", headers=headers
    )
    assert comparison.status_code == 200
    data = comparison.json()

    assert data["item_count"] == 2
    assert data["covered_item_count"] == 2
    assert data["best_mix_total"] == "190.00"
    assert {row["status"] for row in data["suppliers"]} == {"responded", "requested"}

    best_by_item = {row["quote_item_id"]: row for row in data["items"]}
    assert best_by_item[items[0]["id"]]["best_unit_price"] == "9.50"
    assert best_by_item[items[0]["id"]]["best_supplier_id"] == supplier_b["id"]
    assert best_by_item[items[1]["id"]]["best_unit_price"] == "19.00"
    assert best_by_item[items[1]["id"]]["best_supplier_id"] == supplier_b["id"]
