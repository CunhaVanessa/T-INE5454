import requests
import zipfile
import io
import csv
import json
import time
import os

PASTA_SAIDA = "data"
UFS_ALVO = []
TERMO_BUSCA_API = "consulta candidatos 2024"
URLS_FALLBACK = [
    "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2024.zip"
]

def obter_url_correta():
    print("1. Buscando URL do dataset 'Consulta Candidatos'...")
    
    url_api = "https://dadosabertos.tse.jus.br/api/3/action/package_search"
    try:
        resp = requests.get(url_api, params={"q": TERMO_BUSCA_API, "rows": 10}, timeout=10)
        if resp.status_code == 200:
            pacotes = resp.json().get('result', {}).get('results', [])
            for pkg in pacotes:
                for rec in pkg.get('resources', []):
                    url = rec.get('url', '')
                    if url.lower().endswith('.zip') and "consulta_cand" in url.lower():
                        print(f"    ✓ [SUCESSO] URL encontrada na API: {url}")
                        return url
    except Exception:
        pass

    print("   ✗ [AVISO] API retornou dados inconclusivos. Usando Link Direto (Fallback).")
    
    for url in URLS_FALLBACK:
        try:
            r = requests.head(url, timeout=10)
            if r.status_code == 200:
                print(f"   ✓ [SUCESSO] Link direto validado: {url}")
                return url
        except:
            pass
            
    return None

def processar_dados(url_zip):
    print(f"\n2. Baixando e processando arquivo...")
    print(f"   Fonte: {url_zip}")
    
    vereadoras = []

    stats = {
        "total_eleitos_geral": 0,
        "total_homens_eleitos": 0,
        "total_mulheres_eleitas": 0,
        "total_nao_divulgado_eleitos": 0
    }
    
    try:
        response = requests.get(url_zip, stream=True)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            arquivos_csv = [f for f in z.namelist() if f.lower().endswith('.csv') and "consulta_cand" in f.lower() and "brasil" not in f.lower()]
            
            if not arquivos_csv:
                print("   [ERRO] O ZIP baixado não contém arquivos 'consulta_cand*.csv'.")
                return []

            for nome_arq in arquivos_csv:
                uf_arquivo = nome_arq.upper().replace(".CSV", "")[-2:]
                
                if UFS_ALVO and uf_arquivo not in UFS_ALVO:
                    continue

                print(f"   -> Lendo tabela: {nome_arq}")
                
                with z.open(nome_arq) as f:
                    conteudo = io.TextIOWrapper(f, encoding='latin-1')
                    leitor = csv.DictReader(conteudo, delimiter=';')
                    
                    for linha in leitor:
                        try:
                            if 'CD_CARGO' not in linha or 'CD_GENERO' not in linha:
                                continue

                            if linha['CD_CARGO'] != '13': continue
                            
                            situacao = str(linha.get('DS_SIT_TOT_TURNO', '')).upper()
                            
                            termos_vitoria = ["ELEITO", "ELEITO POR QP", "ELEITO POR MÉDIA"]
                            if situacao not in termos_vitoria: continue
                            
                            if "SUPLENTE" in situacao or "NÃO ELEITO" in situacao: continue
                            
                            stats["total_eleitos_geral"] += 1
                            
                            cod_genero = linha.get('CD_GENERO')

                            if cod_genero == '2': # Masculino
                                stats["total_homens_eleitos"] += 1
                                continue # Se é homem, já contamos, pode pular
                            elif cod_genero == '4': # Feminino
                                stats["total_mulheres_eleitas"] += 1
                                # Mulher: Não continua, desce para extrair dados
                            else:
                                stats["total_nao_divulgado_eleitos"] += 1
                                continue
                            cidade_nasc = linha.get('NM_MUNICIPIO_NASCIMENTO', 'Não Informado')
                            uf_nasc = linha.get('SG_UF_NASCIMENTO', '')
                            naturalidade_formatada = f"{cidade_nasc} - {uf_nasc}" if uf_nasc else "Não Informado"
                            
                            email = linha.get('DS_EMAIL', '').lower()
                            if "não divulgável" in email:
                                email = "Não divulgado"

                            dados_vereadora = {
                                "nome": linha.get('NM_URNA_CANDIDATO'),
                                "nome_civil": linha.get('NM_CANDIDATO'),
                                "partido": linha.get('SG_PARTIDO'),
                                "uf": linha.get('SG_UF'),
                                "municipio": linha.get('NM_UE'),
                                "periodo_mandato": "2025-2028",
                                "naturalidade": naturalidade_formatada,
                                "situacao": situacao,
                                "data_nascimento": linha.get('DT_NASCIMENTO'),
                                "grau_instrucao": linha.get('DS_GRAU_INSTRUCAO'),
                                "ocupacao": linha.get('DS_OCUPACAO'),
                                "estado_civil": linha.get('DS_ESTADO_CIVIL'),
                                "cor_raca": linha.get('DS_COR_RACA'),
                                "email": email,
                                "fonte_dados": "TSE - Dados Abertos 2024",
                                "url_fonte": url_zip,
                                "data_extracao": time.strftime("%Y-%m-%d")
                            }
                            
                            vereadoras.append(dados_vereadora)

                        except Exception:
                            continue

    except Exception as e:
        print(f"   [ERRO CRÍTICO] {e}")
        return []
        
    total = stats["total_eleitos_geral"]
    mulheres = stats["total_mulheres_eleitas"]
    percentual = round(mulheres / total, 4) * 100

    resultado_final = {
        "metadados": {
            "resumo_executivo": "Dados referentes aos vereadores eleitos no pleito municipal de 2024.",
            "total_vereadores_brasil": total,
            "total_homens_eleitos": stats["total_homens_eleitos"],
            "total_mulheres_eleitas": mulheres,
            "representatividade_feminina_percentual": percentual,
            "total_outros_generos_ou_nao_informado": stats["total_nao_divulgado_eleitos"],
            "data_processamento": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fonte_oficial": url_zip
        },
        "vereadoras": vereadoras
    }
    
    return resultado_final

def main():
    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)

    url = obter_url_correta()
    
    if not url:
        print("   ✗   [FALHA] Não foi possível obter a URL dos dados.")
        return

    resultado = processar_dados(url)
    
    caminho_final = os.path.join(PASTA_SAIDA, "vereadoras.json")
    qtd = len(resultado["vereadoras"])
    total_geral = resultado["metadados"]["total_vereadores_brasil"]
    print(f"\n   ✓ [FINALIZADO] Encontradas {qtd} vereadoras.")
    print(f"   Salvando em: {caminho_final}")
    
    with open(caminho_final, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
