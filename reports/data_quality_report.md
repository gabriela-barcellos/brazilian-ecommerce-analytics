# Data Quality Report — Brazilian E-commerce (Olist)

## 1. Objetivo e escopo

Este relatório consolida a inspeção inicial e as validações de qualidade realizadas sobre o Brazilian E-Commerce Public Dataset, disponibilizado pela Olist. A análise cobre inventário, estrutura, valores ausentes, unicidade de chaves, integridade referencial, cardinalidade, regras de negócio e consistência temporal.

Foram inspecionados os nove arquivos CSV do conjunto de dados.

## 2. Inventário dos dados

| Dataset | Registros | Colunas |
|---|---:|---:|
| customers | 99.441 | 5 |
| geolocation | 1.000.163 | 5 |
| order_items | 112.650 | 7 |
| order_payments | 103.886 | 5 |
| order_reviews | 99.224 | 7 |
| orders | 99.441 | 8 |
| products | 32.951 | 9 |
| sellers | 3.095 | 4 |
| product_category_name_translation | 71 | 2 |
| **Total** | **1.650.922** | — |

## 3. Valores ausentes

- **order_reviews:** `review_comment_title` possui 87.656 valores ausentes; `review_comment_message`, 58.247. Os campos de comentário são opcionais e a ausência não invalida a avaliação numérica.
- **orders:** 160 ausências em `order_approved_at`, 1.783 em `order_delivered_carrier_date` e 2.965 em `order_delivered_customer_date`. As ausências podem estar relacionadas ao estado ou ao fluxo do pedido e devem ser preservadas e interpretadas no contexto.
- **products:** 610 registros sem categoria, nome, descrição ou informações de imagem associadas; duas ausências em cada atributo físico de peso e dimensões.
- **Demais datasets:** não foram identificados valores ausentes nas inspeções realizadas.

Não foi aplicada imputação ou exclusão automática nesta etapa.

## 4. Unicidade e chaves

- `customers.customer_id`: sem duplicidades.
- `orders.order_id`: sem duplicidades.
- `order_items`: combinação (`order_id`, `order_item_id`) sem duplicidades.
- `order_payments`: combinação (`order_id`, `payment_sequential`) sem duplicidades.
- `products.product_id` e `sellers.seller_id`: sem duplicidades.
- `order_reviews.review_id`: 789 IDs repetidos (814 ocorrências duplicadas reportadas na validação). Entretanto, a combinação (`review_id`, `order_id`) é única. Portanto, `review_id` isoladamente não deve ser assumido como chave única sem uma regra adicional; a granularidade da avaliação deve ser respeitada.

## 5. Integridade referencial

- `orders.customer_id` → `customers.customer_id`: 99.441 correspondências; nenhum órfão.
- `order_items.product_id` → `products.product_id`: 112.650 correspondências; nenhum órfão.
- `order_items.seller_id` → `sellers.seller_id`: 112.650 correspondências; nenhum órfão.
- Pedidos e itens: 98.666 pedidos possuem itens; 775 não possuem. Entre estes, 603 estão indisponíveis, 164 cancelados, 5 criados, 2 faturados e 1 enviado.
- Pedidos e pagamentos: 99.441 pedidos; um pedido sem pagamento; nenhum pagamento sem pedido.
- Pedidos e avaliações: 768 pedidos sem avaliação; nenhuma avaliação sem pedido.

O pedido com status `shipped` sem item associado merece investigação específica em etapa posterior, sem correção automática.

## 6. Cardinalidade e risco de JOIN

- Pedidos: 99.441; itens: 112.650; pagamentos: 103.886.
- Entre os 98.666 pedidos com itens, a média é 1,1417 item por pedido (mediana 1; máximo 21).
- Entre os 99.440 pedidos com pagamento, a média é 1,0447 pagamento por pedido (mediana 1; máximo 29).

Um JOIN direto entre itens e pagamentos pela chave `order_id` produziu 117.601 linhas, acima das 112.650 linhas originais de itens. O valor de itens passou de R$ 13.591.643,70 para R$ 14.209.115,34 (inflação aproximada de 1,05x).

**Conclusão:** a relação entre pedidos, itens e pagamentos pode ser 1:N em mais de uma tabela. Antes de combinar essas tabelas, agregue cada conjunto na granularidade desejada ou utilize um modelo que preserve a cardinalidade. A soma de valores após JOIN deve ser validada contra os valores de origem.

Após agregação, foram combinados 98.665 pedidos; receita de itens agregada de R$ 13.591.508,73 e pagamentos de R$ 15.846.280,17. Esses valores refletem o subconjunto combinado, não o total irrestrito das tabelas.

## 7. Regras de negócio e valores suspeitos

### Itens
- Quantidade de item (`order_item_id`) menor ou igual a zero: 0.
- Preços negativos ou iguais a zero: 0.
- Frete negativo: 0; frete igual a zero: 383 registros.
- Preço: média R$ 120,65; mediana R$ 74,99; mínimo R$ 0,85; máximo R$ 6.735,00.
- Frete: média R$ 19,99; mediana R$ 16,26; mínimo R$ 0,00; máximo R$ 409,68.

### Pagamentos
- Valores negativos: 0; valores iguais a zero: 9.
- Parcelas menores que 1: 2 registros.
- Tipos: credit_card 76.795; boleto 19.784; voucher 5.775; debit_card 1.529; not_defined 3.
- Valor: média R$ 154,10; mediana R$ 100,00; mínimo R$ 0,00; máximo R$ 13.664,08.
- Parcelas: média 2,85; mediana 1; mínimo 0; máximo 24.

Os nove pagamentos de valor zero incluem seis vouchers e três registros `not_defined`. Dois registros de cartão de crédito possuem zero parcelas, com valores de R$ 58,69 e R$ 129,94. São ocorrências suspeitas a documentar, não evidência suficiente para exclusão ou correção.

### Avaliações
- Scores fora do intervalo esperado: 0.
- Distribuição: nota 1 (11.424), nota 2 (3.151), nota 3 (8.179), nota 4 (19.142), nota 5 (57.328).

### Produtos
- Peso ou dimensões negativos: 0.
- Peso igual a zero: 4 registros.
- Dimensões iguais a zero: 0.

### Pedidos
- Status observados: delivered 96.478; shipped 1.107; canceled 625; unavailable 609; invoiced 314; processing 301; created 5; approved 2.
- Status não reconhecidos: 0.
- Pedidos cancelados com data de entrega ao cliente: 6; com data de transporte: 75.

## 8. Consistência temporal

- Entrega anterior à compra: 0.
- Aprovação anterior à compra: 0.
- 61 pedidos apresentam entrega anterior à aprovação registrada; os casos devem ser investigados considerando possíveis inconsistências ou particularidades do registro.
- Entre pedidos entregues com comparação disponível, 7.827 foram entregues após a data estimada e 88.649 no prazo.

## 9. Conclusões e encaminhamentos

A estrutura apresenta chaves e relacionamentos principais consistentes, sem registros órfãos nas relações centrais avaliadas. Os principais pontos de atenção são:

1. Valores ausentes em comentários de avaliações, timestamps de pedidos e atributos de produtos.
2. `review_id` repetido, exigindo cuidado com a granularidade.
3. Pedidos sem itens ou pagamentos e um pedido enviado sem item.
4. Pagamentos com valor zero ou número de parcelas zero.
5. Divergências temporais em 61 pedidos.
6. Risco de duplicação de valores em JOINs entre tabelas com relações 1:N.

**Recomendação:** preservar os dados originais, registrar as ocorrências e definir regras explícitas de tratamento durante a etapa de engenharia de dados. Nenhuma correção ou exclusão automática foi realizada nesta análise.

## 10. Escopo desta etapa

Este documento encerra a consolidação da etapa de Data Discovery & Data Quality Assessment. Ainda não contempla pipeline ETL, modelagem dimensional, camada analítica ou dashboard; essas atividades pertencem às próximas fases do projeto.
