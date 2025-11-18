#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor de CSV para JSON - Deputadas Federais

Este módulo converte os dados brutos do CSV de deputadas para um formato JSON limpo
contendo apenas os campos específicos solicitados.
"""

import csv
import json
import re
from datetime import datetime
from typing import Dict, List, Optional


class DeputadasCSVToJSONConverter:
    """
    Classe para converter dados de deputadas do CSV para JSON filtrado.
    
    Extrai apenas os campos específicos solicitados:
    - Nome Civil
    - Partido  
    - Data de Nascimento
    - Naturalidade
    - Propostas legislativas de sua autoria
    - Propostas relatadas
    - Votações nominais em Plenário
    - Discursos em Plenário
    - Salário mensal bruto
    - Imóvel funcional
    - Auxílio-moradia
    - Viagens em missão oficial
    """
    
    def __init__(self, csv_file_path: str, json_output_path: str):
        """
        Inicializa o conversor.
        
        Args:
            csv_file_path: Caminho para o arquivo CSV de entrada
            json_output_path: Caminho para o arquivo JSON de saída
        """
        self.csv_file_path = csv_file_path
        self.json_output_path = json_output_path
        
    def extract_from_html_content(self, html_content: str) -> Dict:
        """
        Extrai informações específicas do conteúdo HTML armazenado no CSV.
        
        Args:
            html_content: Conteúdo HTML da página da deputada
            
        Returns:
            Dict: Dados extraídos do HTML
        """
        extracted_data: Dict[str, Optional[str | int | float]] = {
            'nome_civil': None,
            'partido': None,
            'data_nascimento': None,
            'naturalidade': None,
            'propostas_autoria': None,
            'propostas_relatadas': None,
            'votacoes_plenario': None,
            'discursos_plenario': None,
            'salario_mensal_bruto': None,
            'imovel_funcional': None,
            'auxilio_moradia': None,
            'viagens_missao_oficial': None
        }
        
        if not html_content:
            return extracted_data
            
        # Extrair Nome Civil
        nome_civil_match = re.search(r'Nome Civil:\s*([^\n\r]+)', html_content)
        if nome_civil_match:
            extracted_data['nome_civil'] = nome_civil_match.group(1).strip()
            
        # Extrair Partido
        partido_match = re.search(r'Partido:\s*([^\n\r]+)', html_content)
        if partido_match:
            extracted_data['partido'] = partido_match.group(1).strip()
            
        # Extrair Data de Nascimento
        data_nasc_match = re.search(r'Data de Nascimento:\s*(\d{2}/\d{2}/\d{4})', html_content)
        if data_nasc_match:
            extracted_data['data_nascimento'] = data_nasc_match.group(1).strip()
            
        # Extrair Naturalidade
        naturalidade_match = re.search(r'Naturalidade:\s*([^\n\r]+)', html_content)
        if naturalidade_match:
            naturalidade = naturalidade_match.group(1).strip()
            # Limpar possíveis tags HTML ou caracteres extras
            naturalidade = re.sub(r'<[^>]+>', '', naturalidade)
            naturalidade = re.sub(r'\s+', ' ', naturalidade).strip()
            if naturalidade and naturalidade != 'Naturalidade:':
                extracted_data['naturalidade'] = naturalidade
                
        # Extrair Propostas de autoria
        autoria_match = re.search(r'de sua autoria\s*(\d+)', html_content)
        if autoria_match:
            extracted_data['propostas_autoria'] = int(autoria_match.group(1))
            
        # Extrair Propostas relatadas
        relatadas_match = re.search(r'relatadas\s*(\d+)', html_content)
        if relatadas_match:
            extracted_data['propostas_relatadas'] = int(relatadas_match.group(1))
            
        # Extrair Votações em Plenário
        votacoes_match = re.search(r'em Plenário\s*(\d+)', html_content)
        if votacoes_match:
            extracted_data['votacoes_plenario'] = int(votacoes_match.group(1))
            
        # Extrair Discursos em Plenário
        discursos_match = re.search(r'Discursos[^0-9]*em Plenário\s*(\d+)', html_content, re.DOTALL)
        if discursos_match:
            extracted_data['discursos_plenario'] = int(discursos_match.group(1))
            
        # Extrair Salário mensal bruto
        salario_match = re.search(r'Salário mensal bruto[^R]*R\$\s*([\d,.]+)', html_content, re.DOTALL)
        if salario_match:
            salario_str = salario_match.group(1).replace('.', '').replace(',', '.')
            try:
                extracted_data['salario_mensal_bruto'] = float(salario_str)
            except ValueError:
                pass
                
        # Extrair Imóvel funcional
        imovel_match = re.search(r'Imóvel funcional[^?]*\?\s*([^<\n\r]+)', html_content, re.DOTALL)
        if imovel_match:
            imovel_text = imovel_match.group(1).strip()
            # Limpar possíveis tags HTML
            imovel_text = re.sub(r'<[^>]+>', '', imovel_text)
            imovel_text = re.sub(r'\s+', ' ', imovel_text).strip()
            if imovel_text:
                extracted_data['imovel_funcional'] = imovel_text
                
        # Extrair Auxílio-moradia
        auxilio_match = re.search(r'Auxílio-moradia[^?]*\?\s*([^<\n\r]+)', html_content, re.DOTALL)
        if auxilio_match:
            auxilio_text = auxilio_match.group(1).strip()
            # Limpar possíveis tags HTML
            auxilio_text = re.sub(r'<[^>]+>', '', auxilio_text)
            auxilio_text = re.sub(r'\s+', ' ', auxilio_text).strip()
            if auxilio_text:
                extracted_data['auxilio_moradia'] = auxilio_text
                
        # Extrair Viagens em missão oficial
        viagens_match = re.search(r'Viagens em missão oficial[^?]*\?\s*(\d+)', html_content, re.DOTALL)
        if viagens_match:
            extracted_data['viagens_missao_oficial'] = int(viagens_match.group(1))
            
        return extracted_data
        
    def process_csv_to_json(self) -> List[Dict]:
        """
        Processa o arquivo CSV e extrai os dados para formato JSON.
        
        Returns:
            List[Dict]: Lista de deputadas com dados filtrados
        """
        deputadas_data = []
        
        print(f"Lendo arquivo CSV: {self.csv_file_path}")
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for i, row in enumerate(reader, 1):
                    print(f"Processando deputada {i}: {row.get('nome', 'N/A')}")
                    
                    # Extrair dados do conteúdo HTML armazenado na coluna 'titulo_cargo'
                    html_content = row.get('titulo_cargo', '')
                    
                    # Extrair informações específicas do HTML
                    extracted_data = self.extract_from_html_content(html_content)
                    
                    # Se não conseguiu extrair do HTML, usar dados básicos do CSV
                    if not extracted_data['nome_civil']:
                        extracted_data['nome_civil'] = row.get('nome_civil', None)
                        
                    if not extracted_data['partido']:
                        extracted_data['partido'] = row.get('partido', None)
                        
                    # Adicionar informações básicas
                    deputada_info = {
                        'nome': row.get('nome', None),
                        'nome_civil': extracted_data['nome_civil'],
                        'partido': extracted_data['partido'],
                        'data_nascimento': extracted_data['data_nascimento'],
                        'naturalidade': extracted_data['naturalidade'],
                        'propostas_autoria': extracted_data['propostas_autoria'],
                        'propostas_relatadas': extracted_data['propostas_relatadas'],
                        'votacoes_plenario': extracted_data['votacoes_plenario'],
                        'discursos_plenario': extracted_data['discursos_plenario'],
                        'salario_mensal_bruto': extracted_data['salario_mensal_bruto'],
                        'imovel_funcional': extracted_data['imovel_funcional'],
                        'auxilio_moradia': extracted_data['auxilio_moradia'],
                        'viagens_missao_oficial': extracted_data['viagens_missao_oficial'],
                        'link_perfil': row.get('link_perfil', None),
                        'data_extracao': row.get('data_extracao', None)
                    }
                    
                    deputadas_data.append(deputada_info)
                    
        except FileNotFoundError:
            print(f"Erro: Arquivo {self.csv_file_path} não encontrado.")
            return []
        except Exception as e:
            print(f"Erro ao processar CSV: {e}")
            return []
            
        print(f"Total de deputadas processadas: {len(deputadas_data)}")
        return deputadas_data
        
    def save_to_json(self, deputadas_data: List[Dict]) -> bool:
        """
        Salva os dados das deputadas em arquivo JSON.
        
        Args:
            deputadas_data: Lista de dados das deputadas
            
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            # Criar estrutura final do JSON
            output_data = {
                'metadata': {
                    'total_deputadas': len(deputadas_data),
                    'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'fonte': 'Câmara dos Deputados',
                    'campos_extraidos': [
                        'nome_civil',
                        'partido',
                        'data_nascimento',
                        'naturalidade', 
                        'propostas_autoria',
                        'propostas_relatadas',
                        'votacoes_plenario',
                        'discursos_plenario',
                        'salario_mensal_bruto',
                        'imovel_funcional',
                        'auxilio_moradia',
                        'viagens_missao_oficial'
                    ]
                },
                'deputadas': deputadas_data
            }
            
            with open(self.json_output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(output_data, jsonfile, ensure_ascii=False, indent=2)
                
            print(f"Arquivo JSON salvo com sucesso: {self.json_output_path}")
            return True
            
        except Exception as e:
            print(f"Erro ao salvar arquivo JSON: {e}")
            return False
            
    def convert(self) -> bool:
        """
        Executa a conversão completa de CSV para JSON.
        
        Returns:
            bool: True se a conversão foi bem-sucedida
        """
        print("Iniciando conversão de CSV para JSON...")
        
        # Processar CSV
        deputadas_data = self.process_csv_to_json()
        
        if not deputadas_data:
            print("Nenhum dado foi processado.")
            return False
            
        # Salvar JSON
        success = self.save_to_json(deputadas_data)
        
        if success:
            print("Conversão concluída com sucesso!")
            print(f"Arquivo gerado: {self.json_output_path}")
        else:
            print("Erro na conversão.")
            
        return success


def main():
    """Função principal para executar a conversão."""
    # Caminhos dos arquivos
    csv_input = '/Users/vanessacunha/T-INE5454/mulheres_politica/data/deputadas.csv'
    json_output = '/Users/vanessacunha/T-INE5454/mulheres_politica/data/deputadas_filtrado.json'
    
    # Criar conversor e executar
    converter = DeputadasCSVToJSONConverter(csv_input, json_output)
    converter.convert()


if __name__ == "__main__":
    main()