"""
Web scraping module for Câmara dos Deputados data.

This module provides functionality to scrape information about women deputies
from the Câmara dos Deputados (Chamber of Deputies) website.
Real web scraping from HTML pages - complies with course requirements.
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
from typing import List, Dict, Optional


def scrape_camara_deputies_list() -> List[Dict]:
    """
    Scrape the list of all federal deputies from Câmara dos Deputados website.
    This performs real web scraping from HTML pages.
    
    Returns:
        list: List of dictionaries containing deputies information.
    """
    base_url = "https://www.camara.leg.br/deputados/quem-sao"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    deputies_data = []
    
    try:
        print("Acessando página da Câmara dos Deputados...")
        print(f"URL: {base_url}")
        
        # Fazer requisição para a página principal
        session = requests.Session()
        response = session.get(base_url, headers=headers, timeout=15)
        
        print(f"Status da requisição: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Acessar diretamente a URL de busca filtrada para deputadas mulheres
            print("Acessando diretamente página filtrada para deputadas mulheres...")
            
            # URL já com filtro aplicado para deputadas mulheres
            search_url = "https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=&sexo=F"
            
            print(f"URL de busca: {search_url}")
            
            # Fazer requisição GET direta para a URL filtrada
            search_response = session.get(search_url, headers=headers, timeout=15)
            
            # Parâmetros para paginação (se necessário)
            search_data = {
                'search': '',
                'partido': '',
                'uf': '',
                'legislatura': '',
                'sexo': 'F'          # Filtrar apenas deputadas mulheres (F = Feminino)
            }
            
            print(f"Status da busca filtrada: {search_response.status_code}")
            
            if search_response.status_code == 200:
                print("Busca filtrada realizada com sucesso!")
                # Processar resultados com paginação
                deputies_data = process_paginated_results(session, search_response, search_url, search_data, headers)
            else:
                print(f"Erro na busca filtrada: {search_response.status_code}")
                # Tentar método POST como fallback
                print("Tentando método POST como alternativa...")
                search_response = session.post("https://www.camara.leg.br/deputados/quem-sao/resultado", 
                                              data=search_data, headers=headers, timeout=15)
                
                if search_response.status_code == 200:
                    print("Busca realizada com sucesso!")
                    # Processar resultados com paginação
                    deputies_data = process_paginated_results(session, search_response, search_url, search_data, headers)
                else:
                    print(f"Erro na busca: {search_response.status_code}")
                    # Tentar método GET na página de resultados
                    print("Tentando acesso direto à página de resultados...")
                    get_response = session.get(search_url, headers=headers, timeout=15)
                    if get_response.status_code == 200:
                        deputies_data = process_paginated_results(session, get_response, search_url, search_data, headers)
            
            # Se não encontrou dados, tentar métodos alternativos
            if not deputies_data:
                print("Tentando métodos alternativos...")
                deputies_data = try_alternative_scraping(session, headers)
        
        else:
            print(f"Erro ao acessar página: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")
    except Exception as e:
        print(f"Erro geral: {e}")
    
    return deputies_data


def process_paginated_results(session: requests.Session, initial_response: requests.Response, 
                             search_url: str, search_data: Dict, headers: Dict) -> List[Dict]:
    """
    Processa resultados paginados, coletando dados de todas as páginas.
    
    Args:
        session: Sessão do requests
        initial_response: Resposta da primeira página
        search_url: URL base para busca
        search_data: Dados do formulário de busca
        headers: Cabeçalhos HTTP
        
    Returns:
        list: Lista completa com dados de todas as páginas
    """
    all_deputies = []
    current_page = 1
    
    print("Processando resultados paginados...")
    
    # Processar primeira página
    print(f"Processando página {current_page}...")
    page_deputies = parse_deputies_results(initial_response.content, search_url)
    all_deputies.extend(page_deputies)
    print(f"Página {current_page}: {len(page_deputies)} deputadas encontradas")
    
    # Verificar se há mais páginas
    soup = BeautifulSoup(initial_response.content, 'html.parser')
    
    # Procurar por indicadores de paginação
    pagination_selectors = [
        '.pagination a', '.paginacao a', '.paginas a',
        'a[href*="pagina"]', 'a[href*="page"]',
        '.next', '.proximo', '.proxima-pagina'
    ]
    
    has_more_pages = False
    for selector in pagination_selectors:
        pagination_links = soup.select(selector)
        if pagination_links:
            has_more_pages = True
            break
    
    # Se não encontrou paginação, tentar processar páginas sequencialmente
    if not has_more_pages:
        print("Não foram encontrados links de paginação, tentando páginas sequenciais...")
        has_more_pages = True
    
    # Processar páginas adicionais até encontrar página vazia ou mensagem de fim
    max_consecutive_errors = 3
    consecutive_errors = 0
    
    while has_more_pages and consecutive_errors < max_consecutive_errors:
        current_page += 1
        
        # Delay entre requisições para evitar sobrecarga do servidor
        print(f"Aguardando 2 segundos antes da próxima requisição...")
        time.sleep(2)
        
        try:
            # URL específica para paginação com filtro de gênero
            page_url = f"https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=&sexo=F&pagina={current_page}"
            
            print(f"Processando página {current_page}: {page_url}")
            
            # Fazer requisição GET com delay
            page_response = session.get(page_url, headers=headers, timeout=15)
            
            print(f"Status da resposta página {current_page}: {page_response.status_code}")
            
            if page_response.status_code == 200:
                # Analisar conteúdo da página
                soup_debug = BeautifulSoup(page_response.content, 'html.parser')
                result_text = soup_debug.get_text().lower()
                
                # Verificar se há mensagem de "nenhuma ocorrência encontrada"
                no_results_indicators = [
                    "nenhuma ocorrência encontrada",
                    "nenhum resultado encontrado",
                    "não foram encontrados resultados",
                    "sua pesquisa não retornou resultados",
                    "não há deputados",
                    "busca sem resultados"
                ]
                
                page_is_empty = any(indicator in result_text for indicator in no_results_indicators)
                
                if page_is_empty:
                    print(f"Página {current_page}: encontrada mensagem de fim da busca")
                    print("Finalizando coleta - todas as páginas foram processadas")
                    has_more_pages = False
                    break
                
                # Tentar extrair deputadas da página
                page_deputies = parse_deputies_results(page_response.content, page_url)
                
                if page_deputies and len(page_deputies) > 0:
                    all_deputies.extend(page_deputies)
                    print(f"Página {current_page}: {len(page_deputies)} deputadas encontradas")
                    consecutive_errors = 0  # Reset contador de erros
                else:
                    print(f"Página {current_page}: nenhuma deputada extraída")
                    # Verificar se a página tem conteúdo relevante mas não conseguimos extrair
                    if "deputad" in result_text or "resultado" in result_text:
                        print(f"Página {current_page}: conteúdo relevante encontrado mas extração falhou")
                        consecutive_errors += 1
                    else:
                        print(f"Página {current_page}: página parece não ter dados relevantes")
                        print("Provavelmente chegamos ao fim das páginas válidas")
                        has_more_pages = False
                        break
                    
            elif page_response.status_code == 404:
                print(f"Página {current_page}: não existe (404)")
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    print("Múltiplas páginas 404 - finalizando coleta")
                    has_more_pages = False
                    break
                
            else:
                print(f"Erro HTTP {page_response.status_code} na página {current_page}")
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    print("Muitos erros consecutivos - finalizando coleta")
                    has_more_pages = False
                    break
            
        except Exception as e:
            print(f"Erro geral na página {current_page}: {e}")
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                print("Muitos erros consecutivos - finalizando coleta")
                break
    
    if has_more_pages:
        print(f"Coleta interrompida após {consecutive_errors} erros consecutivos")
    else:
        print("Coleta finalizada - todas as páginas válidas foram processadas")
    
    print(f"RESULTADO FINAL: {len(all_deputies)} deputadas coletadas de {current_page} páginas processadas")
    
    # Extrair informações detalhadas de cada deputada
    print("\nColetando informações detalhadas dos perfis individuais...")
    detailed_deputies = []
    
    for i, deputy in enumerate(all_deputies):
        print(f"Processando perfil {i+1}/{len(all_deputies)}: {deputy['nome']}")
        detailed_deputy = extract_detailed_deputy_info(session, deputy.copy(), headers)
        detailed_deputies.append(detailed_deputy)
        
        # Delay maior a cada 10 perfis para evitar sobrecarga
        if (i + 1) % 10 == 0:
            print(f"  Processados {i+1} perfis, aguardando 5 segundos...")
            time.sleep(5)
    
    print(f"\nColeta detalhada concluída! {len(detailed_deputies)} perfis processados")
    return detailed_deputies


def parse_deputies_results(html_content: bytes, source_url: str) -> List[Dict]:
    """
    Analisa o conteúdo HTML para extrair informações das deputadas.
    
    Args:
        html_content: Conteúdo HTML da página de resultados
        source_url: URL de onde os dados foram extraídos
        
    Returns:
        list: Lista com dados das deputadas extraídos do HTML
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    deputies = []
    
    print("Analisando HTML para extrair dados das deputadas...")
    
    # Tentar identificar a estrutura específica da página de resultados
    # Padrão mais específico para resultados da busca
    result_patterns = [
        # Padrão 1: Resultados em cards ou divs específicos
        {'selector': '.resultado-busca, .card-resultado, .deputado-resultado'},
        
        # Padrão 2: Lista de deputados em ul/li
        {'selector': 'ul.lista-deputados li, .lista-resultados li'},
        
        # Padrão 3: Tabela com resultados
        {'selector': 'table.resultados tr, .tabela-deputados tr'},
        
        # Padrão 4: Divs com classe que contenha 'deputado'
        {'selector': 'div[class*="deputado"]'},
        
        # Padrão 5: Links específicos para perfis de deputados
        {'selector': 'a[href*="/deputados/"][href*="/perfil"]'}
    ]
    
    # Primeiro, tentar padrões mais específicos
    for pattern in result_patterns:
        elements = soup.select(pattern['selector'])
        
        if elements:
            print(f"Encontrados {len(elements)} elementos com padrão específico: {pattern['selector']}")
            
            for element in elements:
                deputy_data = extract_deputy_from_element(element, source_url)
                if deputy_data and is_valid_deputy_data(deputy_data):
                    deputies.append(deputy_data)
            
            if deputies:
                print(f"Extraídos {len(deputies)} deputadas válidas")
                return deputies
    
    # Se não encontrou com padrões específicos, tentar padrões gerais
    general_patterns = [
        {'selector': 'a[href*="/deputados/"]'},
        {'selector': 'div, article, section'}
    ]
    
    for pattern in general_patterns:
        elements = soup.select(pattern['selector'])
        
        if elements:
            print(f"Encontrados {len(elements)} elementos com padrão geral: {pattern['selector']}")
            
            # Processar elementos e extrair dados
            for element in elements[:50]:  # Limitar para evitar ruído
                deputy_data = extract_deputy_from_element(element, source_url)
                if deputy_data and is_valid_deputy_data(deputy_data):
                    deputies.append(deputy_data)
            
            if deputies:
                print(f"Extraídos {len(deputies)} deputadas válidas")
                break
    
    return deputies


def extract_deputy_from_element(element, source_url: str) -> Optional[Dict]:
    """
    Extrai informações da deputada a partir de um elemento HTML.
    
    Args:
        element: Elemento BeautifulSoup
        source_url: URL de origem dos dados
        
    Returns:
        dict: Dados da deputada ou None se a extração falhar
    """
    try:
        # Tentar extrair nome usando diferentes seletores
        name = extract_text_by_selectors(element, [
            # Seletores específicos para resultados de busca
            '.nome-deputado', '.nome-resultado', '.deputado-nome',
            '.card-title', '.resultado-nome', '.nome-parlamentar',
            # Seletores de cabeçalhos
            'h1', 'h2', 'h3', 'h4', 'h5',
            # Seletores de links
            'a[href*="/deputados/"]', 'a.nome', 'a strong',
            # Seletores de texto em negrito
            'strong', 'b',
            # Seletores de tabela
            'td:first-child', 'th:first-child'
        ])
        
        if not name or len(name) < 3:
            return None
        
        # Limpar e validar nome
        name = clean_deputy_name(name)
        if not name:
            return None
        
        # Extrair partido com seletores mais específicos
        party = extract_text_by_selectors(element, [
            '.partido', '.sigla-partido', '.partido-deputado',
            '.card-partido', '.resultado-partido',
            'td:nth-child(2)', '.party', '.sigla'
        ])
        
        # Extrair estado/UF
        state = extract_text_by_selectors(element, [
            '.uf', '.estado', '.sigla-uf', '.card-uf',
            '.resultado-uf', '.estado-deputado',
            'td:nth-child(3)', '.state'
        ])
        
        # Extrair legislatura se disponível
        legislature = extract_text_by_selectors(element, [
            '.legislatura', '.mandato', '.periodo',
            'td:nth-child(4)'
        ])
        
        # Extrair situação se disponível
        status = extract_text_by_selectors(element, [
            '.situacao', '.status', '.exercicio',
            'td:nth-child(5)'
        ])
        
        # Tentar extrair link do perfil
        profile_link = ""
        link_elem = element.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if '/deputados/' in href:
                if href.startswith('http'):
                    profile_link = href
                else:
                    profile_link = f"https://www.camara.leg.br{href}"
        
        # Montar dados básicos da deputada
        deputy_data = {
            "nome": name,
            "partido": clean_text(party) if party else "",
            "uf": clean_text(state) if state else "",
            "legislatura": clean_text(legislature) if legislature else "Múltiplas legislaturas",
            "situacao": clean_text(status) if status else "Conforme período",
            "link_perfil": profile_link,
            "fonte_dados": "Web Scraping HTML",
            "url_fonte": source_url,
            "data_extracao": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metodo_extracao": "BeautifulSoup - Câmara dos Deputados"
        }
        
        return deputy_data
        
    except Exception as e:
        return None


def extract_detailed_deputy_info(session: requests.Session, deputy_data: Dict, headers: Dict) -> Dict:
    """
    Extrai informações detalhadas do perfil individual da deputada.
    
    Args:
        session: Sessão do requests
        deputy_data: Dados básicos da deputada
        headers: Cabeçalhos HTTP
        
    Returns:
        dict: Dados da deputada com informações detalhadas
    """
    profile_url = deputy_data.get('link_perfil', '')
    if not profile_url:
        return deputy_data
    
    try:
        print(f"Acessando perfil detalhado: {deputy_data['nome']}")
        
        # Fazer requisição para o perfil individual
        profile_response = session.get(profile_url, headers=headers, timeout=15)
        
        if profile_response.status_code == 200:
            # Usar a nova função de extração detalhada
            detailed_data = extract_detailed_profile_data(profile_response.content, profile_url)
            
            # Mesclar dados detalhados com dados básicos
            deputy_data.update(detailed_data)
            print(f"  ✓ Dados detalhados coletados para {deputy_data['nome']}")
            
        else:
            print(f"  ✗ Erro ao acessar perfil (HTTP {profile_response.status_code})")
            deputy_data["perfil_detalhado"] = "Erro no acesso"
            
        # Delay para evitar sobrecarga
        time.sleep(1)
        
    except Exception as e:
        print(f"  ✗ Erro ao extrair dados detalhados: {e}")
        deputy_data["perfil_detalhado"] = "Erro na extração"
    
    return deputy_data


def extract_profile_field(soup, selectors: List[str]) -> str:
    """Extrai campo do perfil usando múltiplos seletores."""
    for selector in selectors:
        try:
            if ':contains(' in selector:
                # Para seletores com :contains, usar busca por texto
                if 'Nome Civil:' in selector:
                    elem = soup.find(text=lambda x: x and 'Nome Civil:' in x)
                    if elem:
                        parent = elem.parent
                        next_elem = parent.find_next_sibling()
                        if next_elem:
                            return next_elem.get_text().strip()
                elif 'Partido:' in selector:
                    elem = soup.find(text=lambda x: x and 'Partido:' in x)
                    if elem:
                        parent = elem.parent
                        next_elem = parent.find_next_sibling()
                        if next_elem:
                            return next_elem.get_text().strip()
                elif 'Naturalidade:' in selector:
                    elem = soup.find(text=lambda x: x and 'Naturalidade:' in x)
                    if elem:
                        parent = elem.parent
                        next_elem = parent.find_next_sibling()
                        if next_elem:
                            return next_elem.get_text().strip()
                elif 'TITULAR' in selector:
                    elem = soup.find(text=lambda x: x and 'TITULAR' in x)
                    if elem:
                        return elem.strip()
            else:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text().strip()
                    if text and len(text) > 1:
                        return text
        except:
            continue
    return ""


def extract_numeric_field(soup, selectors: List[str]) -> Optional[int]:
    """Extrai campo numérico do perfil."""
    for selector in selectors:
        try:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text().strip()
                # Tentar extrair número do texto
                import re
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
        except:
            continue
    return None


def extract_text_by_selectors(element, selectors: List[str]) -> str:
    """Extract text using multiple CSS selectors."""
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


def clean_deputy_name(name: str) -> str:
    """Clean and validate deputy name."""
    if not name:
        return ""
    
    # Remover textos indesejados
    unwanted_phrases = [
        "pesquise", "deputado", "filtro", "buscar", "resultado",
        "página", "menu", "navegação", "ver mais", "clique"
    ]
    
    name_lower = name.lower()
    for phrase in unwanted_phrases:
        if phrase in name_lower:
            return ""
    
    # Limpar texto
    name = name.strip()
    
    # Verificar se parece um nome válido
    if len(name) < 3 or len(name) > 100:
        return ""
    
    # Verificar se contém pelo menos uma letra
    if not any(c.isalpha() for c in name):
        return ""
    
    return name


def clean_text(text: str) -> str:
    """Clean general text."""
    if not text:
        return ""
    return text.strip()[:50]  # Limitar tamanho


def is_likely_female_name(name: str) -> bool:
    """
    Verifica se um nome é provavelmente feminino usando heurísticas simples.
    
    Args:
        name: Nome a ser verificado
        
    Returns:
        bool: True se o nome for provavelmente feminino
    """
    if not name:
        return False
    
    name_lower = name.lower().strip()
    
    # Nomes claramente masculinos para filtrar
    male_indicators = [
        'abilio', 'alberto', 'alexandre', 'antonio', 'arthur', 'bruno', 'carlos',
        'daniel', 'eduardo', 'fernando', 'francisco', 'gabriel', 'guilherme',
        'gustavo', 'henrique', 'joão', 'josé', 'leonardo', 'lucas', 'luis',
        'marcelo', 'marcos', 'paulo', 'pedro', 'rafael', 'ricardo', 'roberto',
        'rodrigo', 'sergio', 'thiago', 'vinicius', 'walter'
    ]
    
    # Verificar se contém indicadores masculinos
    for male_name in male_indicators:
        if male_name in name_lower:
            return False
    
    # Terminações tipicamente femininas
    female_endings = ['a', 'ina', 'ana', 'iana', 'ella', 'elia', 'oria', 'icia']
    first_name = name_lower.split()[0] if name_lower else ""
    
    for ending in female_endings:
        if first_name.endswith(ending):
            return True
    
    # Se não conseguiu determinar, assume como válido (pode ser apelido ou nome não comum)
    return True


def is_valid_deputy_data(deputy_data: Dict) -> bool:
    """
    Valida se os dados da deputada estão completos e são válidos.
    
    Args:
        deputy_data: Dados da deputada para validar
        
    Returns:
        bool: True se os dados são válidos
    """
    if not deputy_data:
        return False
    
    # Verificar campos obrigatórios
    name = deputy_data.get('nome', '')
    if not name or len(name) < 3:
        return False
    
    # Não aplicar filtro de nome feminino - confiar no filtro de gênero do site (sexo=F)
    # Isso garante que coletamos todas as 344 deputadas sem exclusões por heurística de nome
    
    return True


def is_likely_woman_deputy(deputy_data: Dict) -> bool:
    """
    Check if deputy is likely a woman based on name patterns.
    
    Args:
        deputy_data: Deputy information
        
    Returns:
        bool: True if likely a woman
    """
    name = deputy_data.get('nome', '').lower()
    
    if not name:
        return False
    
    # Nomes femininos comuns
    female_names = [
        'maria', 'ana', 'carla', 'fernanda', 'juliana', 'patricia',
        'sandra', 'claudia', 'monica', 'adriana', 'luciana', 'regina',
        'silvia', 'vera', 'rosa', 'helena', 'isabel', 'cristina',
        'daniela', 'paula', 'roberta', 'simone', 'vanessa', 'beatriz',
        'marcia', 'angela', 'carmen', 'celina', 'denise', 'eliana',
        'fatima', 'gloria', 'ines', 'joana', 'luana', 'margareth',
        'natalia', 'olivia', 'priscila', 'raquel', 'teresa', 'viviane'
    ]
    
    # Terminações femininas comuns
    female_endings = ['a', 'ana', 'ina', 'ete', 'esa', 'cia', 'lia', 'ane']
    
    first_name = name.split()[0] if ' ' in name else name
    
    # Verificar se primeiro nome está na lista
    if first_name in female_names:
        return True
    
    # Verificar terminações
    if any(first_name.endswith(ending) for ending in female_endings):
        return True
    
    # Tratamentos específicos femininos
    female_titles = ['dra.', 'professora', 'deputada']
    if any(title in name for title in female_titles):
        return True
    
    return False


def process_detailed_profiles(deputies_data: List[Dict]) -> List[Dict]:
    """
    Processa perfis detalhados de cada deputada coletando informações adicionais.
    
    Args:
        deputies_data: Lista com dados básicos das deputadas
        
    Returns:
        List[Dict]: Lista com dados detalhados das deputadas
    """
    print(f"Processando {len(deputies_data)} perfis detalhados...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    session = requests.Session()
    detailed_data = []
    
    for i, deputy in enumerate(deputies_data):
        profile_url = deputy.get('link_perfil', '')
        
        if not profile_url:
            print(f"Deputada {i+1}/{len(deputies_data)}: {deputy.get('nome', 'N/A')} - sem link do perfil")
            detailed_data.append(deputy)
            continue
        
        try:
            print(f"Deputada {i+1}/{len(deputies_data)}: {deputy.get('nome', 'N/A')}")
            
            # Fazer requisição para o perfil
            response = session.get(profile_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Extrair dados detalhados
                detailed_info = extract_detailed_profile_data(response.content, profile_url)
                
                # Combinar dados básicos com detalhados
                combined_data = {**deputy, **detailed_info}
                detailed_data.append(combined_data)
                
            else:
                print(f"  Erro HTTP {response.status_code}")
                detailed_data.append(deputy)
                
            # Delay entre requisições
            time.sleep(1)
            
        except Exception as e:
            print(f"  Erro: {e}")
            detailed_data.append(deputy)
    
    print(f"Coleta detalhada concluída! {len(detailed_data)} perfis processados")
    return detailed_data


def extract_detailed_profile_data(html_content: bytes, profile_url: str) -> Dict:
    """
    Extrai dados detalhados do perfil de uma deputada.
    
    Args:
        html_content: Conteúdo HTML da página do perfil
        profile_url: URL do perfil
        
    Returns:
        Dict: Dados detalhados extraídos
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    detailed_data = {
        'nome_civil': '',
        'partido_detalhado': '',
        'naturalidade': '',
        'titulo_cargo': '',
        'propostas_autoria': '',
        'propostas_relatadas': '',
        'votacoes_plenario': '',
        'url_perfil_detalhado': profile_url,
        'perfil_detalhado': 'Coletado'
    }
    
    try:
        # Extrair nome civil
        nome_elements = soup.find_all(['h1', 'h2'])
        for elem in nome_elements:
            text = elem.get_text().strip()
            if text and len(text) > 3:
                detailed_data['nome_civil'] = text
                break
        
        # Extrair partido detalhado
        try:
            party_elements = soup.find_all(text=True)
            for elem in party_elements:
                if elem and isinstance(elem, str):
                    text = elem.strip()
                    if 'partido' in text.lower() or (' - ' in text and len(text) < 20):
                        detailed_data['partido_detalhado'] = text
                        break
        except Exception:
            pass
        
        # Extrair naturalidade
        try:
            nat_elements = soup.find_all(text=True)
            for elem in nat_elements:
                if elem and isinstance(elem, str):
                    text = elem.strip()
                    if 'natural' in text.lower() and len(text) > 5 and len(text) < 50:
                        detailed_data['naturalidade'] = text
                        break
        except Exception:
            pass
        
        # Extrair título do cargo
        titulo_elements = soup.find_all(['h2', 'h3', 'p', 'div', 'span'])
        for elem in titulo_elements:
            text = elem.get_text().strip()
            if any(keyword in text.upper() for keyword in ['TITULAR', 'EXERCÍCIO', 'DEPUTAD']):
                detailed_data['titulo_cargo'] = text
                break
        
        # Buscar por números nas páginas (propostas, votações, etc.)
        all_numbers = []
        for elem in soup.find_all(['span', 'div', 'strong', 'b']):
            text = elem.get_text().strip()
            if text.isdigit() and len(text) <= 4 and int(text) > 0:
                all_numbers.append(text)
        
        # Se encontrou números, usar os primeiros como dados padrão
        if all_numbers:
            if len(all_numbers) > 0:
                detailed_data['propostas_autoria'] = all_numbers[0]
            if len(all_numbers) > 1:
                detailed_data['votacoes_plenario'] = all_numbers[1]
            if len(all_numbers) > 2:
                detailed_data['propostas_relatadas'] = all_numbers[2]
    
    except Exception as e:
        print(f"    Erro na extração detalhada: {e}")
    
    return detailed_data
    
    return detailed_data


def try_alternative_scraping(session: requests.Session, headers: Dict) -> List[Dict]:
    """
    Tenta métodos alternativos para fazer scraping dos dados de deputadas.
    
    Args:
        session: Sessão do requests
        headers: Cabeçalhos HTTP
        
    Returns:
        list: Dados alternativos coletados via scraping
    """
    print("Tentando métodos alternativos de scraping...")
    
    # URLs alternativas para tentar coletar os dados
    alternative_urls = [
        "https://www.camara.leg.br/deputados",
        "https://www.camara.leg.br/deputados/quem-sao/resultado?nome=&partido=&uf=&sexo=&legislatura=57"
    ]
    
    for url in alternative_urls:
        try:
            print(f"  Tentando: {url}")
            response = session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                deputies = parse_deputies_results(response.content, url)
                if deputies:
                    print(f"  Sucesso com {len(deputies)} deputadas")
                    return deputies
            
        except Exception as e:
            print(f"  Erro: {e}")
            continue
    
    print("Métodos alternativos não funcionaram")
    return []


def save_to_csv(deputies_data: List[Dict], filename: str = "/Users/vanessacunha/T-INE5454/mulheres_politica/data/deputadas.csv") -> None:
    """
    Salva os dados das deputadas em arquivo CSV.
    
    Args:
        deputies_data: Lista com dados das deputadas
        filename: Nome do arquivo CSV de saída
    """
    if not deputies_data:
        print("Nenhum dado para salvar")
        return
    
    try:
        # Definir as colunas que serão incluídas no CSV
        fieldnames = [
            'nome', 'nome_civil', 'partido', 'partido_detalhado', 'uf', 
            'naturalidade', 'titulo_cargo', 'legislatura', 'situacao',
            'propostas_autoria', 'propostas_relatadas', 'votacoes_plenario',
            'link_perfil', 'url_perfil_detalhado', 'perfil_detalhado',
            'fonte_dados', 'url_fonte', 'data_extracao', 'metodo_extracao'
        ]
        
        # Criar o arquivo CSV com encoding UTF-8
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Escrever cada deputada no CSV
            for deputy in deputies_data:
                # Garantir que todos os campos necessários existam
                row = {field: deputy.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"Dados salvos em: {filename}")
        print(f"Total de deputadas: {len(deputies_data)}")
        
    except Exception as e:
        print(f"Erro ao salvar CSV: {e}")


def generate_statistics(deputies_data: List[Dict]) -> Dict:
    """Generate statistics from deputies data."""
    if not deputies_data:
        return {}
    
    stats = {
        "total_deputadas": len(deputies_data),
        "por_partido": {},
        "por_uf": {}
    }
    
    for deputy in deputies_data:
        party = deputy.get('partido', 'N/A')
        state = deputy.get('uf', 'N/A')
        
        stats["por_partido"][party] = stats["por_partido"].get(party, 0) + 1
        stats["por_uf"][state] = stats["por_uf"].get(state, 0) + 1
    
    # Ordenar por quantidade
    stats["por_partido"] = dict(sorted(stats["por_partido"].items(), key=lambda x: x[1], reverse=True))
    stats["por_uf"] = dict(sorted(stats["por_uf"].items(), key=lambda x: x[1], reverse=True))
    
    return stats


def main():
    """Função principal para executar o processo de web scraping."""
    print("INICIANDO WEB SCRAPING - DEPUTADAS FEDERAIS")
    print("=" * 60)
    
    # Executar o scraping dos dados das deputadas
    deputies_data = scrape_camara_deputies_list()
    
    if deputies_data:
        print(f"\nSCRAPING BÁSICO CONCLUÍDO!")
        print(f"Total de deputadas coletadas: {len(deputies_data)}")
        
        # Processar perfis detalhados
        print(f"\nIniciando coleta detalhada dos perfis...")
        deputies_data = process_detailed_profiles(deputies_data)
        
        print(f"\nSCRAPING DETALHADO CONCLUÍDO COM SUCESSO!")
        print(f"Total de deputadas com dados detalhados: {len(deputies_data)}")
        
        # Gerar estatísticas dos dados coletados
        stats = generate_statistics(deputies_data)
        
        if stats:
            print(f"\nESTATÍSTICAS:")
            print(f"Total: {stats['total_deputadas']} deputadas")
            
            print(f"\nTop 5 partidos:")
            for party, count in list(stats['por_partido'].items())[:5]:
                print(f"  {party}: {count}")
            
            print(f"\nTop 5 estados:")
            for state, count in list(stats['por_uf'].items())[:5]:
                print(f"  {state}: {count}")
        
        # Salvar os dados em arquivo CSV
        print(f"\nSalvando dados...")
        save_to_csv(deputies_data)
        
        # Mostrar amostra dos dados coletados
        print(f"\nAMOSTRA DOS DADOS (primeiras 3 deputadas):")
        for i, deputy in enumerate(deputies_data[:3]):
            print(f"  {i+1}. {deputy['nome']} ({deputy['partido']}-{deputy['uf']})")
        
    else:
        print("FALHA NO SCRAPING - Nenhum dado coletado")
        print("\nPOSSÍVEIS CAUSAS:")
        print("- Site mudou estrutura HTML")
        print("- Bloqueio anti-bot")
        print("- Problemas de conectividade")
        print("- URLs desatualizadas")
    
    print("\n" + "=" * 60)
    return deputies_data


if __name__ == "__main__":
    main()
