# Modelo de negócio

O COMPRE atua como camada de intermediação comercial.

1. Cliente solicita cotação.
2. COMPRE consolida fornecedores elegíveis.
3. COMPRE apresenta proposta.
4. Cliente aprova.
5. Pedido é encaminhado ao fornecedor.
6. Fornecedor entrega diretamente ao cliente quando aplicável.
7. COMPRE registra o negócio e calcula a comissão conforme regra contratada.

O COMPRE não precisa possuir estoque para executar o modelo inicial.

## Cadastro do cliente no fornecedor

Estados explícitos: cadastro necessário, cadastro solicitado, cadastro aprovado, cadastro recusado e pedido liberado.

O COMPRE não deve depender de chamadas síncronas do fornecedor para todo o fluxo.