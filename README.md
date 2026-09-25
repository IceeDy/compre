# COMPRE

Plataforma B2B de intermediação de compras.

O COMPRE conecta compradores e fornecedores, centralizando cotação, proposta, aprovação, pagamento, pedido ao fornecedor, entrega e comissão. O modelo inicial evita estoque próprio e mantém a execução comercial separada da camada de inteligência.

## Princípios

- Privacy by design e LGPD desde a arquitetura.
- Multi-tenant desde o início.
- Dados identificáveis separados de dados analíticos.
- Auditoria de eventos relevantes.
- API-first.
- Segurança e autorização no servidor.

## Stack

- Backend: Python 3.13+, FastAPI, SQLAlchemy 2, Pydantic v2.
- Banco: PostgreSQL.
- Frontend: React + TypeScript.
- Infra: Docker Compose.
- CI: GitHub Actions.

## Fluxo

Cliente -> Cotação -> Proposta -> Aprovação -> Pagamento -> Pedido ao fornecedor -> Entrega -> Conclusão -> Comissão.

Consulte docs/architecture/overview.md e docs/product/mvp.md.

## Phase 1

Identity, PostgreSQL persistence, Alembic migrations, JWT authentication, multi-tenancy, tenant-scoped RBAC, Docker runtime, and integration tests are implemented.


CI validation: end-to-end finance lifecycle coverage is included in the test suite.
