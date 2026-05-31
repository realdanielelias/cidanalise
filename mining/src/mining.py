import json
import os
import sys
import time
import requests
from pathlib import Path
import psycopg2

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / 'data' / 'input'
OUTPUT_DIR = BASE_DIR / 'data' / 'output'

def extrair_siconfi(endpoint_name, url, params=None):
    print(f"[ETL] Iniciando extracao do endpoint: {endpoint_name}...")
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            dados = response.json()
            registros = dados.get('items', [])
            print(f"[ETL] {endpoint_name} extraido com sucesso! {len(registros)} registros encontrados.")
            
            # Captura o ID do ente e o ano para criar um nome unico
            id_ente = params.get('id_ente', 'geral') if params else 'geral'
            ano = params.get('an_exercicio', '') if params else ''
            filename = OUTPUT_DIR / f"dados_{endpoint_name.lower()}_{id_ente}_{ano}.json"
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
                
            print(f"[ETL] Arquivo salvo em: {filename}")
            return registros
        else:
            print(f"[ETL] Erro na API no endpoint {endpoint_name}. Status: {response.status_code}")
            return []
    except Exception as e:
        print(f"[ETL] Falha de conexao em {endpoint_name}: {e}")
        return []

def salvar_no_banco(dados, codigo_ibge, ano, periodo):
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "db"),
            database=os.environ.get("DB_NAME", "cid_db"),
            user=os.environ.get("DB_USER", "daniel"),
            password=os.environ.get("DB_PASSWORD", "secret_pass")
        )
        cursor = conn.cursor()
        
        print(f"[DATABASE] Conectado ao banco para salvar dados de IBGE {codigo_ibge} ({ano}/{periodo})")        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERRO] Falha ao salvar no banco: {e}")

def ejecutar_pipeline_extracao(lista_ibge, ano, bimestre):
    print(f"[PIPELINE] Iniciando lote para {len(lista_ibge)} municipios...")

    # Gap de segurança de 60 segundos para evitar Rate Limiting do Siconfi
    DELAY_API = 60

    # A. Extracao Entes (Geral)
    url_entes = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/entes"
    dados_entes = extrair_siconfi("Entes", url_entes)
    if dados_entes:
        salvar_no_banco(dados_entes, codigo_ibge=None, ano=None, periodo="Geral")

    print(f"[ETL] Aguardando {DELAY_API} segundos antes de iniciar o loop de municipios...")
    time.sleep(DELAY_API)

    # B. Loop pelos municipios da lista
    for codigo_ibge in lista_ibge:
        print(f"\n--- Processando Municipio IBGE: {codigo_ibge} ---")
    
        # 1. Extracao RREO (Usa IBGE, Ano e Bimestre)
        url_rreo = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo"
        params_rreo = {
            "an_exercicio": ano, 
            "nr_periodo": bimestre, 
            "co_tipo_demonstrativo": "RREO", 
            "id_ente": codigo_ibge
        }
        dados_rreo = extrair_siconfi("RREO", url_rreo, params_rreo)
        
        if dados_rreo:
            salvar_no_banco(dados_rreo, codigo_ibge, ano, f"Bimestre {bimestre}")
        
        print(f"[ETL] Aguardando {DELAY_API} segundos para respeitar o limite da API...")
        time.sleep(DELAY_API)

        # 2. Extracao DCA (Usa IBGE e Ano)
        url_dca = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
        params_dca = {
            "an_exercicio": ano, 
            "id_ente": codigo_ibge
        }
        dados_dca = extrair_siconfi("DCA", url_dca, params_dca)
        
        if dados_dca:
            despesas_educacao = [
                item for item in dados_dca 
                if item.get("conta") and item.get("conta").startswith("12.")
            ]
            print(f"[ETL] Filtro aplicado: Encontradas {len(despesas_educacao)} linhas de despesas de educacao na DCA.")
            salvar_no_banco(despesas_educacao, codigo_ibge, ano, "Anual")

        print(f"[ETL] Aguardando {DELAY_API} segundos antes de mudar de municipio...")
        time.sleep(DELAY_API)

if __name__ == "__main__":
    arquivo_municipios = INPUT_DIR / 'municipios.json'
    arquivo_config = INPUT_DIR / 'config.json'

    if arquivo_municipios.exists():
        with open(arquivo_municipios, 'r') as f:
            ibge_lista = json.load(f)
    else:
        ibge_lista = [3529005]

    if arquivo_config.exists():
        with open(arquivo_config, 'r') as f:
            config_dados = json.load(f)
        ano_escolhido = int(config_dados.get('ano', 2025))
        bimestre_escolhido = int(config_dados.get('bimestre', 6))
    else:
        ano_escolhido = 2025
        bimestre_escolhido = 6

    executar_pipeline_extracao(ibge_lista, ano_escolhido, bimestre_escolhido)