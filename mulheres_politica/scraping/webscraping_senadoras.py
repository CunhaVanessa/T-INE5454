"""
Web scraping module for Senado Federal data.

Este módulo coleta informações sobre mulheres senadoras
do site do Senado Federal brasileiro.
"""

import json
import requests
from bs4 import BeautifulSoup
import csv
import time
from typing import List, Dict
from pathlib import Path
import re


def scrape_senadoras_list() -> List[Dict]:
    """
    Faz scraping da lista de senadoras em exercício.
    Usa a URL com filtro por sexo do próprio site.
    """
    
    base_url = "https://www25.senado.leg.br/web/senadores/em-exercicio/-/e/por-sexo"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    senadoras_data = []
    
    try:
        print("=" * 70)
        print("INICIANDO WEB SCRAPING - SENADORAS FEDERAIS")
        print("=" * 70)
        print(f"\n1. Acessando página com filtro de GÊNERO FEMININO...")
        print(f"   URL: {base_url}")
        
        response = requests.get(base_url, headers=headers, timeout=15)
        
        print(f"   Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ Página acessada com sucesso!\n")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            senadoras_data = extract_senadoras_from_filtered_table(soup, base_url, headers)
        else:
            print(f"  ✗ Erro ao acessar página: HTTP {response.status_code}\n")
            
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Erro de conexão: {e}\n")
    except Exception as e:
        print(f"  ✗ Erro geral: {e}\n")
    
    return senadoras_data


def extract_senadoras_from_filtered_table(soup: BeautifulSoup, source_url: str, headers: Dict) -> List[Dict]:
    
    senadoras = []

    total_homens = 0
    
    print("2. Localizando tabela e seção 'Feminino'...")
    
    table = soup.find('table')
    
    if not table:
        print("  ✗ Tabela não encontrada no HTML\n")
        return senadoras
    
    print("  ✓  Tabela encontrada!")
    
    rows = table.find_all('tr')
    
    inside_feminino_section = False
    inside_masculino_section = False
    total_senadoras = 0
    
    print("   Procurando seção 'Feminino'...\n")
    
    for row in rows:
        row_text = row.get_text().strip()
        
        if 'Feminino' in row_text and row_text == 'Feminino':
            inside_feminino_section = True
            print("3.   ✓ Seção 'Feminino' encontrada! Extraindo senadoras...\n")
            continue
        
        if 'Masculino' in row_text and row_text == 'Masculino':
            inside_feminino_section = False
            inside_masculino_section = True
            print(f"\n4.  Seção 'Masculino' encontrada - parando extração ✗")
            print(f"\n   Seção 'Masculino' encontrada. Contando senadores homens...")
            print(f"    ✓ Total de senadoras coletadas: {total_senadoras}\n")
            continue
        
        cells = row.find_all('td')
        
        if len(cells) >= 2:

            if inside_feminino_section:
                cells = row.find_all('td')
                
                if len(cells) >= 6:
                    try:
                        nome_cell = cells[0]
                        nome_link = nome_cell.find('a')
                        
                        if nome_link:
                            nome = nome_link.get_text().strip()
                            perfil_url = nome_link.get('href', '')
                            
                            if perfil_url and not perfil_url.startswith('http'):
                                perfil_url = f"https://www25.senado.leg.br{perfil_url}"
                        else:
                            continue
                        
                        partido = cells[1].get_text().strip()
                        uf = cells[2].get_text().strip()
                        periodo = cells[3].get_text().strip()
                        telefones = cells[4].get_text().strip()
                        email = cells[5].get_text().strip()
                        
                        print(f"   ✓ Senadora encontrada: {nome} ({partido}-{uf})")
                        
                        senadora_data = {
                            'nome': nome,
                            'partido': partido,
                            'uf': uf,
                            'periodo_mandato': periodo,
                            'telefones': telefones,
                            'email': email,
                            'link_perfil': perfil_url,
                            'fonte_dados': 'Web Scraping HTML',
                            'url_fonte': source_url,
                            'data_extracao': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'metodo_extracao': 'BeautifulSoup - Senado Federal (filtro por sexo)'
                        }
                        
                        senadoras.append(senadora_data)
                        total_senadoras += 1
                    
                    except Exception as e:
                        print(f"   ⚠ Erro ao processar linha: {e}")
                        continue
            
            elif inside_masculino_section:
                if cells[0].find('a'):
                    total_homens += 1

    stats = {"total_homens": total_homens}
    with open('data/temp_stats_senado.json', 'w') as f:
        json.dump(stats, f)
    print(f"\n   Contagem finalizada: {len(senadoras)} Mulheres e {total_homens} Homens.")
         
    if senadoras:
        print("\n5. Coletando informações detalhadas dos perfis individuais...\n")
        senadoras = collect_detailed_profiles(senadoras, headers)
    else:
        print("\n   ✗ Nenhuma senadora foi encontrada na seção 'Feminino'\n")
    
    return senadoras


def collect_detailed_profiles(senadoras: List[Dict], headers: Dict) -> List[Dict]:
    
    detailed_senadoras = []
    
    for i, senadora in enumerate(senadoras, 1):
        nome = senadora['nome']
        perfil_url = senadora.get('link_perfil', '')
        
        print(f"   [{i}/{len(senadoras)}] Processando: {nome}")
        
        if not perfil_url:
            print(f"                Sem URL de perfil, pulando...")
            detailed_senadoras.append(senadora)
            continue
        
        try:
            response = requests.get(perfil_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                detalhes = extract_profile_details(soup, perfil_url)
                
                senadora_completa = {**senadora, **detalhes}
                detailed_senadoras.append(senadora_completa)
                
                print(f"              ✓   Dados detalhados coletados")
            else:
                print(f"              ✗  Erro HTTP {response.status_code}")
                detailed_senadoras.append(senadora)
            
            time.sleep(1.5)
            
        except Exception as e:
            print(f"              ✗ Erro: {e}")
            detailed_senadoras.append(senadora)
    
    print()
    return detailed_senadoras


def extract_profile_details(soup: BeautifulSoup, perfil_url: str) -> Dict:
     
    detalhes = {
        'nome_civil': '',
        'data_nascimento': '',
        'naturalidade': '',
        'profissao': '',
        'formacao': '',
        'numero_mandatos': '',
        'comissoes': '',
        'biografia_resumida': '',
        'url_perfil_detalhado': perfil_url
    }
    
    try:
        texto_completo = soup.get_text()
        
        nome_tag = soup.find('h1')
        if nome_tag:
            detalhes['nome_civil'] = nome_tag.get_text().strip()[:100]
        
        data_match = re.search(
            r'(?:Nascimento|Nascido|Nascida|Data de Nascimento)[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            texto_completo,
            re.IGNORECASE
        )
        if data_match:
            detalhes['data_nascimento'] = data_match.group(1)
        
        nat_match = re.search(
            r'(?:Naturalidade|Natural de)[:\s]*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\.;\n]{3,80})',
            texto_completo,
            re.IGNORECASE
        )
        if nat_match:
            naturalidade = nat_match.group(1).strip()
            
            if "Gabinete" in naturalidade:
                naturalidade = naturalidade.split("Gabinete")[0].strip()
            
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
        
        paragrafos = soup.find_all('p', limit=3)
        if paragrafos:
            biografia_parts = []
            for p in paragrafos:
                texto_p = p.get_text().strip()
                if len(texto_p) > 50:
                    biografia_parts.append(texto_p)
            
            if biografia_parts:
                biografia = ' '.join(biografia_parts)
                detalhes['biografia_resumida'] = biografia[:400]
    
    except Exception as e:
        pass
    
    return detalhes

def save_to_csv(senadoras_data: List[Dict], filename: str = "data/senadoras.csv") -> None:
    
    if not senadoras_data:
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
        
        print("6. Salvando dados em CSV...")
        print(f"   Arquivo: {filename}")
        print(f"   Campos: {len(fieldnames)} atributos")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for senadora in senadoras_data:
                row = {field: senadora.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"   ✓  Dados salvos com sucesso!")
        print(f"    Total de senadoras: {len(senadoras_data)}")
        print(f"    Caminho completo: {Path(filename).absolute()}\n")
        
    except Exception as e:
        print(f"   ✗ Erro ao salvar CSV: {e}\n")


def generate_statistics(senadoras_data: List[Dict]) -> Dict:
    
    if not senadoras_data:
        return {}
    
    stats = {
        "total_senadoras": len(senadoras_data),
        "por_partido": {},
        "por_uf": {},
        "por_periodo": {}
    }
    
    for senadora in senadoras_data:
        partido = senadora.get('partido', 'N/A')
        uf = senadora.get('uf', 'N/A')
        periodo = senadora.get('periodo_mandato', 'N/A')
        
        stats["por_partido"][partido] = stats["por_partido"].get(partido, 0) + 1
        stats["por_uf"][uf] = stats["por_uf"].get(uf, 0) + 1
        stats["por_periodo"][periodo] = stats["por_periodo"].get(periodo, 0) + 1
    
    stats["por_partido"] = dict(sorted(stats["por_partido"].items(), key=lambda x: x[1], reverse=True))
    stats["por_uf"] = dict(sorted(stats["por_uf"].items(), key=lambda x: x[1], reverse=True))
    stats["por_periodo"] = dict(sorted(stats["por_periodo"].items(), key=lambda x: x[1], reverse=True))
    
    return stats


def main():
    
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "WEB SCRAPING - SENADORAS FEDERAIS" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    senadoras_data = scrape_senadoras_list()
    
    if senadoras_data:
        print("=" * 70)
        print("SCRAPING CONCLUÍDO COM SUCESSO! ✓")
        print("=" * 70)
        
        print("\n7. Gerando estatísticas dos dados...\n")
        stats = generate_statistics(senadoras_data)
        
        if stats:
            print("   ESTATÍSTICAS FINAIS:")
            print("   " + "-" * 50)
            print(f"   Total de senadoras: {stats['total_senadoras']}")
            
            print(f"\n   Distribuição por partido:")
            for partido, count in stats['por_partido'].items():
                barra = "█" * count
                print(f"      • {partido:20} {barra} {count}")
            
            print(f"\n   Distribuição por estado (Top 5):")
            for i, (uf, count) in enumerate(list(stats['por_uf'].items())[:5], 1):
                print(f"      {i}. {uf}: {count}")
            
            print(f"\n   Distribuição por período de mandato:")
            for periodo, count in stats['por_periodo'].items():
                print(f"      • {periodo}: {count}")
        
        print("\n" + "=" * 70)
        save_to_csv(senadoras_data)
        
        print("=" * 70)
        print("AMOSTRA DOS DADOS (primeiras 3 senadoras):")
        print("-" * 70)
        for i, senadora in enumerate(senadoras_data[:3], 1):
            print(f"\n{i}. {senadora['nome']}")
            print(f"   Partido: {senadora['partido']} | UF: {senadora['uf']}")
            print(f"   Mandato: {senadora['periodo_mandato']}")
            print(f"   Email: {senadora['email']}")
            print(f"   Telefone: {senadora['telefones']}")
            if senadora.get('naturalidade'):
                print(f"   Naturalidade: {senadora['naturalidade']}")
            if senadora.get('profissao'):
                print(f"   Profissão: {senadora['profissao']}")
            print(f"   Perfil: {senadora['link_perfil']}")
        
        print()
        
    else:
        print("=" * 70)
        print("  ✗ FALHA NO SCRAPING - Nenhum dado coletado")
        print("=" * 70)
        print("\nPOSSÍVEIS CAUSAS:")
        print("  • Site mudou estrutura HTML")
        print("  • Bloqueio anti-bot (403 Forbidden)")
        print("  • Problemas de conectividade (timeout)")
        print("  • Seção 'Feminino' não foi encontrada na tabela")
        print("\nSUGESTÕES:")
        print("  • Verificar se a URL ainda está acessível")
        print("  • Testar manualmente no navegador")
        print("  • Verificar estrutura HTML da página")
        print()
    
    print("=" * 70)
    print("FIM DO PROCESSO")
    print("=" * 70)
    print()
    
    return senadoras_data


if __name__ == "__main__":
    main()