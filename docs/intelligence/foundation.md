# Fase 4 — Fundação de Inteligência

## Objetivo

Transformar eventos operacionais em métricas de mercado sem permitir que a camada de inteligência precise consultar diretamente dados pessoais, comerciais identificáveis ou credenciais financeiras.

## Camadas

```text
Domínio
  ↓
DomainEvent / AuditLog
  ↓
Transformação e minimização
  ↓
AnalyticsEvent
  ↓
Agregação com limiar mínimo
  ↓
MarketMetric
  ↓
Produtos de inteligência
```

## AnalyticsEvent

Um evento analítico contém somente tenant técnico de origem, referência opcional ao evento de domínio, chave da métrica, chave de escopo canônica, valor numérico, unidade, moeda e timestamp.

Não há nome, e-mail, telefone, endereço, documento, texto livre ou JSON arbitrário.

## MarketMetric

A métrica publicada é agregada por período e escopo. A fundação exige, por padrão, dados provenientes de pelo menos **3 tenants distintos** antes de produzir uma métrica de mercado.

Isso reduz o risco de transformar o comportamento de uma única empresa em informação comercial identificável.

## Regras

1. A camada de inteligência não consulta tabelas de clientes, usuários ou fornecedores para gerar métricas.
2. O evento analítico deve ser minimizado antes de entrar nessa camada.
3. Chaves de escopo devem ser canônicas e não conter PII.
4. Métricas abaixo do limiar de diversidade de tenants não são publicadas.
5. Dados financeiros brutos e credenciais de pagamento permanecem fora dessa camada.
6. Agregações futuras devem preservar período, unidade e moeda.

## Primeiros produtos possíveis

- índice de preço por categoria/produto normalizado;
- tendência de preço;
- benchmark de prazo de entrega;
- indicador agregado de disponibilidade;
- frequência agregada de compra;
- benchmark de economia obtida.

## Próxima etapa

Criar produtores de `AnalyticsEvent` a partir de eventos de domínio específicos, começando por preço e prazo de entrega, e depois materializar séries históricas por período.