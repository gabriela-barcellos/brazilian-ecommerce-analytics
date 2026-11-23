# Brazilian E-commerce — Engenharia de Dados + Analytics

Projeto de portfólio construído sobre o **Brazilian E-Commerce Public
Dataset by Olist**. Os CSVs brutos passam por um pipeline em camadas no
**PostgreSQL** (Bronze → Silver → Gold), com auditoria de execuções e
verificações automáticas de qualidade. O modelo dimensional resultante é
servido por uma **API FastAPI** e consumido por uma **dashboard
HTML/JavaScript** com Plotly.

A proposta é transformar dados transacionais em indicadores confiáveis,
com definições claras, reconciliação contra resultados auditados e
limitações documentadas — não apenas apresentar gráficos.

## Arquitetura

```text
CSV Olist (data/raw)
   │  Scripts/ingestion.py            COPY direto, sem Pandas; truncate-and-reload
   ▼
PostgreSQL · bronze   dados brutos preservados (TEXT) + metadados de carga
   │  Scripts/silver_transformation.py + sql/silver/*.sql
   ▼
PostgreSQL · silver   tipado, padronizado, PK/FK/CHECK; nenhuma linha descartada
   │  Scripts/gold_build.py + sql/gold/*.sql
   ▼
PostgreSQL · gold     star schema + tabelas de apoio
   │  Scripts/quality_checks.py       77 verificações (críticas interrompem o pipeline)
   ▼
FastAPI (api/)        KPIs, filtros e séries dos gráficos
   ▼
dashboard_integrated.html   HTML + JavaScript + Plotly.js
```

Toda execução fica registrada no schema `control`:
`pipeline_runs` (uma linha por execução), `dataset_loads` (contagem
origem × destino por tabela) e `quality_results` (resultado de cada
verificação).

## Tecnologias

| Camada | Ferramentas |
|---|---|
| Ingestão e transformação | Python 3.14, psycopg 3 (`COPY`), SQL |
| Banco de dados | PostgreSQL 18 (schemas `bronze`, `silver`, `gold`, `control`) |
| Qualidade | Verificações SQL automatizadas, gravadas em `control.quality_results` |
| API | FastAPI + Uvicorn |
| Visualização | HTML, CSS, JavaScript, Plotly.js 2.35.2 (CDN) |
| Análise exploratória (1ª versão) | Pandas |
| Versionamento | Git e GitHub |

**Por que psycopg e não SQLAlchemy:** a ingestão usa `COPY` (a forma
nativa e mais rápida de carregar CSV no PostgreSQL, ~1 milhão de linhas
de geolocalização) e as transformações são SQL puro. Um ORM não traria
benefício aqui.

## Estrutura do repositório

```text
├── api/
│   ├── main.py                 rotas FastAPI
│   └── queries.py              consultas SQL sobre a Gold
├── Scripts/
│   ├── db.py                   conexão (lê DATABASE_URL do .env)
│   ├── ingestion.py            CSV -> bronze
│   ├── silver_transformation.py
│   ├── gold_build.py
│   ├── quality_checks.py
│   ├── run_pipeline.py         orquestra bronze -> silver -> gold -> qualidade
│   ├── test_connection.py      teste da conexão
│   ├── test_api.py             testes da API (46 verificações)
│   ├── build_integrated_dashboard.py
│   └── ...                     scripts Pandas da 1ª versão (ver abaixo)
├── sql/
│   ├── 01_postgresql_foundation.sql   schemas, controle e Bronze
│   ├── 03_silver_tables.sql           tabelas Silver
│   ├── 05_gold_tables.sql             star schema
│   ├── 07_quality_tables.sql          resultados de qualidade
│   ├── 00/02/04/06_check_*.sql        consultas de conferência por camada
│   ├── silver/01..09_*.sql            uma transformação por tabela
│   └── gold/01..09_*.sql              uma carga por tabela
├── reports/                    inventário, inspeção de schema e relatório de qualidade
├── dashboard.html              dashboard original (dados embutidos, ~44 MB)
├── dashboard_integrated.html   mesma dashboard consumindo a API (~29 KB)
├── requirements.txt
└── .env.example                modelo da variável DATABASE_URL
```

Os CSVs (`data/`) e o `.env` não são versionados.

## Modelo dimensional (Gold)

| Tabela | Granularidade | Observação |
|---|---|---|
| `fact_sales` | 1 linha por **item** do pedido (todos os status) | `price` = receita de produtos |
| `fact_payments` | 1 linha por **pagamento** | separada de `fact_sales` |
| `fact_order_delivery` | 1 linha por pedido `delivered` com data real (96.470) | prazo, atraso, frete, distância |
| `dim_date` | 1 linha por dia (774) | calendário contínuo |
| `dim_customer` | 1 linha por `customer_id` | inclui `customer_unique_id` e coordenadas |
| `dim_product` | 1 linha por produto | categoria, rótulo e tradução |
| `dim_seller` | 1 linha por vendedor | inclui coordenadas |
| `zip_prefix_location` | 1 linha por prefixo de CEP | coordenada representativa |
| `agg_order_status` | 1 linha por status | todos os 99.441 pedidos |

Chaves naturais da Olist (hashes estáveis) são usadas como chaves do
modelo, com `PRIMARY KEY` e `FOREIGN KEY` explícitas.

**Itens e pagamentos nunca são unidos para somar receita.** As
granularidades são diferentes: o JOIN direto produz 117.601 linhas em vez
de 112.650 e infla a receita para R$ 14.209.115,34 (≈ 1,05×). O filtro por
forma de pagamento usa um semi-join (`order_id IN (...)`) em
`fact_payments`.

## Regras de negócio

### Comercial

- **Receita de produtos:** soma de `price` dos itens; não inclui frete.
- **Pedidos:** quantidade distinta de `order_id` na base de itens.
- **Ticket médio:** receita de produtos ÷ pedidos distintos.
- **Clientes únicos:** quantidade distinta de `customer_unique_id`.
- **Filtro de pagamento:** seleciona os pedidos com **ao menos um**
  pagamento do tipo escolhido e considera todos os itens desses pedidos.
  Um pedido pode ter mais de uma forma de pagamento, então os resultados
  por forma de pagamento **não** são grupos mutuamente exclusivos.
- **Período parcial:** setembro de 2018 tem registros só até 03/09 e fica
  fora das comparações mensais; agosto de 2018 é o último mês completo.

### Logística

A análise considera pedidos `delivered` com data real de entrega.

| Indicador | Resultado auditado |
|---|---:|
| Pedidos entregues com data válida | 96.470 |
| Tempo médio entre compra e entrega | 12,56 dias |
| Mediana do tempo de entrega | 10,22 dias |
| Entregas até a data estimada | 91,89% |
| Entregas após a data estimada | 8,11% |
| Antecipação média em relação à previsão | 11,18 dias |

- Tempo de entrega = data de entrega ao cliente − data de compra.
- No prazo = entrega real ≤ data estimada (data **e** hora).
- Há 96.478 pedidos `delivered`; 8 não têm data real de entrega e ficam
  fora dos indicadores de duração e pontualidade.

### Investigação: distância, frete e atrasos

A distância vendedor–cliente é aproximada em linha reta pela fórmula de
Haversine (raio 6.371 km), usando como coordenada de cada prefixo de CEP
a **mediana** dos pontos de geolocalização. Em pedidos com itens de mais
de um vendedor, usa-se a **distância média** dos itens.

Cobertura: 95.994 pedidos entregues com coordenadas; 112.096 de 112.650
itens (≈ 99,51%) com geolocalização de cliente e vendedor.

| Faixa de distância | Pedidos | Prazo médio | Taxa de atraso | Frete médio |
|---|---:|---:|---:|---:|
| Até 100 km | 17.823 | 6,51 dias | 6,43% | R$ 13,35 |
| 100–300 km | 13.429 | 9,96 dias | 6,37% | R$ 18,83 |
| 300–600 km | 31.483 | 12,63 dias | 7,77% | R$ 22,39 |
| 600–1.000 km | 17.919 | 14,72 dias | 8,45% | R$ 24,85 |
| 1.000–2.000 km | 9.725 | 17,95 dias | 10,76% | R$ 33,09 |
| Acima de 2.000 km | 5.615 | 21,18 dias | 13,66% | R$ 39,88 |

Correlação de Spearman:

- Distância × tempo de entrega: **0,543** (associação positiva moderada).
- Distância × (entrega real − estimada): **−0,179** (associação negativa
  fraca).

Distâncias maiores estão associadas a prazos mais longos. A associação
fraca e negativa com a diferença em relação à previsão não significa que
a distância reduza atrasos: a própria previsão já varia com a distância e
com outras condições operacionais.

Estados com maiores taxas de atraso: AL 23,93% · MA 19,67% · PI 15,97% ·
CE 15,32% · SE 15,22% · BA 14,04% · RJ 13,47% · TO 12,77%. As taxas devem
ser lidas junto com o volume de pedidos de cada estado.

## Qualidade e auditoria

`Scripts/quality_checks.py` executa 77 verificações sobre as três camadas
e grava cada resultado em `control.quality_results`.

- **Críticas** (falha interrompe o pipeline): contagem da origem; Silver
  sem perda de linhas; chaves duplicadas e registros órfãos; preço,
  frete, pagamento e nota válidos; datas impossíveis; receita e
  pagamentos da Gold iguais aos da Silver (proteção contra JOIN que
  duplica valores); todos os indicadores auditados acima, inclusive as
  faixas da página de investigação.
- **Alertas** (registrados, não interrompem): ocorrências conhecidas do
  relatório de qualidade — 775 pedidos sem itens, 789 `review_id`
  repetidos, 9 pagamentos com valor zero, 61 entregas registradas antes
  da aprovação, 42 coordenadas fora do Brasil, entre outras. Se algum
  desses números mudar, o pipeline sinaliza.

Decisões de tratamento na Silver: nenhuma linha é excluída; nulos são
preservados; CEP é mantido como texto de 5 dígitos (preserva o zero à
esquerda); `review_id` não é chave única sozinho — a chave é
(`review_id`, `order_id`); colunas `*_lenght` da origem viram
`*_length`.

Detalhes da avaliação inicial em
[`reports/data_quality_report.md`](reports/data_quality_report.md).

## API

| Endpoint | Conteúdo |
|---|---|
| `GET /api/health` | banco acessível, última execução de cada camada e último resultado de qualidade |
| `GET /api/filters` | opções dos filtros (meses, estados, categorias, pagamentos) |
| `GET /api/commercial` | KPIs, comparação com o mês anterior, série mensal, ranking de categorias e estados, participação dos pagamentos. Parâmetros: `period`, `state`, `category`, `payment`, `top` |
| `GET /api/logistics` | KPIs de entrega, evolução mensal, estados com menor pontualidade, status dos pedidos |
| `GET /api/investigation` | Spearman, faixas de distância e de frete, estados com mais atraso |

Documentação interativa em `http://127.0.0.1:8000/docs`.

## Como reproduzir (Windows / PowerShell)

Pré-requisitos: Python 3.11+ e PostgreSQL instalados.

1. Baixe o dataset na [página da Olist no
   Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) e
   coloque os 9 CSVs, com os nomes originais, em `data/raw/`.

2. Crie o ambiente e instale as dependências:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Configure a conexão: copie `.env.example` para `.env` e preencha a
   senha do PostgreSQL (o `.env` não é versionado).

   ```powershell
   Copy-Item .env.example .env
   ```

4. Crie o banco e as tabelas:

   ```powershell
   psql -U postgres -c "CREATE DATABASE brazilian_ecommerce;"
   psql -U postgres -d brazilian_ecommerce -f sql\01_postgresql_foundation.sql
   psql -U postgres -d brazilian_ecommerce -f sql\03_silver_tables.sql
   psql -U postgres -d brazilian_ecommerce -f sql\05_gold_tables.sql
   psql -U postgres -d brazilian_ecommerce -f sql\07_quality_tables.sql
   python Scripts\test_connection.py
   ```

5. Execute o pipeline completo (≈ 3 a 4 minutos):

   ```powershell
   python Scripts\run_pipeline.py
   ```

   Para retomar a partir de uma etapa: `--from silver`, `--from gold` ou
   `--from quality`.

6. Suba a API e, em outro terminal, rode os testes:

   ```powershell
   uvicorn api.main:app --reload
   python Scripts\test_api.py
   ```

7. Com a API rodando, abra `dashboard_integrated.html` no navegador
   (é necessário acesso à internet para carregar o Plotly.js pela CDN).
   Para usar outra URL da API: `dashboard_integrated.html?api=http://host:porta`.

## Duas versões da dashboard

- **`dashboard.html`** — versão original, autocontida: os dados estão
  embutidos no arquivo e ela abre sem banco nem API.
- **`dashboard_integrated.html`** — mesmo layout, tema, gráficos e
  filtros, com os dados vindos da API. É gerada a partir da original por
  `Scripts/build_integrated_dashboard.py`, sem alterá-la. Diferenças em
  relação à original, ambas correções:
  - a comparação com o mês anterior aplica a mesma regra de pagamento do
    filtro principal;
  - o percentual de pedidos entregues é 97,0% (96.478 de 99.441); a
    original mostrava 97,8%.

## Decisões técnicas

- **Bronze em TEXT:** preserva exatamente o conteúdo dos CSVs; tipagem e
  validação acontecem na Silver.
- **Recarga idempotente:** cada camada é recarregada dentro de uma
  transação (truncate-and-reload). Se algo falha, a versão anterior é
  mantida e a falha fica registrada em `control.pipeline_runs`.
- **Coordenada por CEP e distância por pedido:** a análise original não
  tinha o código do cálculo salvo. O critério (mediana por prefixo de CEP
  + média das distâncias dos itens) foi identificado testando 64
  combinações contra os valores publicados na dashboard; é o único que
  reproduz todos eles.
- **Calendário sem fuso horário:** `dim_date` é gerada com `DATE + inteiro`,
  porque séries com `INTERVAL` em `timestamptz` pulam dias de início do
  horário de verão brasileiro (2016–2018).
- **Orquestração simples:** `run_pipeline.py` executa as etapas em ordem
  e para na primeira falha. Para um dataset estático, um orquestrador
  como o Airflow não traria benefício proporcional à complexidade.

## Primeira versão (Pandas / CSV)

A análise começou em Pandas, gerando CSVs em `data/processed` e
`data/analytics`. Esses scripts continuam no repositório como histórico:
`transformation.py`, `analytics_model.py`, `analytics_dimensions.py`,
`analytics_metrics.py` e os scripts de validação (`*_validation.py`,
`schema_inspection.py`, `inventory.py`, `join_impact_analysis.py`). A
lógica de validação deles foi portada para `quality_checks.py`, que roda
direto no banco.

## Limitações e cuidados de interpretação

- Os dados cobrem 2016 a 2018 e não descrevem o cenário atual do
  e-commerce brasileiro.
- Setembro de 2018 é parcial e não deve ser comparado a meses completos.
- Oito pedidos entregues sem data real de entrega ficam fora dos cálculos
  de duração e pontualidade.
- A análise geográfica depende da qualidade dos CEPs e coordenadas; a
  distância é uma aproximação em linha reta, não o trajeto real.
- Correlação não demonstra causalidade.
- Pedidos com várias formas de pagamento aparecem em mais de um filtro
  de pagamento.

## Próximos passos

- Docker Compose para subir PostgreSQL, pipeline e API com um comando.
- Capturas de tela da dashboard neste README.
- Dicionário de dados das camadas Silver e Gold.

## Créditos

Dados: **Olist — Brazilian E-Commerce Public Dataset**, disponibilizado no
[Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

Projeto independente de estudo e portfólio, sem vínculo com a Olist.
