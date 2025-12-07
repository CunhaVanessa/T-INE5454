"""
Conversor CSV → JSON - Deputadas Federais

Usa os dados JÁ EXTRAÍDOS e presentes nas colunas do CSV.
"""

import csv
import json
from datetime import datetime
from typing import Dict, List
from pathlib import Path
from webscraping_deputadas import get_total_homens

class DeputadasCSVToJSONConverter:
   
    def __init__(self, csv_file_path: str, json_output_path: str):
        """
        Inicializa o conversor.
        
        Args:
            csv_file_path: Caminho para o arquivo CSV de entrada
            json_output_path: Caminho para o arquivo JSON de saída
        """
        self.csv_file_path = csv_file_path
        self.json_output_path = json_output_path
    
    def process_csv_to_json(self) -> List[Dict]:
        """
        Processa o arquivo CSV e extrai os dados para formato JSON.
        
        Returns:
            List[Dict]: Lista de deputadas com dados filtrados
        """
        deputadas_data = []

        print(f"\n1. Lendo arquivo CSV: {self.csv_file_path}\n")
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for i, row in enumerate(reader, 1):
                    nome = row.get('nome', 'N/A')
                    print(f"   [{i}] Processando: {nome}")

                    deputada_info = {
                        'nome': row.get('nome', '').split('(')[0],
                        'nome_civil': row.get('nome_civil', ''),
                        'partido': row.get('partido', ''),
                        'uf': row.get('uf', ''),
                        'cargo': "Deputada",
                        'periodo_mandato': row.get('periodo_mandato', ''),
                        'telefones': row.get('telefones', ''),
                        'email': row.get('email', ''),
                        'data_nascimento': row.get('data_nascimento', ''),
                        'naturalidade': row.get('naturalidade', ''),
                        'profissao': row.get('profissao', ''),
                        'formacao': row.get('formacao', ''),
                        'numero_mandatos': row.get('numero_mandatos', ''),
                        'comissoes': row.get('comissoes', ''),
                        'link_perfil': row.get('link_perfil', ''),
                        'fonte_dados': row.get('fonte_dados', 'Web Scraping HTML'),
                        'url_fonte':  row.get('url_fonte', ''),
                        'data_extracao': row.get('data_extracao', '')
                    }
                    
                    deputadas_data.append(deputada_info)
            
            print(f"\n2. ✓ Total de deputadas processadas: {len(deputadas_data)}\n")
        
        except FileNotFoundError:
            print(f"   ✗ Erro: Arquivo {self.csv_file_path} não encontrado.\n")
            return []
        except Exception as e:
            print(f"   ✗ Erro ao processar CSV: {e}\n")
            return []
        
        return deputadas_data
    
    def save_to_json(self, deputadas_data: List[Dict]) -> bool:
        """
        Salva os dados das deputadas em arquivo JSON.
        
        Estrutura final:
        {
            "metadata": { ... },
            "deputadas": [ ... ]
        }
        
        Args:
            deputadas_data: Lista de dados das deputadas
        
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            # Criar diretório se não existir
            Path(self.json_output_path).parent.mkdir(parents=True, exist_ok=True)

            campos_nao_vazios = {
                'nome': 0,
                'nome_civil': 0,
                'partido': 0,
                'uf': 0,
                'cargo': 0,
                'periodo_mandato': 0,
                'telefones': 0,
                'email': 0,
                'data_nascimento': 0,
                'naturalidade': 0,
                'profissao': 0,
                'formacao': 0,
                'numero_mandatos': 0,
                'comissoes': 0,
                'link_perfil': 0,
                'fonte_dados': 0,
                'url_fonte': 0,
                'data_extracao': 0
            }
            
            for deputada in deputadas_data:
                for campo in campos_nao_vazios.keys():
                    if deputada.get(campo) and str(deputada.get(campo)).strip():
                        campos_nao_vazios[campo] += 1
            
            total_homens = get_total_homens()
                
            qtd_mulheres = len(deputadas_data)
            total_geral = qtd_mulheres + total_homens
            pct_mulheres = 0
            if total_geral > 0:
                pct_mulheres = round((qtd_mulheres / total_geral) * 100, 2)
            
            output_data = {
                'metadata': {
                    'fonte': 'Câmara dos Deputados',
                    'tipo': 'Deputadas Federais',
                    'total_registros': len(deputadas_data),
                    'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'campos': [
                        'nome',
                        'nome_civil',
                        'partido',
                        'uf',
                        'cargo',
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
                        'data_extracao'
                    ],
                    'total_campos': 17,
                    'campos_preenchidos': campos_nao_vazios,
                    'estatisticas_genero': {
                        'total_mulheres': qtd_mulheres,
                        'total_homens': total_homens,
                        'total_geral': total_geral,
                        'porcentagem_mulheres': pct_mulheres
                    },
                },
                'deputadas': deputadas_data
            }
            
            print("3. Salvando arquivo JSON...")
            print(f"  ✓ Arquivo: {self.json_output_path}")
            
            with open(self.json_output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(output_data, jsonfile, ensure_ascii=False, indent=2)
            
            print(f"   ✓ Arquivo JSON salvo com sucesso!")
            print(f"   ✓ Total de senadoras: {len(deputadas_data)}")
            print(f"   ✓ Total de campos: 17 ✓")
            print(f"\n4. Estatísticas de preenchimento dos campos:\n")
            
            for campo, count in campos_nao_vazios.items():
                percentual = (count / len(deputadas_data)) * 100 if deputadas_data else 0
                barra = "█" * int(percentual / 5)
                print(f"   • {campo:20} {barra:20} {count:3}/{len(deputadas_data)} ({percentual:.1f}%)")
            
            print()
            return True
        
        except Exception as e:
            print(f"   ✗ Erro ao salvar arquivo JSON: {e}\n")
            return False
    
    def convert(self) -> bool:
        """
        Executa a conversão completa de CSV para JSON.
        
        Returns:
            bool: True se a conversão foi bem-sucedida
        """

        deputadas_data = self.process_csv_to_json()
            
        success = self.save_to_json(deputadas_data)
        
        if success:
            print("=" * 70)
            print("CONVERSÃO CONCLUÍDA COM SUCESSO! ✓")
            print("=" * 70)
            print(f"\nArquivo gerado: {self.json_output_path}")
            print()
        else:
            print("=" * 70)
            print("ERRO NA CONVERSÃO ✗")
            print("=" * 70)
            print()
        
        return success


def main():
    csv_input = 'data/deputadas.csv'
    json_output = 'data/deputadas.json'
    
    print("\n")
    print("┌" + "─" * 68 + "┐")
    print("│        CONVERSOR CSV → JSON - DEPUTADAS FEDERAIS                   │")
    print()
    
    converter = DeputadasCSVToJSONConverter(csv_input, json_output)
    success = converter.convert()
    
    if success:
        print("✅ Conversão bem-sucedida!")
        print(f"📄 Arquivo JSON disponível em: {json_output}")
        print()
    else:
        print("❌ Erro na conversão!")
        print()
        print("POSSÍVEIS CAUSAS:")
        print("  • Arquivo CSV não encontrado")
        print("  • Arquivo CSV com estrutura incorreta")
        print("  • Permissões de escrita no diretório de saída")
        print()
    
    print("─" * 70)
    print()


if __name__ == "__main__":
    main()