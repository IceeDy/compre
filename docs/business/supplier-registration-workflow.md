# Supplier customer registration workflow

Supplier customer registration is deliberately asynchronous.

## Why

A supplier may require COMPRE's customer to be registered before accepting an order. That requirement must not make the quote engine depend on a synchronous supplier response.

The workflow is:

1. Quote is created.
2. Supplier can respond to the quote.
3. Proposal can become an order.
4. If supplier registration is required, COMPRE opens a registration workflow.
5. Registration moves through requested → under_review → approved or rejected.
6. Order release checks the registration status.
7. Only the release step is blocked while registration is pending.

This keeps commercial negotiation independent from supplier back-office latency.

## Privacy boundary

The registration record belongs to the tenant and links only the existing supplier and customer identities.

The metadata field is intended for non-sensitive workflow metadata such as requested field names. It must not become a dumping ground for customer documents or unnecessary personal data.

Supplier-specific external references and rejection reasons are kept separately for operational traceability.

## Events

The workflow emits:

- SupplierRegistrationRequested
- SupplierRegistrationUnderReview
- SupplierRegistrationApproved
- SupplierRegistrationRejected
- OrderReleaseBlocked
- OrderReleased

All events use the existing tenant-scoped, idempotent domain-event mechanism.

## API

- POST /api/v1/supplier-registrations
- GET /api/v1/supplier-registrations
- PATCH /api/v1/supplier-registrations/{registration_id}
- POST /api/v1/orders/{order_id}/release

A pending registration does not prevent order creation. It prevents release until the registration is approved.
