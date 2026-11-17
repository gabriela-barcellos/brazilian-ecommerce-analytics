# Brazilian E-commerce Analytics

Projeto de análise de dados e Business Intelligence desenvolvido a
partir do **Brazilian E-Commerce Public Dataset by Olist**, com foco em
desempenho comercial, comportamento de compra e eficiência logística.

A proposta é transformar dados transacionais em indicadores confiáveis e
análises que ajudem a responder perguntas de negócio --- não apenas
apresentar gráficos.

## Visão geral

O projeto está organizado em três frentes analíticas:

1.  **Comercial:** evolução da receita de produtos, volume de pedidos,
    ticket médio, clientes únicos, categorias, estados e formas de
    pagamento.
2.  **Logística:** tempo de entrega, pontualidade, atrasos e diferenças
    de desempenho entre estados.
3.  **Investigação logística:** relação entre distância, frete, prazo de
    entrega e ocorrência de atrasos.

A dashboard possui filtros de período, estado, categoria e forma de
pagamento na visão comercial.

## Fonte dos dados

**Brazilian E-Commerce Public Dataset by Olist --- Kaggle**

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

O conjunto reúne aproximadamente 100 mil pedidos realizados entre 2016 e
2018 em marketplaces brasileiros. Os dados foram disponibilizados de
forma anonimizada pela Olist. Consulte a página original para conhecer a
licença e as condições de uso do dataset.

Tabelas utilizadas no projeto:

  ------------------------------------------------------------------------
  Arquivo                              Conteúdo utilizado
  ------------------------------------ -----------------------------------
  `olist_orders_dataset.csv`           Status dos pedidos e datas de
                                       compra, entrega e previsão

  `olist_order_items_dataset.csv`      Itens, preços, vendedores e valores
                                       de frete

  `olist_customers_dataset.csv`        Identificação e localização dos
                                       clientes

  `olist_order_payments_dataset.csv`   Formas e valores de pagamento

  `olist_sellers_dataset.csv`          Localização dos vendedores

  `olist_geolocation_dataset.csv`      Coordenadas geográficas associadas
                                       aos CEPs
  ------------------------------------------------------------------------

A disponibilidade de arquivos pode variar conforme a versão baixada do
dataset. Os arquivos originais não devem ser presumidos como parte deste
repositório.

## Tecnologias e recursos

-   **Python / Pandas:** preparação, exploração, cruzamento e auditoria
    dos dados.
-   **HTML, CSS e JavaScript:** estrutura, estilo, filtros e
    interatividade da dashboard.
-   **Plotly.js:** visualizações interativas.
-   **Análise estatística:** correlação de Spearman e cálculo de
    indicadores logísticos.
-   **Git e GitHub:** versionamento e documentação do projeto.

> Inclua SQL no inventário de tecnologias somente se as consultas SQL
> fizerem parte efetiva da versão publicada do projeto. A documentação
> deve refletir o que está implementado e pode ser demonstrado.

## Estrutura analítica

### 1. Visão comercial

Indicadores apresentados:

-   **Receita de produtos:** soma de `price` dos itens. O valor não
    inclui frete.
-   **Pedidos:** quantidade distinta de pedidos presentes na base de
    itens após a aplicação dos filtros.
-   **Ticket médio:** receita de produtos dividida pela quantidade
    distinta de pedidos.
-   **Clientes únicos:** quantidade distinta de identificadores de
    clientes únicos.
-   **Receita por mês, categoria e estado:** agregações da receita de
    produtos.
-   **Participação por forma de pagamento:** distribuição dos valores
    registrados na tabela de pagamentos.

#### Regra do filtro de pagamento

O filtro identifica os pedidos que possuem ao menos um registro da forma
de pagamento selecionada. Depois, considera todos os itens desses
pedidos para calcular a receita.

Um mesmo pedido pode possuir mais de uma forma de pagamento. Portanto,
ele pode aparecer em mais de uma seleção de pagamento; os resultados por
forma de pagamento não devem ser somados como se fossem grupos
mutuamente exclusivos.

#### Período parcial

Setembro de 2018 possui registros somente até 03/09 e é tratado como
período parcial. Agosto de 2018 é o último mês completo utilizado nas
comparações mensais.

### 2. Desempenho logístico

A análise considera pedidos com status `delivered` e datas válidas de
entrega.

  Indicador                                   Resultado auditado
  ----------------------------------------- --------------------
  Pedidos entregues com data válida                       96.470
  Tempo médio entre compra e entrega                  12,56 dias
  Mediana do tempo de entrega                         10,22 dias
  Entregas até a data estimada                            91,89%
  Entregas após a data estimada                            8,11%
  Antecipação média em relação à previsão             11,18 dias

**Critérios:**

-   Tempo de entrega = data de entrega ao cliente − data de compra.
-   Entrega no prazo = data real de entrega menor ou igual à data
    estimada.
-   Atraso = data real de entrega posterior à data estimada.

Há 96.478 pedidos com status `delivered` na base, mas 8 não possuem data
real de entrega. Por isso, esses 8 pedidos não entram nos indicadores de
duração e pontualidade.

### 3. Investigação logística: distância, frete e atrasos

A distância entre vendedor e cliente é aproximada em linha reta usando a
fórmula de Haversine, com coordenadas representativas dos prefixos de
CEP.

Para pedidos com itens de mais de um vendedor, é utilizada a distância
média dos itens do pedido.

**Cobertura da análise geográfica:**

-   95.994 pedidos entregues com coordenadas disponíveis.
-   112.096 de 112.650 linhas de itens com geolocalização,
    aproximadamente 99,51%.

#### Distância e prazo de entrega

  --------------------------------------------------------------------------
  Faixa de              Pedidos    Prazo médio Taxa de atraso    Frete médio
  distância                                                   
  -------------- -------------- -------------- -------------- --------------
  Até 100 km             17.823      6,51 dias          6,43%      R\$ 13,35

  100--300 km            13.429      9,96 dias          6,37%      R\$ 18,83

  300--600 km            31.483     12,63 dias          7,77%      R\$ 22,39

  600--1.000 km          17.919     14,72 dias          8,45%      R\$ 24,85

  1.000--2.000            9.725     17,95 dias         10,76%      R\$ 33,09
  km                                                          

  Acima de 2.000          5.615     21,18 dias         13,66%      R\$ 39,88
  km                                                          
  --------------------------------------------------------------------------

#### Correlação

-   Distância e tempo de entrega: **Spearman = 0,543**, associação
    positiva moderada.
-   Distância e diferença entre entrega real e estimada: **Spearman =
    −0,179**, associação negativa fraca.

A leitura é que distâncias maiores estão associadas a prazos de entrega
mais longos. Já a associação fraca e negativa entre distância e
diferença em relação à previsão não significa que a distância reduza
atrasos: a previsão de entrega pode variar de acordo com a distância e
outras condições operacionais.

#### Estados com maiores taxas de atraso

Entre os estados destacados na análise:

  Estado     Taxa de atraso
  -------- ----------------
  AL                 23,93%
  MA                 19,67%
  PI                 15,97%
  CE                 15,32%
  SE                 15,22%
  BA                 14,04%
  RJ                 13,47%
  TO                 12,77%

As taxas devem ser interpretadas considerando também o volume de pedidos
de cada estado.

## Auditoria e confiabilidade dos indicadores

A validação dos indicadores foi feita por recálculo a partir dos
arquivos transacionais originais, comparando os resultados agregados com
os valores apresentados na dashboard.

Pontos verificados:

-   Receita de produtos reconciliada com a soma dos preços dos itens.
-   Quantidade de pedidos e clientes calculada com identificadores
    distintos.
-   Indicadores logísticos recalculados a partir das datas de compra,
    entrega e previsão.
-   Indicadores mensais e taxas por estado comparados com a base.
-   Faixas de distância, frete médio, prazo e taxa de atraso
    recalculados.
-   Filtro de pagamento ajustado para selecionar pedidos pela tabela de
    pagamentos e preservar todos os itens dos pedidos selecionados.

A auditoria é parte do projeto: os indicadores devem ter definições
claras, denominadores explícitos e limitações documentadas.

## Limitações e cuidados de interpretação

-   Os dados representam o período de 2016 a 2018; não descrevem o
    cenário atual do comércio eletrônico brasileiro.
-   Setembro de 2018 é parcial e não deve ser comparado diretamente a
    meses completos.
-   Oito pedidos entregues sem data real de entrega foram excluídos dos
    cálculos de duração e pontualidade.
-   A análise geográfica depende da disponibilidade e qualidade dos CEPs
    e coordenadas.
-   A distância calculada é uma aproximação em linha reta, não a
    distância real percorrida pelo transporte.
-   Correlação não demonstra causalidade.
-   Pedidos com múltiplas formas de pagamento podem aparecer em mais de
    um filtro de pagamento.

## Como reproduzir

1.  Baixe o dataset original na página da [Olist no
    Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
2.  Organize os arquivos CSV localmente, mantendo os nomes originais.
3.  Execute as etapas de preparação e análise utilizadas no projeto.
4.  Abra o arquivo HTML da dashboard em um navegador com acesso à
    internet, pois a biblioteca Plotly.js é carregada por CDN.

> Os caminhos locais dos arquivos e eventuais scripts de preparação
> devem ser ajustados à estrutura final do repositório antes da
> publicação.

## Próximos passos

-   Publicar a estrutura final do projeto e os arquivos necessários para
    reprodução.
-   Adicionar um dicionário de dados e documentar as etapas de
    transformação.
-   Registrar consultas SQL e scripts Python utilizados na preparação e
    auditoria, quando aplicável.
-   Incluir capturas de tela da dashboard no README.
-   Descrever decisões analíticas e oportunidades de negócio
    identificadas.

## Créditos

Dados: **Olist --- Brazilian E-Commerce Public Dataset**,
disponibilizado no Kaggle.

Este é um projeto independente de estudo e portfólio, sem vínculo com a
Olist.
