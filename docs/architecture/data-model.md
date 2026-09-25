# Modelo de dados inicial

## Identidade

tenants, users, roles, user_roles

## Cadastro

customers, suppliers, addresses, products

## Comercial

quotes, quote_items, proposals, proposal_items, orders, order_items

## Execução

payments, supplier_orders, shipments, deliveries, documents

## Financeiro

commissions, commission_rules, settlements

## Governança

audit_logs, domain_events

## Regras

PII deve ser identificável por necessidade operacional, mas não replicada desnecessariamente em tabelas analíticas.

Campos financeiros usam Decimal/Numeric, nunca float.

IDs públicos devem ser UUIDs. Identificadores internos podem ser separados dos identificadores expostos pela API.

Entidades multi-tenant devem possuir tenant_id, índices adequados e integridade referencial.