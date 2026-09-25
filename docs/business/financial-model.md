# Modelo financeiro — Fase 3

## Objetivo

A Fase 3 separa quatro conceitos que não devem ser misturados:

1. **Pagamento** — registro de uma obrigação financeira do cliente e seu estado de liquidação.
2. **Comissão** — receita da COMPRE calculada sobre um pedido.
3. **Repasse (settlement)** — valor líquido devido ao fornecedor.
4. **Conciliação** — confirmação de que os registros internos correspondem ao pagamento/repasse externo.

A COMPRE não armazena dados de cartão, CVV ou credenciais de pagamento. Apenas referências externas e metadados mínimos são persistidos.

## Fluxo

```
Pedido concluído/comercialmente elegível
        |
        v
Snapshot financeiro
  bruto / comissão / líquido fornecedor
        |
        +--> Pagamento do cliente
        |
        +--> Comissão COMPRE
        |
        +--> Repasse ao fornecedor
        |
        v
Conciliação
```

O modelo não presume que o dinheiro passe pela COMPRE. O pagamento possui `flow` explícito, permitindo representar tanto pagamento cliente→COMPRE quanto cliente→fornecedor.

## Snapshot financeiro

Cada pedido possui no máximo um `order_financials`. Ele congela os valores utilizados para a operação financeira:

- `gross_amount`
- `commission_amount`
- `supplier_net_amount`
- `currency`
- taxa percentual aplicada
- valor fixo aplicado

O cálculo é feito no servidor. Depois de confirmado, o snapshot não deve ser recalculado silenciosamente; alterações futuras devem ser tratadas como ajustes.

## Comissão

`commission_rules` permite definir uma regra percentual e/ou fixa. A regra aplicada é copiada para o snapshot da comissão, preservando histórico mesmo se a regra original for alterada.

Estados:

`pending -> generated -> approved -> paid`

Uma comissão pode ser revertida posteriormente por evento/ajuste, sem apagar histórico.

## Pagamentos

Estados suportados:

- `pending`
- `authorized`
- `paid`
- `failed`
- `cancelled`
- `refunded`
- `partially_refunded`

O campo `provider_reference` identifica a transação no provedor sem armazenar dados sensíveis do instrumento.

## Repasse

O settlement representa o valor líquido devido ao fornecedor e possui estados:

`pending -> scheduled -> paid -> failed -> reconciled`

O valor do repasse é derivado do snapshot financeiro, não de entrada fornecida pelo cliente.

## Conciliação e idempotência

Pagamentos, comissões e repasses possuem referências externas opcionais e eventos idempotentes. Nenhuma operação financeira deve depender de duplicação acidental de requisições.

## LGPD e segurança

- Nunca armazenar PAN, CVV, senha bancária ou token secreto de provedor.
- Minimizar dados pessoais.
- Separar dados financeiros operacionais da camada de inteligência.
- Eventos e auditoria devem registrar identificadores técnicos e valores necessários, evitando dados pessoais desnecessários.

## Evolução planejada

A Fase 3 inicial não implementa gateway de pagamento nem contabilidade completa. Ela cria o núcleo transacional para posteriormente conectar PSPs, PIX, boleto, ERP financeiro e processos de conciliação.
