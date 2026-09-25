# Segurança e LGPD

## Controles do MVP

- Hash de senha com algoritmo apropriado.
- Segredos somente via ambiente/secret manager.
- JWT de curta duração e renovação segura.
- RBAC no backend.
- Validação de tenant em toda operação.
- Logs sem senha, token ou dados sensíveis desnecessários.
- Auditoria de ações administrativas e financeiras.
- Criptografia em trânsito.
- Backups e política de retenção.
- Rate limiting nos endpoints sensíveis.
- Validação de uploads e documentos.

## LGPD by design

Separar dados necessários para execução do contrato, segurança/auditoria, dados opcionais e dados destinados a analytics.

Produtos de inteligência devem preferir métricas agregadas, intervalos, categorias e estatísticas derivadas, evitando exposição de cliente, fornecedor ou pessoa identificável.

A base legal, retenção, finalidade, direitos do titular e processos de atendimento devem ser definidos antes da operação em produção. Este documento é arquitetural e não substitui revisão jurídica.