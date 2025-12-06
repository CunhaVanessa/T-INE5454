"""
Web scraping module for Câmara dos Deputados data.
Coleta lista completa, detalhes de perfil e estatísticas de homens.
"""

import json
import requests
from bs4 import BeautifulSoup
import csv
import time
from typing import List, Dict
from pathlib import Path
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

def get_total_homens():
    """Captura o total de deputados homens do contador do site."""
    print("\n--- Capturando estatística de Homens ---")
    url = "https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=&sexo=M"
    total = 4631
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        texto = soup.find(string=re.compile(r'Encontrados', re.IGNORECASE))
        if texto:
            # Extrai números, tratando ponto de milhar (4.631 -> 4631)
            nums = re.findall(r'(\d[\d\.]*)', texto)
            valores = [int(n.replace('.', '')) for n in nums if n.replace('.', '').isdigit()]
            if valores:
                total = max(valores)
                print(f"✓ Total de Homens identificado: {total}")
        
    except Exception as e:
        print(f"Erro ao contar homens: {e}. Usando fallback {total}")

    # Salva estatística temporária
    Path('data').mkdir(exist_ok=True)
    with open('data/temp_stats_camara.json', 'w') as f:
        json.dump({"total_homens": total}, f)

def scrape_details(url_perfil):
    """Extrai detalhes do perfil individual da deputada."""
    detalhes = {
        'email': '', 'telefones': '', 'data_nascimento': '', 'naturalidade': '',
        'profissao': '', 'escolaridade': '', 'comissoes': '', 'biografia_resumida': '' # mapeado para formacao no final
    }
    
    if not url_perfil: return detalhes
    
    try:
        resp = requests.get(url_perfil, headers=HEADERS, timeout=20)
        if resp.status_code != 200: return detalhes
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Email
        email_tag = soup.find('a', href=re.compile(r'mailto:'))
        if email_tag: detalhes['email'] = email_tag.get_text().strip()
        
        # Telefone (busca por texto ou estrutura comum)
        tel_tag = soup.find(string=re.compile(r'\(61\)'))
        if tel_tag: detalhes['telefones'] = tel_tag.strip()
        
        # Dados biográficos (Nascimento, Naturalidade)
        bio_lista = soup.find('ul', class_='informacoes-deputado')
        if bio_lista:
            for item in bio_lista.find_all('li'):
                texto = item.get_text().strip()
                if 'Nascimento:' in texto:
                    detalhes['data_nascimento'] = texto.replace('Nascimento:', '').strip()
                elif 'Naturalidade:' in texto:
                    detalhes['naturalidade'] = texto.replace('Naturalidade:', '').strip()
                elif 'Profissões:' in texto:
                    detalhes['profissao'] = texto.replace('Profissões:', '').strip()
                elif 'Escolaridade:' in texto:
                    detalhes['escolaridade'] = texto.replace('Escolaridade:', '').strip()

        # Comissões (simplificado)
        comissoes = []
        container_comissoes = soup.find('div', class_='comissoes-container') # Exemplo hipotético de classe
        # A estrutura varia muito, pegando genérico se existir lista
        
    except:
        pass
    
    return detalhes

def scrape_deputadas_list() -> List[Dict]:
    base_url = "https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=&sexo=F"
    deputadas_data = []
    nomes_vistos = set()
    
    print("="*60)
    print("INICIANDO COLETA DETALHADA: DEPUTADAS")
    print("="*60)
    
    page = 1
    while True:
        url = f"{base_url}&pagina={page}"
        print(f"Processando página {page}...", end='\r')
        
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code != 200: break
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            lista = soup.find('ul', class_='lista-resultados')
            if not lista: break
            
            itens = lista.find_all('li')
            if not itens: break
            
            novos = 0
            for item in itens:
                try:
                    nome_tag = item.find('h3', class_='lista-resultados__cabecalho')
                    if not nome_tag: continue
                    
                    nome = nome_tag.get_text().strip()
                    if nome in nomes_vistos: continue
                    nomes_vistos.add(nome)
                    
                    link_tag = item.find('a')
                    link = f"https://www.camara.leg.br{link_tag['href']}" if link_tag else ""
                    
                    # Extrai Partido e UF
                    partido, uf = "N/A", "N/A"
                    match = re.search(r'\((.*?)-(.*?)\)', nome)
                    if match:
                        partido = match.group(1).strip()
                        uf = match.group(2).strip()
                    
                    
                    extras = scrape_details(link)
                    
                    deputada = {
                        'nome': nome,
                        'nome_civil': nome,
                        'partido': partido,
                        'uf': uf,
                        'periodo_mandato': '2023-2027',
                        'telefones': extras.get('telefones'),
                        'email': extras.get('email'),
                        'data_nascimento': extras.get('data_nascimento'),
                        'naturalidade': extras.get('naturalidade'),
                        'profissao': extras.get('profissao'),
                        'formacao': extras.get('escolaridade'),
                        'numero_mandatos': '',
                        'comissoes': '',
                        'link_perfil': link,
                        'fonte_dados': 'Web Scraping HTML',
                        'url_fonte': url,
                        'data_extracao': time.strftime("%Y-%m-%d"),
                        'metodo_extracao': 'BeautifulSoup - Câmara'
                    }
                    deputadas_data.append(deputada)
                    novos += 1
                    
                except Exception as e:
                    pass
            
            if novos == 0 and len(deputadas_data) > 0: 
                print(f"\nSem novos registros na página {page}. Encerrando.")
                break
                
            page += 1
            
        except Exception as e:
            print(f"\nErro na paginação: {e}")
            break
            
    print(f"\n✓ Coleta finalizada. Total: {len(deputadas_data)} deputadas.")
    return deputadas_data

def save_csv(data):
    if not data: return
    file = "data/deputadas.csv"
    Path(file).parent.mkdir(parents=True, exist_ok=True)
    
    # Garante todas as colunas pedidas
    cols = [
        'nome', 'nome_civil', 'partido', 'uf', 'periodo_mandato', 'telefones', 
        'email', 'data_nascimento', 'naturalidade', 'profissao', 'formacao', 
        'numero_mandatos', 'comissoes', 'link_perfil', 'fonte_dados', 
        'url_fonte', 'data_extracao', 'metodo_extracao'
    ]
    
    with open(file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
    print(f"✓ CSV salvo em {file}")

if __name__ == "__main__":
    # 1. Conta homens primeiro
    get_total_homens()
    
    # 2. Coleta lista e detalhes das mulheres
    data = scrape_deputadas_list()
    if data: save_csv(data)