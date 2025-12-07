import requests
import os
import time

class WebscrapingVereadoras:
    """
    Classe responsável apenas pelo download do arquivo ZIP com dados de candidatos do TSE.
    Foca exclusivamente na coleta dos dados brutos (CSV) para posterior processamento.
    """
    
    def __init__(self):
        self.pasta_saida = "../data"
        self.termo_busca_api = "consulta candidatos 2024"
        self.urls_fallback = [
            "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2024.zip"
        ]
        self.nome_arquivo_zip = "consulta_cand_2024.zip"
    
    def obter_url_correta(self):
        """
        Busca a URL correta do dataset na API do TSE ou usa fallback.
        """
        print("═══════════════════════════════════════════════════════════════")
        print("WEBSCRAPING VEREADORAS - ETAPA 1: LOCALIZAR DADOS")
        print("═══════════════════════════════════════════════════════════════")
        print("Buscando URL do dataset 'Consulta Candidatos 2024'...")
        
        # Tentar via API oficial do TSE
        url_api = "https://dadosabertos.tse.jus.br/api/3/action/package_search"
        try:
            print("   -> Consultando API oficial do TSE...")
            resp = requests.get(url_api, params={"q": self.termo_busca_api, "rows": 10}, timeout=15)
            if resp.status_code == 200:
                pacotes = resp.json().get('result', {}).get('results', [])
                for pkg in pacotes:
                    for rec in pkg.get('resources', []):
                        url = rec.get('url', '')
                        if url.lower().endswith('.zip') and "consulta_cand" in url.lower():
                            print(f"   [SUCESSO] URL encontrada via API: {url}")
                            return url
            print("   [AVISO] API não retornou URL válida")
        except Exception as e:
            print(f"   [ERRO] Erro na consulta da API: {e}")

        # Fallback para URL direta
        print("   -> Testando URLs de fallback...")
        for url in self.urls_fallback:
            try:
                r = requests.head(url, timeout=10)
                if r.status_code == 200:
                    print(f"   [SUCESSO] URL validada (fallback): {url}")
                    return url
            except Exception as e:
                print(f"   [ERRO] Fallback falhou: {e}")
                
        return None
    
    def baixar_zip_dados(self, url_zip):
        """
        Baixa o arquivo ZIP com os dados de candidatos.
        """
        print("\n═══════════════════════════════════════════════════════════════")
        print("WEBSCRAPING VEREADORAS - ETAPA 2: DOWNLOAD DOS DADOS")
        print("═══════════════════════════════════════════════════════════════")
        print(f"Fonte de dados: {url_zip}")
        
        if not os.path.exists(self.pasta_saida):
            print(f"Criando pasta de destino: {self.pasta_saida}")
            os.makedirs(self.pasta_saida)
        
        caminho_arquivo = os.path.join(self.pasta_saida, self.nome_arquivo_zip)
        
        try:
            print("Iniciando download...")
            response = requests.get(url_zip, stream=True)
            response.raise_for_status()
            
            # Obter tamanho do arquivo
            total_size = int(response.headers.get('content-length', 0))
            if total_size:
                print(f"Tamanho do arquivo: {total_size / (1024*1024):.1f} MB")
            
            # Download com progresso
            downloaded = 0
            chunk_size = 8192
            
            with open(caminho_arquivo, 'wb') as f:
                print("Progresso do download:")
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            progress_bar = "█" * int(percent // 5) + "░" * (20 - int(percent // 5))
                            print(f"\r   [{progress_bar}] {percent:.1f}% ({downloaded/(1024*1024):.1f}/{total_size/(1024*1024):.1f} MB)", end="", flush=True)
                        else:
                            print(f"\r   Baixado: {downloaded/(1024*1024):.1f} MB", end="", flush=True)
            
            print(f"\n[SUCESSO] Download concluído com sucesso!")
            print(f"Arquivo salvo em: {caminho_arquivo}")
            return caminho_arquivo
            
        except Exception as e:
            print(f"\n[ERRO] ERRO no download: {e}")
            return None
    
    def executar_webscraping(self):
        """
        Executa o processo completo de webscraping (apenas download).
        """
        print("INICIANDO WEBSCRAPING DE DADOS DE VEREADORAS")
        print(f"Horário de início: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Etapa 1: Obter URL
        url = self.obter_url_correta()
        if not url:
            print("\n[FALHA] Não foi possível obter a URL dos dados.")
            return False
        
        # Etapa 2: Baixar ZIP
        arquivo_baixado = self.baixar_zip_dados(url)
        if not arquivo_baixado:
            print("\n[FALHA] Erro no download do arquivo.")
            return False
        
        print("\n═══════════════════════════════════════════════════════════════")
        print("WEBSCRAPING CONCLUÍDO COM SUCESSO!")
        print("═══════════════════════════════════════════════════════════════")
        print(f"Arquivo ZIP disponível em: {arquivo_baixado}")
        print("Próximo passo: Execute 'csv_to_json_vereadoras.py' para processar os dados")
        print(f"Finalizado em: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True

def main():
    """
    Função principal para execução do webscraping.
    """
    scraper = WebscrapingVereadoras()
    sucesso = scraper.executar_webscraping()
    
    if not sucesso:
        print("\n[ERRO] Processo de webscraping falhou!")
        exit(1)

if __name__ == "__main__":
    main()

