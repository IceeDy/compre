from .test_commercial import login, register
from .test_supplier_orders import _prepare_released_order


def test_shipment_and_delivery_lifecycle(client):
    assert register(client, "delivery-a", "delivery@test.example").status_code == 201
    token = login(client, "delivery@test.example")
    headers = {"Authorization": f"Bearer {token}"}

    order_id, _ = _prepare_released_order(client, headers)
    supplier_order = client.post(
        f"/api/v1/supplier-orders/from-order/{order_id}",
        headers=headers,
    ).json()

    for next_status in ("confirmed", "preparing", "shipped"):
        response = client.patch(
            f"/api/v1/supplier-orders/{supplier_order['id']}",
            headers=headers,
            json={"status": next_status},
        )
        assert response.status_code == 200

    shipment = client.post(
        f"/api/v1/fulfillment/supplier-orders/{supplier_order['id']}/shipment",
        headers=headers,
        json={
            "carrier": "Transportadora Exemplo",
            "tracking_number": "BR-123456",
        },
    )
    assert shipment.status_code == 201
    shipment_id = shipment.json()["id"]

    delivery = client.post(
        f"/api/v1/fulfillment/shipments/{shipment_id}/delivery",
        headers=headers,
    )
    assert delivery.status_code == 201
    delivery_id = delivery.json()["id"]

    delivered = client.patch(
        f"/api/v1/fulfillment/deliveries/{delivery_id}",
        headers=headers,
        json={
            "status": "delivered",
            "recipient_name": "Recebedor Exemplo",
            "proof_reference": "POD-001",
        },
    )
    assert delivered.status_code == 200
    assert delivered.json()["status"] == "delivered"


def test_delivery_requires_recipient_when_delivered(client):
    assert register(client, "delivery-b", "delivery-b@test.example").status_code == 201
    token = login(client, "delivery-b@test.example")
    headers = {"Authorization": f"Bearer {token}"}

    order_id, _ = _prepare_released_order(client, headers)
    supplier_order = client.post(
        f"/api/v1/supplier-orders/from-order/{order_id}",
        headers=headers,
    ).json()
    for next_status in ("confirmed", "preparing", "shipped"):
        assert client.patch(
            f"/api/v1/supplier-orders/{supplier_order['id']}",
            headers=headers,
            json={"status": next_status},
        ).status_code == 200

    shipment = client.post(
        f"/api/v1/fulfillment/supplier-orders/{supplier_order['id']}/shipment",
        headers=headers,
        json={},
    ).json()

    delivery = client.post(
        f"/api/v1/fulfillment/shipments/{shipment['id']}/delivery",
        headers=headers,
    ).json()

    response = client.patch(
        f"/api/v1/fulfillment/deliveries/{delivery['id']}",
        headers=headers,
        json={"status": "delivered"},
    )
    assert response.status_code == 400
