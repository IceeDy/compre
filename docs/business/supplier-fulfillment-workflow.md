# Supplier Fulfillment Workflow

## Objective

Separate the commercial order accepted by the customer from the operational order sent to the supplier.

The lifecycle is:

`Order released -> SupplierOrder sent -> confirmed -> preparing -> shipped -> delivered`

A supplier rejection or cancellation is represented on the supplier order without rewriting the commercial history.

## Why this separation matters

The COMPRE order represents the commercial commitment.

The supplier order represents execution with the selected supplier.

Keeping them separate allows the platform to record:

- when the order was released;
- when the supplier received it;
- supplier confirmation or rejection;
- supplier reference numbers;
- preparation and shipment;
- delivery completion.

This also creates a clean foundation for future shipment, delivery proof, invoicing and commission workflows.

## Privacy boundary

The supplier order stores identifiers necessary for execution and references the existing customer/order context through internal relationships.

Supplier integrations should receive only the fields required to fulfill the order. Customer PII must not be copied into analytics or event payloads unless there is a documented operational purpose.

## Events

The workflow emits:

- `SupplierOrderSent`
- `SupplierOrderConfirmed`
- `SupplierOrderRejected`
- `SupplierOrderPreparing`
- `ShipmentCreated`
- `DeliveryCompleted`
- `SupplierOrderCancelled`

The event store remains tenant-scoped and idempotent.

## API

### Create supplier order

`POST /api/v1/supplier-orders/from-order/{order_id}`

Only a released COMPRE order can generate a supplier order.

### List supplier orders

`GET /api/v1/supplier-orders`

### Update supplier order

`PATCH /api/v1/supplier-orders/{supplier_order_id}`

Allowed transitions are enforced server-side.

## Next evolution

The current phase intentionally keeps shipment and delivery state on the supplier order.

A later fulfillment phase can introduce dedicated `shipments` and `deliveries` entities with tracking numbers, carriers, proof of delivery and timestamps without changing the commercial order model.
