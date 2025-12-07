"""
Conversor CSV para JSON - Senadoras Federais

Usa os dados JÁ EXTRAÍDOS e presentes nas colunas do CSV.
"""

import csv
import json
from datetime import datetime
from typing import Dict, List
from pathlib import Path


class SenadorasCSVToJSONConverter:
   
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
            List[Dict]: Lista de senadoras com dados filtrados
        """
        senadoras_data = []

        print(f"\n1. Lendo arquivo CSV: {self.csv_file_path}\n")
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for i, row in enumerate(reader, 1):
                    nome = row.get('nome', 'N/A')
                    print(f"   [{i}] Processando: {nome}")

                    senadora_info = {
                        'nome': row.get('nome', ''),
                        'nome_civil': row.get('nome_civil', ''),
                        'partido': row.get('partido', ''),
                        'uf': row.get('uf', ''),
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
                    
                    senadoras_data.append(senadora_info)
            
            print(f"\n2. ✓ Total de senadoras processadas: {len(senadoras_data)}\n")
        
        except FileNotFoundError:
            print(f"   ✗ Erro: Arquivo {self.csv_file_path} não encontrado.\n")
            return []
        except Exception as e:
            print(f"   ✗ Erro ao processar CSV: {e}\n")
            return []
        
        return senadoras_data
    
    def save_to_json(self, senadoras_data: List[Dict]) -> bool:
        """
        Salva os dados das senadoras em arquivo JSON.
        
        Estrutura final:
        {
            "metadata": { ... },
            "senadoras": [ ... ]
        }
        
        Args:
            senadoras_data: Lista de dados das senadoras
        
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
            
            for senadora in senadoras_data:
                for campo in campos_nao_vazios.keys():
                    if senadora.get(campo) and str(senadora.get(campo)).strip():
                        campos_nao_vazios[campo] += 1
            
            total_homens = 0
            try:
                with open('data/temp_stats_senado.json', 'r') as f:
                    stats = json.load(f)
                    total_homens = stats.get('total_homens', 0)
            except:
                pass
                
                if not senadoras_data:
                    print("✗ Nenhum dado foi processado.\n")
                    return False
                
            qtd_mulheres = len(senadoras_data)
            total_geral = qtd_mulheres + total_homens
            pct_mulheres = 0
            if total_geral > 0:
                pct_mulheres = round((qtd_mulheres / total_geral) * 100, 2)
            
            output_data = {
                'metadata': {
                    'fonte': 'Senado Federal',
                    'tipo': 'Senadoras Federais',
                    'total_registros': len(senadoras_data),
                    'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'campos': [
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
                'senadoras': senadoras_data
            }
            
            print("3. Salvando arquivo JSON...")
            print(f"  ✓ Arquivo: {self.json_output_path}")
            
            with open(self.json_output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(output_data, jsonfile, ensure_ascii=False, indent=2)
            
            print(f"   ✓ Arquivo JSON salvo com sucesso!")
            print(f"   ✓ Total de senadoras: {len(senadoras_data)}")
            print(f"   ✓ Total de campos: 17 ✓")
            print(f"\n4. Estatísticas de preenchimento dos campos:\n")
            
            for campo, count in campos_nao_vazios.items():
                percentual = (count / len(senadoras_data)) * 100 if senadoras_data else 0
                barra = "█" * int(percentual / 5)
                print(f"   • {campo:20} {barra:20} {count:3}/{len(senadoras_data)} ({percentual:.1f}%)")
            
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

        senadoras_data = self.process_csv_to_json()
            
        success = self.save_to_json(senadoras_data)
        
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
    csv_input = '../data/senadoras.csv'
    json_output = '../data/senadoras.json'
    
    print("\n")
    print("┌" + "─" * 68 + "┐")
    print("│        CONVERSOR CSV PARA JSON - SENADORAS FEDERAIS                │")
    print()
    
    converter = SenadorasCSVToJSONConverter(csv_input, json_output)
    success = converter.convert()
    
    if success:
        print("[SUCESSO] Conversão bem-sucedida!")
        print(f"📄 Arquivo JSON disponível em: {json_output}")
        print()
    else:
        print("[ERRO] Erro na conversão!")
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