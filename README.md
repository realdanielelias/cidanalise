# CidAnalise (nome temporario ate pensar num melhor)

Pipeline de dados em Python e Docker para extrair, filtrar e analisar dados fiscais e orçamentários de municípios brasileiros diretamente da API do Siconfi.

O foco inicial do projeto é a análise das despesas ligadas à **Educação** utilizando os relatórios RREO e DCA.

## Ferramentas usadas

- **Docker**
- **Python 3.13-slim** (python:3.13-slim)
- **PostgreSQL 15** (postgres:15)


## Estrutura atual

```text
CidAnalise/
├── db-sql/               # Dados que persistem do PostgreSQL (Ignorado pelo Git)
├── mining/               # Extração de dados (Python)
│   ├── data/
│   │   ├── input/        # Arquivos de entrada/configuração
│   │   └── output/       # JSONs extraídos da API (Ignorados pelo Git)
│   ├── src/
│   │   └── mining.py     # Script principal
│   └── requirements.txt
├── .gitignore
├── docker-compose.yml
└── README.md

## Para testes:

Sobrescrever arquivoss config.json e municipios .json pelo codigo do ente no IBGE e outros parametros para RREO e DCA presentes na pagina: https://apidatalake.tesouro.gov.br/docs/siconfi/

Valores padrao sao o ultimo bimestre de 2025 e os municipios de Marilia, Bauru e Presidente Prudente.