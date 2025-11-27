#+ difícil dados de multiplas fontes os API única?
#- IBGE
#- https://sig.tse.jus.br/ords/dwapr/r/seai/sig-eleicao-arquivo/arquivos-gerados?session=225616866824267

"""
Web scraping/API module for collecting data about female city councilors (vereadoras).

Este módulo coleta informações sobre mulheres vereadoras eleitas nas eleições
municipais brasileiras de 2024, utilizando dados abertos do TSE e API do IBGE.

IMPORTANTE: Utiliza dados oficiais do Portal de Dados Abertos do TSE.
Fonte: https://dadosabertos.tse.jus.br/dataset/candidatos-2024
"""

import requests
import csv
import time
from typing import List, Dict, Optional
from pathlib import Path
import zipfile
import io
import os


# ==========================================
# PARTE 1: CONFIGURAÇÕES E CONSTANTES
# ==========================================

# URLs das APIs e arquivos de dados
TSE_CANDIDATOS_2024_URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2024.zip"
IBGE_MUNICIPIOS_API = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

# Constantes para filtragem
CARGO_VEREADOR = "VEREADOR"  # Código 13 no TSE
GENERO_FEMININO = "FEMININO"  # Código 4 no TSE
SITUACAO_ELEITO = "ELEITO"  # Situação de candidato eleito

# Encoding dos arquivos do TSE
TSE_ENCODING = "latin-1"


# ==========================================
# PARTE 2: FUNÇÃO PRINCIPAL DE SCRAPING/API
# ==========================================

def scrape_vereadoras_data() -> List[Dict]:
    """
    Coleta dados de vereadoras eleitas em 2024 usando dados abertos do TSE.
    
    Fluxo de execução:
    1. Baixa arquivo ZIP com dados de candidatos 2024 do TSE
    2. Extrai arquivo CSV do Brasil inteiro
    3. Filtra apenas vereadoras (cargo = VEREADOR + gênero = FEMININO + situação = ELEITO)
    4. Enriquece dados com informações do IBGE (nome completo do município)
    5. Retorna lista com dados estruturados
    
    Fonte dos dados:
    - TSE: https://dadosabertos.tse.jus.br/dataset/candidatos-2024
    - IBGE: API de municípios brasileiros
    
    Returns:
        list: Lista de dicionários com dados das vereadoras eleitas
    """
    
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 10 + "WEB SCRAPING/API - VEREADORAS MUNICIPAIS 2024" + " " * 13 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    print("=" * 70)
    print("INICIANDO COLETA DE DADOS - VEREADORAS ELEITAS 2024")
    print("=" * 70)
    
    vereadoras_data = []
    
    try:
        # Passo 1: Baixar dados do TSE
        print("\n1. Baixando arquivo de candidatos 2024 do TSE...")
        print(f"   Fonte: Portal de Dados Abertos do TSE")
        print(f"   URL: {TSE_CANDIDATOS_2024_URL}")
        print(f"   ⚠ Arquivo grande (~200MB) - pode demorar alguns minutos...")
        
        candidatos_csv = download_tse_data(TSE_CANDIDATOS_2024_URL)
        
        if not candidatos_csv:
            print("   ✗ Falha ao baixar dados do TSE")
            return []
        
        print(f"   ✓ Arquivo baixado e extraído com sucesso!\n")
        
        # Passo 2: Filtrar vereadoras eleitas
        print("2. Filtrando vereadoras eleitas do arquivo CSV...")
        print(f"   Filtros aplicados:")
        print(f"   • Cargo: {CARGO_VEREADOR}")
        print(f"   • Gênero: {GENERO_FEMININO}")
        print(f"   • Situação: Eleita/Deferida")
        
        vereadoras_data = parse_and_filter_vereadoras(candidatos_csv)
        
        if not vereadoras_data:
            print("   ✗ Nenhuma vereadora encontrada nos dados")
            return []
        
        print(f"   ✓ {len(vereadoras_data)} vereadoras eleitas encontradas!\n")
        
        # Passo 3: Enriquecer dados com informações do IBGE
        print("3. Enriquecendo dados com informações do IBGE...")
        print("   (buscando nomes completos de municípios)")
        
        municipios_ibge = fetch_municipios_ibge()
        
        if municipios_ibge:
            vereadoras_data = enrich_with_ibge_data(vereadoras_data, municipios_ibge)
            print(f"   ✓ Dados enriquecidos com sucesso!\n")
        else:
            print(f"   ⚠ Não foi possível enriquecer dados do IBGE\n")
        
    except Exception as e:
        print(f"   ✗ Erro geral na coleta: {e}\n")
        return []
    
    return vereadoras_data


# ==========================================
# PARTE 3: DOWNLOAD DOS DADOS DO TSE
# ==========================================

def download_tse_data(url: str) -> Optional[str]:
    """
    Baixa e extrai arquivo ZIP de candidatos do TSE.
    
    O TSE disponibiliza os dados em formato ZIP contendo múltiplos CSVs.
    Esta função:
    1. Faz download do arquivo ZIP (pode ser grande, ~200MB)
    2. Extrai o CSV do Brasil inteiro (consulta_cand_2024_BRASIL.csv)
    3. Retorna o conteúdo do CSV como string
    
    Args:
        url: URL do arquivo ZIP do TSE
        
    Returns:
        str: Conteúdo do CSV de candidatos ou None se falhar
    """
    
    try:
        # Headers HTTP para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/zip, application/octet-stream, */*',
        }
        
        # Fazer download do arquivo ZIP (pode demorar)
        print("   → Iniciando download...")
        response = requests.get(url, headers=headers, timeout=300, stream=True)
        
        if response.status_code != 200:
            print(f"   ✗ Erro HTTP: {response.status_code}")
            return None
        
        # Obter tamanho do arquivo para progresso
        total_size = int(response.headers.get('content-length', 0))
        print(f"   → Tamanho do arquivo: {total_size / (1024*1024):.1f} MB")
        
        # Baixar em chunks para mostrar progresso
        downloaded = 0
        chunks = []
        
        for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
            if chunk:
                chunks.append(chunk)
                downloaded += len(chunk)
                
                if total_size > 0:
                    progress = (downloaded / total_size) * 100
                    print(f"   → Progresso: {progress:.1f}%", end='\r')
        
        print()  # Nova linha após progresso
        
        # Montar bytes do arquivo completo
        zip_bytes = b''.join(chunks)
        
        print("   → Extraindo arquivo CSV do ZIP...")
        
        # Abrir ZIP em memória
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
            # Listar arquivos no ZIP
            file_list = zip_file.namelist()
            
            # Procurar arquivo do Brasil (pode ter variações no nome)
            brasil_files = [f for f in file_list if 'BRASIL' in f.upper() and f.endswith('.csv')]
            
            if not brasil_files:
                print(f"   ✗ Arquivo CSV do Brasil não encontrado no ZIP")
                print(f"   Arquivos disponíveis: {file_list[:5]}...")
                return None
            
            # Extrair primeiro arquivo do Brasil encontrado
            brasil_file = brasil_files[0]
            print(f"   → Extraindo: {brasil_file}")
            
            # Ler conteúdo do CSV
            with zip_file.open(brasil_file) as csv_file:
                csv_content = csv_file.read().decode(TSE_ENCODING, errors='ignore')
            
            return csv_content
        
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Erro de conexão: {e}")
        return None
    except zipfile.BadZipFile as e:
        print(f"   ✗ Erro ao processar ZIP: {e}")
        return None
    except Exception as e:
        print(f"   ✗ Erro inesperado: {e}")
        return None


# ==========================================
# PARTE 4: PROCESSAMENTO E FILTRAGEM
# ==========================================

def parse_and_filter_vereadoras(csv_content: str) -> List[Dict]:
    """
    Processa CSV do TSE e filtra apenas vereadoras eleitas.
    
    O CSV do TSE contém TODOS os candidatos (homens, mulheres, todos os cargos).
    Esta função:
    1. Parseia o CSV linha por linha
    2. Filtra apenas registros que atendem aos critérios:
       - Cargo = VEREADOR
       - Gênero = FEMININO
       - Situação de candidatura = válida (deferida)
       - Situação de totalização = ELEITO (se disponível)
    3. Extrai campos relevantes de cada registro
    
    Campos do CSV do TSE (principais):
    - DS_CARGO: Nome do cargo (VEREADOR, PREFEITO, etc.)
    - DS_GENERO: Gênero do candidato
    - NM_CANDIDATO: Nome de urna
    - NM_URNA_CANDIDATO: Nome de urna simplificado
    - SG_PARTIDO: Sigla do partido
    - SG_UF: Sigla do estado
    - NM_UE: Nome da unidade eleitoral (município)
    - DS_SIT_TOT_TURNO: Situação de totalização (ELEITO, NÃO ELEITO, etc.)
    
    Args:
        csv_content: Conteúdo do CSV como string
        
    Returns:
        list: Lista de dicionários com dados das vereadoras
    """
    
    vereadoras = []
    
    try:
        # Dividir CSV em linhas
        lines = csv_content.strip().split('\n')
        
        if len(lines) < 2:
            print("   ✗ CSV vazio ou inválido")
            return []
        
        # Primeira linha = cabeçalho
        header_line = lines[0]
        headers = [h.strip('"').strip() for h in header_line.split(';')]
        
        print(f"   → Total de linhas no CSV: {len(lines):,}")
        print(f"   → Processando registros...")
        
        # Processar cada linha de dados
        processed_count = 0
        filtered_count = 0
        
        for i, line in enumerate(lines[1:], 1):
            # Mostrar progresso a cada 10000 linhas
            if i % 10000 == 0:
                print(f"   → Processadas {i:,} linhas | Vereadoras encontradas: {filtered_count}", end='\r')
            
            try:
                # Parsear linha CSV (separador = ponto-e-vírgula)
                values = [v.strip('"').strip() for v in line.split(';')]
                
                # Criar dicionário linha
                if len(values) != len(headers):
                    continue  # Pular linhas malformadas
                
                row_dict = dict(zip(headers, values))
                
                # Aplicar filtros
                cargo = row_dict.get('DS_CARGO', '').upper()
                genero = row_dict.get('DS_GENERO', '').upper()
                situacao_cand = row_dict.get('DS_SITUACAO_CANDIDATURA', '').upper()
                situacao_tot = row_dict.get('DS_SIT_TOT_TURNO', '').upper()
                
                # Filtro 1: Cargo = VEREADOR
                if CARGO_VEREADOR not in cargo:
                    continue
                
                # Filtro 2: Gênero = FEMININO
                if GENERO_FEMININO not in genero:
                    continue
                
                # Filtro 3: Candidatura deferida (válida)
                if 'DEFERIDO' not in situacao_cand and 'APTO' not in situacao_cand:
                    continue
                
                # Filtro 4: Eleita (se campo disponível)
                # Nota: Nem sempre o campo DS_SIT_TOT_TURNO está preenchido
                # Para vereadoras eleitas, procurar por "ELEITO" ou similar
                if situacao_tot and SITUACAO_ELEITO not in situacao_tot:
                    # Se o campo existe e não é ELEITO, pular
                    if situacao_tot and situacao_tot != '#NULO#' and situacao_tot != '':
                        continue
                
                # Extrair dados relevantes
                vereadora_data = extract_vereadora_data(row_dict)
                
                if vereadora_data:
                    vereadoras.append(vereadora_data)
                    filtered_count += 1
                
                processed_count += 1
                
            except Exception as e:
                # Ignorar linhas com erro de parsing
                continue
        
        print()  # Nova linha após progresso
        print(f"   → Total processado: {processed_count:,} candidaturas")
        
    except Exception as e:
        print(f"   ✗ Erro ao processar CSV: {e}")
    
    return vereadoras


def extract_vereadora_data(row_dict: Dict) -> Optional[Dict]:
    """
    Extrai dados relevantes de uma vereadora do dicionário da linha CSV.
    
    Campos extraídos (mínimo 11 atributos - REQUISITO DO TRABALHO!):
    1. Nome de urna
    2. Nome completo (civil)
    3. Partido
    4. Número de candidato
    5. UF (estado)
    6. Município
    7. Situação de candidatura
    8. Situação de totalização (eleito/não eleito)
    9. Gênero
    10. Cor/Raça
    11. Grau de instrução
    12. Data de nascimento (extra)
    13. CPF (extra - pode estar parcialmente oculto)
    14. E-mail (extra)
    15. Número da urna (extra)
    16. Composição da legenda (coligação) (extra)
    
    Args:
        row_dict: Dicionário com dados da linha CSV
        
    Returns:
        dict: Dados estruturados da vereadora
    """
    
    try:
        vereadora = {
            # Atributos obrigatórios (mínimo 11)
            'nome_urna': row_dict.get('NM_URNA_CANDIDATO', row_dict.get('NM_CANDIDATO', '')),
            'nome_completo': row_dict.get('NM_CANDIDATO', ''),
            'partido': row_dict.get('SG_PARTIDO', ''),
            'numero_candidato': row_dict.get('NR_CANDIDATO', ''),
            'uf': row_dict.get('SG_UF', ''),
            'municipio': row_dict.get('NM_UE', ''),
            'situacao_candidatura': row_dict.get('DS_SITUACAO_CANDIDATURA', ''),
            'situacao_totalizacao': row_dict.get('DS_SIT_TOT_TURNO', 'Não informado'),
            'genero': row_dict.get('DS_GENERO', ''),
            'cor_raca': row_dict.get('DS_COR_RACA', ''),
            'grau_instrucao': row_dict.get('DS_GRAU_INSTRUCAO', ''),
            
            # Atributos extras (enriquecimento)
            'data_nascimento': row_dict.get('DT_NASCIMENTO', ''),
            'idade': calculate_age(row_dict.get('DT_NASCIMENTO', '')),
            'cpf': row_dict.get('NR_CPF_CANDIDATO', ''),
            'email': row_dict.get('NM_EMAIL', ''),
            'numero_urna': row_dict.get('NR_CANDIDATO', ''),
            'composicao_legenda': row_dict.get('DS_COMPOSICAO_LEGENDA', ''),
            'estado_civil': row_dict.get('DS_ESTADO_CIVIL', ''),
            'ocupacao': row_dict.get('DS_OCUPACAO', ''),
            
            # Metadados
            'fonte_dados': 'TSE - Portal de Dados Abertos',
            'url_fonte': 'https://dadosabertos.tse.jus.br/dataset/candidatos-2024',
            'data_extracao': time.strftime("%Y-%m-%d %H:%M:%S"),
            'metodo_extracao': 'API/Download - Dados Abertos TSE + IBGE',
            'ano_eleicao': '2024'
        }
        
        return vereadora
        
    except Exception as e:
        return None


# ==========================================
# PARTE 5: ENRIQUECIMENTO COM DADOS DO IBGE
# ==========================================

def fetch_municipios_ibge() -> Dict[str, Dict]:
    """
    Busca lista completa de municípios brasileiros na API do IBGE.
    
    A API do IBGE fornece:
    - Código IBGE do município
    - Nome completo do município
    - Microrregião
    - Mesorregião
    - UF completa
    
    API: https://servicodados.ibge.gov.br/api/v1/localidades/municipios
    
    Returns:
        dict: Dicionário {nome_municipio: {dados_completos}}
    """
    
    try:
        print("   → Acessando API do IBGE...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(IBGE_MUNICIPIOS_API, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"   ✗ Erro HTTP {response.status_code}")
            return {}
        
        municipios_json = response.json()
        
        print(f"   → Recebidos {len(municipios_json):,} municípios")
        
        # Criar dicionário de lookup
        municipios_dict = {}
        
        for municipio in municipios_json:
            nome = municipio.get('nome', '').upper()
            
            municipios_dict[nome] = {
                'codigo_ibge': municipio.get('id', ''),
                'nome_completo': municipio.get('nome', ''),
                'microrregiao': municipio.get('microrregiao', {}).get('nome', ''),
                'mesorregiao': municipio.get('microrregiao', {}).get('mesorregiao', {}).get('nome', ''),
                'uf_nome': municipio.get('microrregiao', {}).get('mesorregiao', {}).get('UF', {}).get('nome', ''),
                'uf_sigla': municipio.get('microrregiao', {}).get('mesorregiao', {}).get('UF', {}).get('sigla', ''),
                'regiao_nome': municipio.get('microrregiao', {}).get('mesorregiao', {}).get('UF', {}).get('regiao', {}).get('nome', '')
            }
        
        return municipios_dict
        
    except Exception as e:
        print(f"   ✗ Erro ao buscar dados do IBGE: {e}")
        return {}


def enrich_with_ibge_data(vereadoras: List[Dict], municipios_ibge: Dict) -> List[Dict]:
    """
    Enriquece dados das vereadoras com informações do IBGE.
    
    Adiciona campos:
    - Código IBGE do município
    - Microrregião
    - Mesorregião
    - Nome completo do estado
    - Região do Brasil
    
    Args:
        vereadoras: Lista com dados das vereadoras
        municipios_ibge: Dicionário de municípios do IBGE
        
    Returns:
        list: Lista enriquecida
    """
    
    enriched_count = 0
    
    for vereadora in vereadoras:
        municipio_nome = vereadora.get('municipio', '').upper()
        
        if municipio_nome in municipios_ibge:
            ibge_data = municipios_ibge[municipio_nome]
            
            # Adicionar campos do IBGE
            vereadora['codigo_ibge_municipio'] = ibge_data['codigo_ibge']
            vereadora['microrregiao'] = ibge_data['microrregiao']
            vereadora['mesorregiao'] = ibge_data['mesorregiao']
            vereadora['uf_nome_completo'] = ibge_data['uf_nome']
            vereadora['regiao_brasil'] = ibge_data['regiao_nome']
            
            enriched_count += 1
    
    print(f"   → {enriched_count}/{len(vereadoras)} vereadoras enriquecidas com dados IBGE")
    
    return vereadoras


# ==========================================
# PARTE 6: FUNÇÕES AUXILIARES
# ==========================================

def calculate_age(data_nascimento: str) -> str:
    """
    Calcula idade a partir da data de nascimento.
    
    Args:
        data_nascimento: Data no formato DD/MM/AAAA
        
    Returns:
        str: Idade calculada ou vazio se inválido
    """
    
    try:
        if not data_nascimento or len(data_nascimento) < 8:
            return ""
        
        # Formato esperado: DD/MM/AAAA
        parts = data_nascimento.split('/')
        if len(parts) != 3:
            return ""
        
        dia, mes, ano = int(parts[0]), int(parts[1]), int(parts[2])
        
        # Calcular idade aproximada (ano atual - ano nascimento)
        from datetime import datetime
        hoje = datetime.now()
        idade = hoje.year - ano
        
        # Ajustar se ainda não fez aniversário este ano
        if (hoje.month, hoje.day) < (mes, dia):
            idade -= 1
        
        return str(idade)
        
    except:
        return ""


# ==========================================
# PARTE 7: SALVAMENTO EM CSV
# ==========================================

def save_to_csv(vereadoras_data: List[Dict], filename: str = "../data/vereadoras.csv") -> None:
    """
    Salva os dados das vereadoras em arquivo CSV.
    
    CSV é um formato intermediário antes da consolidação JSON.
    
    Args:
        vereadoras_data: Lista com dados das vereadoras
        filename: Nome do arquivo CSV (caminho relativo)
    """
    
    if not vereadoras_data:
        print("   ✗ Nenhum dado para salvar\n")
        return
    
    try:
        # Criar diretório se não existir
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        # Definir campos (colunas) do CSV - MÍNIMO 11 ATRIBUTOS (temos 26!)
        fieldnames = [
            # 11 atributos obrigatórios
            'nome_urna',                   # 1
            'nome_completo',               # 2
            'partido',                     # 3
            'numero_candidato',            # 4
            'uf',                          # 5
            'municipio',                   # 6
            'situacao_candidatura',        # 7
            'situacao_totalizacao',        # 8
            'genero',                      # 9
            'cor_raca',                    # 10
            'grau_instrucao',              # 11
            
            # Atributos extras
            'data_nascimento',             # 12
            'idade',                       # 13
            'cpf',                         # 14
            'email',                       # 15
            'numero_urna',                 # 16
            'composicao_legenda',          # 17
            'estado_civil',                # 18
            'ocupacao',                    # 19
            
            # Dados do IBGE (enriquecimento)
            'codigo_ibge_municipio',       # 20
            'microrregiao',                # 21
            'mesorregiao',                 # 22
            'uf_nome_completo',            # 23
            'regiao_brasil',               # 24
            
            # Metadados
            'fonte_dados',                 # 25
            'url_fonte',                   # 26
            'data_extracao',               # 27
            'metodo_extracao',             # 28
            'ano_eleicao'                  # 29
        ]
        
        print("4. Salvando dados em CSV...")
        print(f"   Arquivo: {filename}")
        print(f"   Campos: {len(fieldnames)} atributos (requisito: mínimo 11) ✓")
        
        # Escrever CSV com encoding UTF-8
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Escrever cabeçalho
            writer.writeheader()
            
            # Escrever cada vereadora
            for vereadora in vereadoras_data:
                # Garantir que todos os campos existem
                row = {field: vereadora.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"   ✓ Dados salvos com sucesso!")
        print(f"   ✓ Total de vereadoras: {len(vereadoras_data)}")
        print(f"   ✓ Caminho completo: {Path(filename).absolute()}\n")
        
    except Exception as e:
        print(f"   ✗ Erro ao salvar CSV: {e}\n")


# ==========================================
# PARTE 8: ESTATÍSTICAS DOS DADOS
# ==========================================

def generate_statistics(vereadoras_data: List[Dict]) -> Dict:
    """
    Gera estatísticas descritivas dos dados coletados.
    
    Args:
        vereadoras_data: Lista com dados das vereadoras
        
    Returns:
        dict: Estatísticas calculadas
    """
    
    if not vereadoras_data:
        return {}
    
    stats = {
        "total_vereadoras": len(vereadoras_data),
        "por_partido": {},
        "por_uf": {},
        "por_regiao": {},
        "por_cor_raca": {},
        "por_grau_instrucao": {}
    }
    
    # Contar distribuições
    for vereadora in vereadoras_data:
        partido = vereadora.get('partido', 'N/A')
        uf = vereadora.get('uf', 'N/A')
        regiao = vereadora.get('regiao_brasil', 'N/A')
        cor_raca = vereadora.get('cor_raca', 'N/A')
        grau_instrucao = vereadora.get('grau_instrucao', 'N/A')
        
        stats["por_partido"][partido] = stats["por_partido"].get(partido, 0) + 1
        stats["por_uf"][uf] = stats["por_uf"].get(uf, 0) + 1
        stats["por_regiao"][regiao] = stats["por_regiao"].get(regiao, 0) + 1
        stats["por_cor_raca"][cor_raca] = stats["por_cor_raca"].get(cor_raca, 0) + 1
        stats["por_grau_instrucao"][grau_instrucao] = stats["por_grau_instrucao"].get(grau_instrucao, 0) + 1
    
    # Ordenar por quantidade (decrescente)
    stats["por_partido"] = dict(sorted(stats["por_partido"].items(), key=lambda x: x[1], reverse=True))
    stats["por_uf"] = dict(sorted(stats["por_uf"].items(), key=lambda x: x[1], reverse=True))
    stats["por_regiao"] = dict(sorted(stats["por_regiao"].items(), key=lambda x: x[1], reverse=True))
    stats["por_cor_raca"] = dict(sorted(stats["por_cor_raca"].items(), key=lambda x: x[1], reverse=True))
    stats["por_grau_instrucao"] = dict(sorted(stats["por_grau_instrucao"].items(), key=lambda x: x[1], reverse=True))
    
    return stats


# ==========================================
# PARTE 9: FUNÇÃO MAIN (ORQUESTRAÇÃO)
# ==========================================

def main():
    """
    Função principal que orquestra todo o processo de coleta de dados.
    
    Fluxo de execução:
    1. Coletar dados (TSE + IBGE)
    2. Gerar estatísticas descritivas
    3. Salvar dados em CSV
    4. Mostrar resumo e amostra dos dados
    """
    
    # 1. Executar coleta de dados
    vereadoras_data = scrape_vereadoras_data()
    
    if vereadoras_data:
        print("=" * 70)
        print("COLETA CONCLUÍDA COM SUCESSO! ✓")
        print("=" * 70)
        
        # 2. Gerar estatísticas
        print("\n5. Gerando estatísticas dos dados...\n")
        stats = generate_statistics(vereadoras_data)
        
        if stats:
            print("   ESTATÍSTICAS FINAIS:")
            print("   " + "-" * 50)
            print(f"   Total de vereadoras eleitas: {stats['total_vereadoras']:,}")
            
            print(f"\n   Distribuição por região (Top 5):")
            for i, (regiao, count) in enumerate(list(stats['por_regiao'].items())[:5], 1):
                print(f"      {i}. {regiao}: {count:,}")
            
            print(f"\n   Distribuição por partido (Top 10):")
            for i, (partido, count) in enumerate(list(stats['por_partido'].items())[:10], 1):
                barra = "█" * min(count // 10, 30)  # Limitar barra visual
                print(f"      {i:2}. {partido:10} {barra} {count}")
            
            print(f"\n   Distribuição por UF (Top 10):")
            for i, (uf, count) in enumerate(list(stats['por_uf'].items())[:10], 1):
                print(f"      {i:2}. {uf}: {count:,}")
            
            print(f"\n   Distribuição por cor/raça:")
            for cor_raca, count in stats['por_cor_raca'].items():
                print(f"      • {cor_raca}: {count:,}")
            
            print(f"\n   Distribuição por grau de instrução (Top 5):")
            for i, (grau, count) in enumerate(list(stats['por_grau_instrucao'].items())[:5], 1):
                print(f"      {i}. {grau}: {count:,}")
        
        # 3. Salvar em CSV
        print("\n" + "=" * 70)
        save_to_csv(vereadoras_data)
        
        # 4. Mostrar amostra dos dados coletados
        print("=" * 70)
        print("AMOSTRA DOS DADOS (primeiras 3 vereadoras):")
        print("-" * 70)
        for i, vereadora in enumerate(vereadoras_data[:3], 1):
            print(f"\n{i}. {vereadora['nome_urna']} ({vereadora['nome_completo']})")
            print(f"   Partido: {vereadora['partido']} | Número: {vereadora['numero_candidato']}")
            print(f"   Município: {vereadora['municipio']} - {vereadora['uf']}")
            print(f"   Situação: {vereadora['situacao_totalizacao']}")
            if vereadora.get('idade'):
                print(f"   Idade: {vereadora['idade']} anos")
            if vereadora.get('cor_raca'):
                print(f"   Cor/Raça: {vereadora['cor_raca']}")
            if vereadora.get('grau_instrucao'):
                print(f"   Escolaridade: {vereadora['grau_instrucao']}")
            if vereadora.get('regiao_brasil'):
                print(f"   Região: {vereadora['regiao_brasil']}")
        
        print()
        
    else:
        print("=" * 70)
        print("FALHA NA COLETA - Nenhum dado coletado ✗")
        print("=" * 70)
        print("\nPOSSÍVEIS CAUSAS:")
        print("  • Arquivo ZIP do TSE indisponível")
        print("  • Problema na conexão (timeout)")
        print("  • Estrutura do CSV mudou")
        print("  • Filtros muito restritivos")
        print("\nSUGESTÕES:")
        print("  • Verificar se a URL do TSE ainda está acessível")
        print("  • Testar download manual do arquivo")
        print("  • Verificar logs de erro acima")
        print()
    
    print("=" * 70)
    print("FIM DO PROCESSO")
    print("=" * 70)
    print()
    
    return vereadoras_data


# ==========================================
# PONTO DE ENTRADA DO SCRIPT
# ==========================================

if __name__ == "__main__":
    # Executar função main quando script for rodado diretamente
    main()