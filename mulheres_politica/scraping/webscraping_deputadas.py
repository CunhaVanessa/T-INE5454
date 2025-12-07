"""
Web scraping module for Câmara dos Deputados data.

Este módulo coleta informações sobre mulheres deputadas federais
do site da Câmara dos Deputados brasileira.
"""

import json
import requests
from bs4 import BeautifulSoup
import csv
import time
from typing import List, Dict, Optional
from pathlib import Path
import re

HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }

def get_total_homens():
    """Captura o total de deputados homens do contador do site."""
    print("\n--- Capturando estatística de Homens ---")
    url = "https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=&sexo=M"
    total = 4631
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        texto = soup.find(string=re.compile(r'encontrados', re.IGNORECASE))
        if texto:
            nums = re.findall(r'(\d[\d\.]*)', texto)
            valores = [int(n.replace('.', '')) for n in nums if n.replace('.', '').isdigit()]
            if valores:
                total = max(valores)
                print(f"✓ Total de Homens identificado: {total}")
        
        return total
        
    except Exception as e:
        print(f"Erro ao contar homens: {e}. Usando fallback {total}")
        return total

# ==========================================
# PARTE 1: FUNÇÃO PRINCIPAL DE SCRAPING
# ==========================================

def scrape_deputadas_list() -> List[Dict]:
    """
    Faz scraping da lista de deputadas em exercício.
    Usa a URL com filtro por sexo do próprio site.
    """
    
    base_url = "https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=&sexo=F"

    deputadas_data =[]
    
    try:
        print("=" * 70)
        print("INICIANDO WEB SCRAPING - DEPUTADAS FEDERAIS")
        print("=" * 70)
        print(f"\n1. Acessando página com filtro de gênero (sexo=F)...")
        print(f"   URL: {base_url}")

        session = requests.Session()
        
        response = session.get(base_url, headers=HEADERS, timeout=15)
        
        print(f"   Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ Página acessada com sucesso!\n")
            
            deputadas_data = process_paginated_results(session, response, base_url, HEADERS)
            
        else:
            print(f"   ✗ Erro ao acessar página: HTTP {response.status_code}\n")
            
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Erro de conexão: {e}\n")
    except Exception as e:
        print(f"   ✗ Erro geral: {e}\n")
    
    return deputadas_data

# ==========================================
# PARTE 2: PROCESSAMENTO DE PÁGINAS
# ==========================================

def process_paginated_results(session: requests.Session, initial_response: requests.Response, 
                             base_url: str, headers: Dict) -> List[Dict]:
    
    all_deputadas = []
    current_page = 1
    max_consecutive_errors = 3
    consecutive_errors = 0
    
    print("2. Processando resultados paginados...\n")
    
    # Processar primeira página
    print(f"   [Página {current_page}] Processando...")
    page_deputadas = parse_deputadas_results(initial_response.content, base_url)
    
    if page_deputadas:
        all_deputadas.extend(page_deputadas)
        print(f"   [Página {current_page}] ✓ {len(page_deputadas)} deputadas encontradas")
    else:
        print(f"   [Página {current_page}] ✗ Nenhuma deputada extraída")

    while consecutive_errors < max_consecutive_errors:
        current_page += 1
        
        time.sleep(2)
        
        try:
            page_url = f"https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=&sexo=F&pagina={current_page}"
            
            print(f"   [Página {current_page}] Processando...")
            
            page_response = session.get(page_url, headers=headers, timeout=15)
            
            if page_response.status_code == 200:
                soup = BeautifulSoup(page_response.content, 'html.parser')
                page_text = soup.get_text().lower()
                
                no_results_indicators = [
                    "nenhuma ocorrência encontrada",
                    "nenhum resultado encontrado",
                    "não foram encontrados resultados",
                    "sua pesquisa não retornou resultados",
                    "não há deputados"
                ]
                
                page_is_empty = any(indicator in page_text for indicator in no_results_indicators)
                
                if page_is_empty:
                    print(f"   [Página {current_page}] ✓ Fim da paginação detectado")
                    print(f"\n3. ✓ Paginação concluída - {current_page - 1} páginas processadas")
                    break
                
                page_deputadas = parse_deputadas_results(page_response.content, page_url)
                
                if page_deputadas and len(page_deputadas) > 0:
                    all_deputadas.extend(page_deputadas)
                    print(f"   [Página {current_page}] ✓ {len(page_deputadas)} deputadas encontradas")
                    consecutive_errors = 0
                else:
                    if "deputad" not in page_text and "resultado" not in page_text:
                        print(f"   [Página {current_page}] ✓ Página vazia - fim da paginação")
                        print(f"\n3. ✓ Paginação concluída - {current_page - 1} páginas processadas")
                        break
                    else:
                        print(f"   [Página {current_page}] ⚠ Página com conteúdo mas extração falhou")
                        consecutive_errors += 1
                        
            elif page_response.status_code == 404:
                print(f"   [Página {current_page}] ✓ Página não existe (404) - fim da paginação")
                print(f"\n3. ✓ Paginação concluída - {current_page - 1} páginas processadas")
                break
            else:
                print(f"   [Página {current_page}] ✗ Erro HTTP {page_response.status_code}")
                consecutive_errors += 1
                
        except Exception as e:
            print(f"   [Página {current_page}] ✗ Erro: {e}")
            consecutive_errors += 1
    
    if consecutive_errors >= max_consecutive_errors:
        print(f"\n3. ⚠ Paginação interrompida após {consecutive_errors} erros consecutivos")
    
    print(f"\n   📊 TOTAL COLETADO: {len(all_deputadas)} deputadas de {current_page - 1} páginas\n")
    
    if all_deputadas:
        print("4. Coletando informações detalhadas dos perfis individuais...\n")
        detailed_deputadas = collect_detailed_profiles(all_deputadas, session, headers)
        return detailed_deputadas
    
    return all_deputadas

def parse_deputadas_results(html_content: bytes, source_url: str) -> List[Dict]:
    
    soup = BeautifulSoup(html_content, 'html.parser')
    deputadas = []
    
    result_patterns = [
        {'selector': '.card-deputado, .card-resultado, .deputado-resultado'},
        {'selector': 'ul.lista-deputados li, .lista-resultados li'},
        {'selector': 'table.resultados tr, .tabela-deputados tr'},
        {'selector': 'div[class*="deputado"]'},
        {'selector': 'a[href*="/deputados/"][href*="/perfil"]'}
    ]
    for pattern in result_patterns:
        elements = soup.select(pattern['selector'])
        
        if elements:
            for element in elements:
                deputada_data = extract_deputada_from_element(element, source_url)
                
                if deputada_data and is_valid_deputada_data(deputada_data):
                    deputadas.append(deputada_data)
            
            if deputadas:
                return deputadas
    
    general_elements = soup.select('a[href*="/deputados/"]')
    
    for element in general_elements[:50]:
        deputada_data = extract_deputada_from_element(element, source_url)
        
        if deputada_data and is_valid_deputada_data(deputada_data):
            deputadas.append(deputada_data)
    
    return deputadas

def extract_deputada_from_element(element, source_url: str) -> Optional[Dict]:
    try:
        nome = extract_text_by_selectors(element, [
            '.nome-deputado', '.nome-resultado', '.deputado-nome',
            '.card-title', '.resultado-nome', '.nome-parlamentar',
            'h1', 'h2', 'h3', 'h4', 'h5',
            'a[href*="/deputados/"]', 'a.nome', 'a strong',
            'strong', 'b',
            'td:first-child', 'th:first-child'
        ])
        
        if not nome or len(nome) < 3:
            return None
        
        nome = clean_deputada_name(nome)
        if not nome:
            return None
        
        perfil_link = ""
        link_elem = element.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if '/deputados/' in href:
                if href.startswith('http'):
                    perfil_link = href
                else:
                    perfil_link = f"https://www.camara.leg.br{href}"
        
        deputada_data = {
            'nome': nome,
            'partido': "",
            'uf': "",
            'link_perfil': perfil_link,
            'fonte_dados': 'Web Scraping HTML',
            'url_fonte': source_url,
            'data_extracao': time.strftime("%Y-%m-%d %H:%M:%S"),
            'metodo_extracao': 'BeautifulSoup - Câmara dos Deputados (filtro sexo=F)'
        }
        
        return deputada_data
    
    except Exception as e:
        return None

# ==========================================
# PARTE 4: COLETA DE DADOS DETALHADOS
# ==========================================

def collect_detailed_profiles(deputadas: List[Dict], session: requests.Session, headers: Dict) -> List[Dict]:
    detailed_deputadas = []
    
    for i, deputada in enumerate(deputadas, 1):
        nome = deputada['nome']
        perfil_url = deputada.get('link_perfil', '')
        
        print(f"   [{i}/{len(deputadas)}] Processando: {nome}")
        
        if not perfil_url:
            print(f"               ✗ Sem URL de perfil, pulando...")
            detailed_deputadas.append(deputada)
            continue
        
        try:
            response = session.get(perfil_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                detalhes = extract_profile_details(response.content, perfil_url)
                
                deputada_completa = {**deputada, **detalhes}
                detailed_deputadas.append(deputada_completa)
                
                print(f"               ✓ Dados detalhados coletados")
            else:
                print(f"               ✗ Erro HTTP {response.status_code}")
                detailed_deputadas.append(deputada)
            
            if i % 10 == 0:
                time.sleep(2)
            else:
                time.sleep(1)
            
        except Exception as e:
            print(f"               ✗ Erro: {e}")
            detailed_deputadas.append(deputada)
    
    print()
    return detailed_deputadas

# ==========================================
# PARTE 5: EXTRAÇÃO DE DADOS DO PERFIL
# ==========================================

# def extract_profile_details(html_content: bytes, perfil_url: str) -> Dict:  
#     soup = BeautifulSoup(html_content, 'html.parser')
    
#     detalhes = {
#         'nome_civil': '',
#         'partido_detalhado': '',
#         'naturalidade': '',
#         'titulo_cargo': '',
#         'propostas_autoria': '',
#         'propostas_relatadas': '',
#         'votacoes_plenario': '',
#         'url_perfil_detalhado': perfil_url,
#         'perfil_detalhado': 'Coletado'
#     }
    
#     try:
#         texto_completo = soup.get_text()
        
#         nome_elements = soup.find_all(['h1', 'h2'])
#         for elem in nome_elements:
#             text = elem.get_text().strip()
#             if text and len(text) > 3 and len(text) < 100:
#                 detalhes['nome_civil'] = text
#                 break
        
#         partido_elements = soup.find_all(text=True)
#         for elem in partido_elements:
#             if elem and isinstance(elem, str):
#                 text = elem.strip()
#                 if re.match(r'^[A-Z]{2,10}\s*-\s*.+', text) and len(text) < 80:
#                     detalhes['partido_detalhado'] = text[:50]
#                     break
        
#         nat_match = re.search(
#             r'(?:Natural de|Naturalidade)[:\s]*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\.;\n]{3,80})',
#             texto_completo,
#             re.IGNORECASE
#         )
#         if nat_match:
#             naturalidade = nat_match.group(1).strip()
#             naturalidade = re.sub(r'\s+', ' ', naturalidade)
#             detalhes['naturalidade'] = naturalidade[:100]
        
#         titulo_keywords = ['TITULAR', 'EXERCÍCIO', 'DEPUTAD']
#         titulo_elements = soup.find_all(['h2', 'h3', 'p', 'div', 'span'])
#         for elem in titulo_elements:
#             text = elem.get_text().strip().upper()
#             if any(keyword in text for keyword in titulo_keywords):
#                 if len(text) < 50:  # Evitar textos longos
#                     detalhes['titulo_cargo'] = text
#                     break
        
#         all_numbers = []
#         for elem in soup.find_all(['span', 'div', 'strong', 'b']):
#             text = elem.get_text().strip()
#             if text.isdigit() and len(text) <= 4 and int(text) > 0:
#                 all_numbers.append(text)
        
#         if len(all_numbers) > 0:
#             detalhes['propostas_autoria'] = all_numbers[0]
#         if len(all_numbers) > 1:
#             detalhes['votacoes_plenario'] = all_numbers[1]
#         if len(all_numbers) > 2:
#             detalhes['propostas_relatadas'] = all_numbers[2]
    
#     except Exception as e:
#         pass
    
#     return detalhes

def extract_profile_details(html_content: bytes, perfil_url: str) -> Dict:  
    soup = BeautifulSoup(html_content, 'html.parser')
    
    detalhes = {
        'nome_civil': '',
        'partido': '',
        'uf': '',
        'data_nascimento': '',
        'naturalidade': '',
        'profissao': '',
        'formacao': '',
        'numero_mandatos': '',
        'comissoes': '',
        'biografia_resumida': '',
        'telefones': '',
        'email': '',
        'periodo_mandato': '',
        'url_perfil_detalhado': perfil_url
    }
    
    try:
        texto_completo = soup.get_text()

        partido_uf_match = re.search(
            r'Partido:\s*([A-Z]{2,10})\s*-\s*([A-Z]{2})',
            texto_completo,
            re.IGNORECASE
        )
        
        if partido_uf_match:
            detalhes['partido'] = partido_uf_match.group(1).strip()
            detalhes['uf'] = partido_uf_match.group(2).strip()
        else:
            partido_uf_pattern = re.search(
                r'\b([A-Z]{2,10})\s*-\s*([A-Z]{2})\b',
                texto_completo
            )
            
            if partido_uf_pattern:
                possivel_partido = partido_uf_pattern.group(1).strip()
                possivel_uf = partido_uf_pattern.group(2).strip()
                
                partidos_validos = [
                    'PT', 'PL', 'PP', 'MDB', 'PSDB', 'PDT', 'PSB', 'REPUBLICANOS',
                    'UNIAO', 'UNIÃO', 'PSOL', 'PCdoB', 'PCDOB', 'PSD', 'CIDADANIA',
                    'AVANTE', 'PODE', 'PODEMOS', 'SOLIDARIEDADE', 'NOVO', 'REDE',
                    'PV', 'PMB', 'PROS', 'PTB', 'PSC', 'PATRIOTA', 'PRD'
                ]
                
                ufs_validas = [
                    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
                    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
                    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
                ]
                
                if possivel_partido in partidos_validos and possivel_uf in ufs_validas:
                    detalhes['partido'] = possivel_partido
                    detalhes['uf'] = possivel_uf
        
        if not detalhes['partido'] or not detalhes['uf']:
            partido_elements = soup.find_all(['div', 'span', 'p', 'strong', 'b'], 
                                            text=re.compile(r'Partido', re.IGNORECASE))
            
            for elem in partido_elements:
                next_text = elem.find_next(text=True)
                if next_text:
                    match = re.search(r'([A-Z]{2,10})\s*-\s*([A-Z]{2})', str(next_text))
                    if match:
                        detalhes['partido'] = match.group(1).strip()
                        detalhes['uf'] = match.group(2).strip()
                        break
        
        nome_elements = soup.find_all(['h1', 'h2'])
        for elem in nome_elements:
            text = elem.get_text().strip()
            if text and len(text) > 3 and len(text) < 100:
                detalhes['nome_civil'] = text
                break
        
        data_match = re.search(
            r'(?:Nascimento|Nascido|Nascida|Data de Nascimento)[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            texto_completo,
            re.IGNORECASE
        )
        if data_match:
            detalhes['data_nascimento'] = data_match.group(1)
        
        nat_match = re.search(
            r'(?:Natural de|Naturalidade)[:\s]*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\.;\n]{3,80})',
            texto_completo,
            re.IGNORECASE
        )
        if nat_match:
            naturalidade = nat_match.group(1).strip()
            naturalidade = re.sub(r'\s+', ' ', naturalidade)
            detalhes['naturalidade'] = naturalidade[:100]

        prof_match = re.search(
            r'(?:Profissão|Ocupação)[:\s]*([A-Za-zÁ-ÿ\s\-]+?)(?:\n|\.|,)',
            texto_completo,
            re.IGNORECASE
        )
        if prof_match:
            detalhes['profissao'] = prof_match.group(1).strip()[:100]
        
        form_match = re.search(
            r'(?:Formação|Graduação|Curso)[:\s]*(?:em\s)?([A-Za-zÁ-ÿ\s\-]+?)(?:\n|\.|,)',
            texto_completo,
            re.IGNORECASE
        )
        if form_match:
            detalhes['formacao'] = form_match.group(1).strip()[:150]
        
        mandatos_match = re.search(
            r'(\d+)[ºª°]?\s*(?:mandato|legislatura)',
            texto_completo,
            re.IGNORECASE
        )
        if mandatos_match:
            detalhes['numero_mandatos'] = mandatos_match.group(1)
        
        comissoes_section = soup.find(text=re.compile(r'comissões?', re.IGNORECASE))
        if comissoes_section:
            parent = comissoes_section.parent
            if parent:
                comissoes_list = parent.find_next(['ul', 'ol', 'p'])
                if comissoes_list:
                    comissoes_text = comissoes_list.get_text().strip()
                    detalhes['comissoes'] = comissoes_text[:250]
        
        tel_match = re.search(
            r'(?:Tel(?:efone)?|Fone|Contato)[:\s]*(\([0-9]{2}\)\s*[0-9\-\s]+)',
            texto_completo,
            re.IGNORECASE
        )
        if tel_match:
            detalhes['telefones'] = tel_match.group(1).strip()[:50]
        else:
            tel_pattern = re.search(r'\(61\)\s*\d{4}\-\d{4}', texto_completo)
            if tel_pattern:
                detalhes['telefones'] = tel_pattern.group(0)
        
        email_match = re.search(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            texto_completo
        )
        if email_match:
            email = email_match.group(0)
            if 'camara.leg.br' in email.lower():
                detalhes['email'] = email
        
        periodo_match = re.search(
            r'(\d{4})\s*(?:-|a|até)\s*(\d{4})',
            texto_completo
        )
        if periodo_match:
            ano_inicio = periodo_match.group(1)
            ano_fim = periodo_match.group(2)
            detalhes['periodo_mandato'] = f"{ano_inicio} - {ano_fim}"
    
    except Exception as e:
        pass
    
    return detalhes

# ==========================================
# PARTE 6: FUNÇÕES AUXILIARES
# ==========================================

def extract_text_by_selectors(element, selectors: List[str]) -> str:
    for selector in selectors:
        try:
            elem = element.select_one(selector)
            if elem:
                text = elem.get_text().strip()
                if text and len(text) > 1:
                    return text
        except:
            continue
    return ""

def clean_deputada_name(name: str) -> str:
    if not name:
        return ""
    
    unwanted_phrases = [
        "pesquise", "deputado", "filtro", "buscar", "resultado",
        "página", "menu", "navegação", "ver mais", "clique"
    ]
    
    name_lower = name.lower()
    for phrase in unwanted_phrases:
        if phrase in name_lower:
            return ""
    
    name = name.strip()
    
    if len(name) < 3 or len(name) > 100:
        return ""
    
    if not any(c.isalpha() for c in name):
        return ""
    
    return name


def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.strip()[:50]


def is_valid_deputada_data(deputada_data: Dict) -> bool:
    if not deputada_data:
        return False
    
    name = deputada_data.get('nome', '')
    if not name or len(name) < 3:
        return False
    
    return True

# ==========================================
# PARTE 7: SALVAMENTO EM CSV
# ==========================================

def save_to_csv(deputadas_data: List[Dict], filename: str = "data/deputadas.csv") -> None:
    if not deputadas_data:
        print("   ✗ Nenhum dado para salvar\n")
        return
    
    try:
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'nome',
            'nome_civil',
            'partido',
            'uf',
            'periodo_mandato',
            'telefones',
            'email',
            'data_nascimento',
            'naturalidade',
            'profissao',
            'formacao',
            'numero_mandatos',
            'comissoes',
            'link_perfil',
            'fonte_dados',
            'url_fonte',
            'data_extracao',
            'metodo_extracao'
        ]
        
        print("5. Salvando dados em CSV...")
        print(f"   Arquivo: {filename}")
        print(f"   Campos: {len(fieldnames)} atributos (requisito: mínimo 11) ✓")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for deputada in deputadas_data:
                row = {field: deputada.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"   ✓ Dados salvos com sucesso!")
        print(f"   ✓ Total de deputadas: {len(deputadas_data)}")
        print(f"   ✓ Caminho completo: {Path(filename).absolute()}\n")
        
    except Exception as e:
        print(f"   ✗ Erro ao salvar CSV: {e}\n")

# ==========================================
# PARTE 8: ESTATÍSTICAS DOS DADOS
# ==========================================

def generate_statistics(deputadas_data: List[Dict]) -> Dict:
    if not deputadas_data:
        return {}
    
    stats = {
        "total_deputadas": len(deputadas_data),
        "por_partido": {},
        "por_uf": {}
    }
    
    for deputada in deputadas_data:
        partido = deputada.get('partido', 'N/A')
        uf = deputada.get('uf', 'N/A')
        
        stats["por_partido"][partido] = stats["por_partido"].get(partido, 0) + 1
        stats["por_uf"][uf] = stats["por_uf"].get(uf, 0) + 1
    
    stats["por_partido"] = dict(sorted(stats["por_partido"].items(), key=lambda x: x[1], reverse=True))
    stats["por_uf"] = dict(sorted(stats["por_uf"].items(), key=lambda x: x[1], reverse=True))
    
    return stats

# ==========================================
# PARTE 9: FUNÇÃO MAIN (ORQUESTRAÇÃO)
# ==========================================

def main():  
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 14 + "WEB SCRAPING - DEPUTADAS FEDERAIS" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    deputadas_data = scrape_deputadas_list()
    
    if deputadas_data:
        print("=" * 70)
        print("SCRAPING CONCLUÍDO COM SUCESSO! ✓")
        print("=" * 70)
        
        print("\n6. Gerando estatísticas dos dados...\n")
        stats = generate_statistics(deputadas_data)
        
        if stats:
            print("   ESTATÍSTICAS FINAIS:")
            print("   " + "-" * 50)
            print(f"   Total de deputadas: {stats['total_deputadas']}")
            
            print(f"\n   Distribuição por partido (Top 10):")
            for i, (partido, count) in enumerate(list(stats['por_partido'].items())[:10], 1):
                barra = "█" * min(count, 30)  # Limitar barra visual
                print(f"      {i:2}. {partido:15} {barra} {count}")
            
            print(f"\n   Distribuição por estado (Top 10):")
            for i, (uf, count) in enumerate(list(stats['por_uf'].items())[:10], 1):
                print(f"      {i:2}. {uf}: {count}")
        
        print("\n" + "=" * 70)
        save_to_csv(deputadas_data)
        
        print("=" * 70)
        print("AMOSTRA DOS DADOS (primeiras 3 deputadas):")
        print("-" * 70)
        for i, deputada in enumerate(deputadas_data[:3], 1):
            print(f"\n{i}. {deputada['nome']}")
            print(f"   Partido: {deputada.get('partido', 'N/A')} | UF: {deputada.get('uf', 'N/A')}")
            if deputada.get('periodo_mandato'):
                print(f"   Mandato: {deputada['periodo_mandato']}")
            if deputada.get('email'):
                print(f"   Email: {deputada['email']}")
            if deputada.get('telefones'):
                print(f"   Telefone: {deputada['telefones']}")
            if deputada.get('naturalidade'):
                print(f"   Naturalidade: {deputada['naturalidade']}")
            print(f"   Perfil: {deputada['link_perfil']}")
        
        print()
        
    else:
        print("=" * 70)
        print("FALHA NO SCRAPING - Nenhum dado coletado ✗")
        print("=" * 70)
        print("\nPOSSÍVEIS CAUSAS:")
        print("  • Site mudou estrutura HTML")
        print("  • Bloqueio anti-bot (403 Forbidden)")
        print("  • Problemas de conectividade (timeout)")
        print("  • Filtro de gênero não funcionou")
        print("\nSUGESTÕES:")
        print("  • Verificar se a URL ainda está acessível")
        print("  • Testar manualmente no navegador")
        print("  • Verificar estrutura HTML da página")
        print()
    
    print("=" * 70)
    print("FIM DO PROCESSO")
    print("=" * 70)
    print()
    
    return deputadas_data

if __name__ == "__main__":
    main()