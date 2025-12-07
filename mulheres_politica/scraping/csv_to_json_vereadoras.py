import zipfile
import io
import csv
import json
import time
import os

class CsvToJsonVereadoras:
    """
    Classe responsável por processar o arquivo ZIP baixado e converter
    os dados de vereadoras eleitas de CSV para JSON.
    """
    
    def __init__(self):
        self.pasta_dados = "../data"
        self.nome_arquivo_zip = "consulta_cand_2024.zip"
        self.nome_arquivo_json = "vereadoras.json"
        
    def verificar_arquivo_zip(self):
        """
        Verifica se o arquivo ZIP está disponível para processamento.
        """
        print("═══════════════════════════════════════════════════════════════")
        print("CSV TO JSON VEREADORAS - ETAPA 1: VERIFICAR DADOS")
        print("═══════════════════════════════════════════════════════════════")
        
        caminho_zip = os.path.join(self.pasta_dados, self.nome_arquivo_zip)
        
        if not os.path.exists(caminho_zip):
            print(f"[ERRO] Arquivo ZIP não encontrado: {caminho_zip}")
            print("Execute primeiro 'webscraping_vereadoras.py' para baixar os dados")
            return None
        
        tamanho_mb = os.path.getsize(caminho_zip) / (1024 * 1024)
        print(f"[SUCESSO] Arquivo ZIP encontrado: {caminho_zip}")
        print(f"Tamanho: {tamanho_mb:.1f} MB")
        
        return caminho_zip
    
    def processar_csvs_em_memoria(self, caminho_zip):
        """
        Descompacta e processa os CSVs em memória para extrair dados de vereadoras.
        """
        print("\n═══════════════════════════════════════════════════════════════")
        print("CSV TO JSON VEREADORAS - ETAPA 2: PROCESSAR CSVs")
        print("═══════════════════════════════════════════════════════════════")
        
        vereadoras = []
        stats = {
            "total_eleitos_geral": 0,
            "total_homens_eleitos": 0,
            "total_mulheres_eleitas": 0,
            "total_nao_divulgado_eleitos": 0,
            "arquivos_processados": 0
        }
        
        try:
            print("Abrindo arquivo ZIP...")
            with zipfile.ZipFile(caminho_zip) as z:
                # Listar arquivos CSV disponíveis
                arquivos_csv = [f for f in z.namelist() 
                              if f.lower().endswith('.csv') 
                              and "consulta_cand" in f.lower() 
                              and "brasil" not in f.lower()]
                
                if not arquivos_csv:
                    print("[ERRO] Nenhum arquivo CSV válido encontrado no ZIP")
                    return None
                
                print(f"Encontrados {len(arquivos_csv)} arquivos CSV para processar")
                print("Iniciando processamento por estado...")
                
                for idx, nome_arq in enumerate(arquivos_csv, 1):
                    uf_arquivo = nome_arq.upper().replace(".CSV", "")[-2:]
                    
                    print(f"   [{idx:02d}/{len(arquivos_csv):02d}] Processando: {uf_arquivo} ({nome_arq})")
                    
                    try:
                        with z.open(nome_arq) as f:
                            # Ler CSV em memória
                            conteudo = io.TextIOWrapper(f, encoding='latin-1')
                            leitor = csv.DictReader(conteudo, delimiter=';')
                            
                            contador_estado = 0
                            
                            for linha in leitor:
                                try:
                                    # Verificar se é cargo de vereador (código 13)
                                    if linha.get('CD_CARGO') != '13':
                                        continue
                                    
                                    # Verificar se foi eleito
                                    situacao = str(linha.get('DS_SIT_TOT_TURNO', '')).upper()
                                    termos_vitoria = ["ELEITO", "ELEITO POR QP", "ELEITO POR MÉDIA"]
                                    
                                    if situacao not in termos_vitoria:
                                        continue
                                    
                                    if "SUPLENTE" in situacao or "NÃO ELEITO" in situacao:
                                        continue
                                    
                                    stats["total_eleitos_geral"] += 1
                                    
                                    # Analisar gênero
                                    cod_genero = linha.get('CD_GENERO')
                                    
                                    if cod_genero == '2':  # Masculino
                                        stats["total_homens_eleitos"] += 1
                                        continue
                                    elif cod_genero == '4':  # Feminino
                                        stats["total_mulheres_eleitas"] += 1
                                        # Continuar processamento para mulheres
                                    else:
                                        stats["total_nao_divulgado_eleitos"] += 1
                                        continue
                                    
                                    # Processar dados específicos da vereadora
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
                                        "url_fonte": "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2024.zip",
                                        "data_extracao": time.strftime("%Y-%m-%d")
                                    }
                                    
                                    vereadoras.append(dados_vereadora)
                                    contador_estado += 1
                                    
                                except Exception:
                                    continue
                            
                            print(f"        [SUCESSO] {contador_estado} vereadoras encontradas em {uf_arquivo}")
                            stats["arquivos_processados"] += 1
                            
                    except Exception as e:
                        print(f"        [ERRO] Erro processando {uf_arquivo}: {e}")
                        continue
                
        except Exception as e:
            print(f"[ERRO] Erro crítico ao processar ZIP: {e}")
            return None
        
        return vereadoras, stats
    
    def gerar_json_final(self, vereadoras, stats):
        """
        Gera o arquivo JSON final com metadados e dados das vereadoras.
        """
        print("\n═══════════════════════════════════════════════════════════════")
        print("CSV TO JSON VEREADORAS - ETAPA 3: GERAR JSON FINAL")
        print("═══════════════════════════════════════════════════════════════")
        
        total = stats["total_eleitos_geral"]
        mulheres = stats["total_mulheres_eleitas"]
        percentual = round(mulheres / total, 4) * 100 if total > 0 else 0
        
        resultado_final = {
            "metadados": {
                "resumo_executivo": "Dados referentes às vereadoras eleitas no pleito municipal de 2024.",
                "total_vereadores_brasil": total,
                "total_homens_eleitos": stats["total_homens_eleitos"],
                "total_mulheres_eleitas": mulheres,
                "representatividade_feminina_percentual": percentual,
                "total_outros_generos_ou_nao_informado": stats["total_nao_divulgado_eleitos"],
                "arquivos_processados": stats["arquivos_processados"],
                "data_processamento": time.strftime("%Y-%m-%d %H:%M:%S"),
                "fonte_oficial": "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2024.zip"
            },
            "vereadoras": vereadoras
        }
        
        # Salvar arquivo JSON
        caminho_json = os.path.join(self.pasta_dados, self.nome_arquivo_json)
        
        try:
            print(f"Salvando arquivo JSON: {caminho_json}")
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(resultado_final, f, ensure_ascii=False, indent=4)
            
            print("[SUCESSO] Arquivo JSON salvo com sucesso!")
            return caminho_json
            
        except Exception as e:
            print(f"[ERRO] Erro ao salvar JSON: {e}")
            return None
    
    def executar_conversao(self):
        """
        Executa o processo completo de conversão CSV para JSON.
        """
        print("INICIANDO CONVERSÃO CSV PARA JSON - VEREADORAS")
        print(f"Horário de início: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Etapa 1: Verificar arquivo ZIP
        caminho_zip = self.verificar_arquivo_zip()
        if not caminho_zip:
            return False
        
        # Etapa 2: Processar CSVs
        resultado_processamento = self.processar_csvs_em_memoria(caminho_zip)
        if not resultado_processamento:
            print("\n[FALHA] Erro no processamento dos CSVs")
            return False
        
        vereadoras, stats = resultado_processamento
        
        # Etapa 3: Gerar JSON final
        arquivo_json = self.gerar_json_final(vereadoras, stats)
        if not arquivo_json:
            print("\n[FALHA] Erro na geração do JSON")
            return False
        
        # Relatório final
        print("\n═══════════════════════════════════════════════════════════════")
        print("CONVERSÃO CONCLUÍDA COM SUCESSO!")
        print("═══════════════════════════════════════════════════════════════")
        print(f"Estatísticas do processamento:")
        print(f"   - Estados processados: {stats['arquivos_processados']}")
        print(f"   - Total de vereadores eleitos: {stats['total_eleitos_geral']:,}")
        print(f"   - Homens eleitos: {stats['total_homens_eleitos']:,}")
        print(f"   - Mulheres eleitas: {stats['total_mulheres_eleitas']:,}")
        print(f"   - Representatividade feminina: {(stats['total_mulheres_eleitas']/stats['total_eleitos_geral']*100):.2f}%")
        print(f"Arquivo final: {arquivo_json}")
        print(f"Finalizado em: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True

def main():
    """
    Função principal para execução da conversão.
    """
    conversor = CsvToJsonVereadoras()
    sucesso = conversor.executar_conversao()
    
    if not sucesso:
        print("\n[ERRO] Processo de conversão falhou!")
        exit(1)

if __name__ == "__main__":
    main()