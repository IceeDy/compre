from .test_commercial import login, register
from .test_supplier_orders import _prepare_released_order


def test_financial_snapshot_payment_and_settlement(client):
    assert register(client, "finance-a", "finance-a@example.com").status_code == 201
    token = login(client, "finance-a@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    order_id, supplier_id = _prepare_released_order(client, headers)

    rule = client.post(
        "/api/v1/finance/commission-rules",
        headers=headers,
        json={
            "name": "Regra padrão",
            "rate_percent": "10.0000",
            "fixed_amount": "2.00",
        },
    )
    assert rule.status_code == 201

    financial = client.post(
        f"/api/v1/finance/orders/{order_id}/initialize",
        headers=headers,
        json={"commission_rule_id": rule.json()["id"]},
    )
    assert financial.status_code == 201
    data = financial.json()
    assert data["gross_amount"] == "20.00"
    assert data["commission_amount"] == "4.00"
    assert data["supplier_net_amount"] == "16.00"

    duplicate = client.post(
        f"/api/v1/finance/orders/{order_id}/initialize",
        headers=headers,
        json={"commission_rule_id": rule.json()["id"]},
    )
    assert duplicate.status_code == 409

    payment = client.post(
        "/api/v1/finance/payments",
        headers=headers,
        json={
            "order_id": order_id,
            "amount": "20.00",
            "currency": "BRL",
            "flow": "customer_to_platform",
            "method": "pix",
            "provider_reference": "PIX-001",
        },
    )
    assert payment.status_code == 201

    paid = client.patch(
        f"/api/v1/finance/payments/{payment.json()['id']}",
        headers=headers,
        json={"status": "paid"},
    )
    assert paid.status_code == 200

    settlements = client.get("/api/v1/finance/settlements", headers=headers)
    assert settlements.status_code == 200
    settlement = next(item for item in settlements.json() if item["order_id"] == order_id)
    assert settlement["supplier_id"] == supplier_id
    assert settlement["amount"] == "16.00"

    settled = client.post(
        f"/api/v1/finance/settlements/{order_id}/pay",
        headers=headers,
    )
    assert settled.status_code == 200
    assert settled.json()["status"] == "paid"

    reconciled = client.post(
        f"/api/v1/finance/settlements/{order_id}/reconcile",
        headers=headers,
    )
    assert reconciled.status_code == 200
    assert reconciled.json()["status"] == "reconciled"


def test_finance_is_tenant_scoped(client):
    assert register(client, "finance-x", "finance-x@example.com").status_code == 201
    token_x = login(client, "finance-x@example.com")
    headers_x = {"Authorization": f"Bearer {token_x}"}
    order_id, _ = _prepare_released_order(client, headers_x)

    rule = client.post(
        "/api/v1/finance/commission-rules",
        headers=headers_x,
        json={"name": "Regra X", "rate_percent": "5.0000"},
    )
    assert rule.status_code == 201
    initialized = client.post(
        f"/api/v1/finance/orders/{order_id}/initialize",
        headers=headers_x,
        json={"commission_rule_id": rule.json()["id"]},
    )
    assert initialized.status_code == 201

    assert register(client, "finance-y", "finance-y@example.com").status_code == 201
    token_y = login(client, "finance-y@example.com")
    headers_y = {"Authorization": f"Bearer {token_y}"}

    response = client.get(
        f"/api/v1/finance/orders/{order_id}",
        headers=headers_y,
    )
    assert response.status_code == 404
