# Arquitetura

## Contextos

Identity & Access: usuários, organizações, tenants, papéis e sessões.

Commercial: clientes, fornecedores, produtos, cotações, propostas e pedidos.

Fulfillment: pagamento, pedido ao fornecedor, expedição, entrega e documentos.

Finance: comissões, repasses e conciliação.

Audit: eventos de segurança e negócio.

Intelligence: dados derivados e agregados para indicadores e produtos analíticos.

## Regra fundamental

O contexto de Intelligence não deve acessar diretamente tabelas de PII para produzir métricas. Dados analíticos passam por transformação que minimize, agregue ou anonimize informações conforme a finalidade.

## Multi-tenancy

Toda entidade operacional pertencente a uma organização deve carregar tenant_id. A autorização deve validar tenant e papel no backend; nunca confiar apenas em filtros enviados pelo frontend.

## Eventos de domínio

QuoteCreated, QuoteSubmitted, ProposalCreated, ProposalAccepted, PaymentConfirmed, PurchaseOrderCreated, SupplierConfirmed, ShipmentCreated, DeliveryCompleted, InvoiceIssued, CommissionGenerated.

Eventos devem ser idempotentes e possuir identificador único.

## Arquitetura lógica

React/TypeScript -> FastAPI -> Application Services -> Domain/Policies -> Repositories -> PostgreSQL

Eventos operacionais -> Pipeline analítico -> Dados agregados -> Produtos de inteligência.