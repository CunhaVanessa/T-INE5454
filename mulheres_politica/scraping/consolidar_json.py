import json
from datetime import datetime
from typing import Dict, List, Union
from pathlib import Path


class JSONConsolidator:
    """
    Mescla os arquivos JSON em um único arquivo consolidado
    mantendo metadados e informações de origem.
    """
    
    def __init__(self, deputadas_json: str, senadoras_json: str, vereadoras_json: str, output_json: str):
        """
        Inicializa o consolidador.
        
        Args:
            deputadas_json: Caminho para o JSON de deputadas
            senadoras_json: Caminho para o JSON de senadoras
            vereadoras_json: Caminho para o JSON de vereadoras
            output_json: Caminho para o JSON consolidado de saída
        """
        self.deputadas_json = deputadas_json
        self.senadoras_json = senadoras_json
        self.vereadoras_json = vereadoras_json
        self.output_json = output_json
    
    def load_json_file(self, filepath: str) -> Union[Dict, List]:
        """
        Carrega um arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo JSON
        
        Returns:
            Dados carregados do JSON (dict ou list) ou vazio se houver erro
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print(f"   ✗ Erro: Arquivo {filepath} não encontrado")
            return {}
        except json.JSONDecodeError:
            print(f"   ✗ Erro: Arquivo {filepath} não é um JSON válido")
            return {}
        except Exception as e:
            print(f"   ✗ Erro ao carregar {filepath}: {e}")
            return {}
    
    def consolidate(self) -> bool:
        """
        Consolida os JSONs em um único arquivo.
        
        Returns:
            bool: True se a consolidação foi bem-sucedida
        """
        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 10 + "CONSOLIDAÇÃO DE JSONs - MULHERES NA POLÍTICA" + " " * 13 + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        
        print("=" * 70)
        print("CONSOLIDANDO DADOS")
        print("=" * 70)
        
        # 1. Carregar JSON de deputadas
        print(f"\n1. Carregando deputadas de: {self.deputadas_json}")
        deputadas_data = self.load_json_file(self.deputadas_json)
        
        if not deputadas_data:
            print("   ✗ Falha ao carregar deputadas\n")
            deputadas_list = []
        else:
            deputadas_list = deputadas_data.get('deputadas', [])
            
        print(f"   ✓ {len(deputadas_list)} deputadas carregadas")
        
        # 2. Carregar JSON de senadoras
        print(f"\n2. Carregando senadoras de: {self.senadoras_json}")
        senadoras_data = self.load_json_file(self.senadoras_json)
        
        if not senadoras_data:
            print("   ✗ Falha ao carregar senadoras\n")
            senadoras_list = []
        else:
            senadoras_list = senadoras_data.get('senadoras', [])
            
        print(f"   ✓ {len(senadoras_list)} senadoras carregadas")

        # 3. Carregar JSON de vereadoras
        print(f"\n3. Carregando vereadoras de: {self.vereadoras_json}")
        vereadoras_data = self.load_json_file(self.vereadoras_json)
        
        vereadoras_list = []
        if not vereadoras_data:
            print("   ✗ Falha ao carregar vereadoras\n")
        else:
            if isinstance(vereadoras_data, list):
                vereadoras_list = vereadoras_data
            elif isinstance(vereadoras_data, dict):
                vereadoras_list = vereadoras_data.get('vereadoras', [])
            
        print(f"   ✓ {len(vereadoras_list)} vereadoras carregadas")
        
        # 4. Adicionar campo "cargo" para diferenciar
        print(f"\n4. Adicionando campo 'cargo' para identificação...")
        for deputada in deputadas_list:
            deputada['cargo'] = 'Deputada Federal'
        
        for senadora in senadoras_list:
            senadora['cargo'] = 'Senadora Federal'

        for vereadora in vereadoras_list:
            vereadora['cargo'] = 'Vereadora Municipal'
        
        print(f"   ✓ Campo 'cargo' adicionado a todos os registros")
        
        # 5. Consolidar listas
        print(f"\n5. Consolidando dados...")
        mulheres_politica = deputadas_list + senadoras_list + vereadoras_list
        total = len(mulheres_politica)
        print(f"   ✓ Total: {total} parlamentares")
        
        # Verificar requisito de 1.000 instâncias
        requisito_atendido = total >= 1000
        status_requisito = "✓ ATENDIDO" if requisito_atendido else "✗ NÃO ATENDIDO"
        print(f"   Requisito de 1.000 instâncias: {status_requisito}")
        
        # 6. Criar metadados consolidados
        print(f"\n6. Gerando metadados consolidados...")
        
        # Distribuição por cargo
        dist_cargo = {
            'Deputada Federal': len(deputadas_list),
            'Senadora Federal': len(senadoras_list),
            'Vereadora Municipal': len(vereadoras_list)
        }
        
        # Distribuição por partido
        dist_partido = {}
        for parlamentar in mulheres_politica:
            partido = parlamentar.get('partido', 'N/A')
            if partido: # Evita chaves vazias
                dist_partido[partido] = dist_partido.get(partido, 0) + 1
        
        # Ordenar partidos por quantidade
        dist_partido = dict(sorted(dist_partido.items(), key=lambda x: x[1], reverse=True))
        
        # Distribuição por UF
        dist_uf = {}
        for parlamentar in mulheres_politica:
            uf = parlamentar.get('uf', 'N/A')
            if uf:
                dist_uf[uf] = dist_uf.get(uf, 0) + 1
        
        # Ordenar UFs por quantidade
        dist_uf = dict(sorted(dist_uf.items(), key=lambda x: x[1], reverse=True))
        
        consolidated_data = {
            'metadata': {
                'projeto': 'Mulheres na Política Brasileira',
                'descricao': 'Dados consolidados de deputadas, senadoras e vereadoras brasileiras',
                'instituicao': 'Congresso Nacional e TSE',
                'total_registros': total,
                'data_consolidacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'fontes': [
                    {
                        'tipo': 'Deputadas Federais',
                        'fonte': 'Câmara dos Deputados',
                        'url': 'https://www.camara.leg.br',
                        'total': len(deputadas_list)
                    },
                    {
                        'tipo': 'Senadoras Federais',
                        'fonte': 'Senado Federal',
                        'url': 'https://www25.senado.leg.br',
                        'total': len(senadoras_list)
                    },
                    {
                        'tipo': 'Vereadoras Municipais',
                        'fonte': 'TSE',
                        'url': 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2024.zip',
                        'total': len(vereadoras_list)
                    }
                ],
                'campos_comuns': [
                    'nome',
                    'nome_civil',
                    'cargo',
                    'partido',
                    'uf',
                    'periodo_mandato',
                    'data_nascimento',
                    'naturalidade',
                    'fonte_dados',
                    'data_extracao'
                ],
                'distribuicoes': {
                    'por_cargo': dist_cargo,
                    'por_partido': dist_partido,
                    'por_uf': dist_uf
                }
            },
            'parlamentares': mulheres_politica
        }
        
        print(f"   ✓ Metadados gerados")
        
        # 7. Salvar JSON consolidado
        try:
            print(f"\n7. Salvando JSON consolidado...")
            print(f"   Arquivo: {self.output_json}")
            
            # Criar diretório se não existir
            Path(self.output_json).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.output_json, 'w', encoding='utf-8') as f:
                json.dump(consolidated_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✓ Arquivo salvo com sucesso!")
            
            # 8. Mostrar resumo final
            print()
            print("=" * 70)
            print("CONSOLIDAÇÃO CONCLUÍDA COM SUCESSO! ✓")
            print("=" * 70)
            print()
            print("📊 RESUMO FINAL:")
            print(f"   • Total de parlamentares: {total}")
            print(f"   • Deputadas Federais: {len(deputadas_list)}")
            print(f"   • Senadoras Federais: {len(senadoras_list)}")
            print(f"   • Vereadoras Municipais: {len(vereadoras_list)}")
            print(f"   • Arquivo consolidado: {self.output_json}")
            print()
            
            print("📈 DISTRIBUIÇÃO POR CARGO:")
            for cargo, count in dist_cargo.items():
                if total > 0:
                    percentual = (count / total) * 100
                    print(f"   • {cargo:20} {count:4} ({percentual:.1f}%)")
            print()
            
            print("🏛️ TOP 10 PARTIDOS:")
            for i, (partido, count) in enumerate(list(dist_partido.items())[:10], 1):
                if total > 0:
                    percentual = (count / total) * 100
                    barra = "█" * int(percentual * 2)
                    print(f"   {i:2}. {partido:10} {barra:20} {count:3} ({percentual:.1f}%)")
            print()
            
            print("🗺️ TOP 10 ESTADOS:")
            for i, (uf, count) in enumerate(list(dist_uf.items())[:10], 1):
                if total > 0:
                    percentual = (count / total) * 100
                    barra = "█" * int(percentual * 2)
                    print(f"   {i:2}. {uf:5} {barra:20} {count:3} ({percentual:.1f}%)")
            print()
            
            return True
        
        except Exception as e:
            print(f"   ✗ Erro ao salvar JSON consolidado: {e}\n")
            return False


def main():
    # Caminhos atualizados para os arquivos filtrados que você já tem
    deputadas_json = 'data/deputadas.json'
    senadoras_json = 'data/senadoras.json'
    vereadoras_json = 'data/vereadoras.json'
    output_json = 'data/mulheres_politica_consolidado.json'
    
    print("\n")
    print("┌" + "─" * 68 + "┐")
    print("│  CONSOLIDAÇÃO FINAL - MULHERES NA POLÍTICA BRASILEIRA             │")
    print("└" + "─" * 68 + "┘")
    print()
    
    consolidator = JSONConsolidator(deputadas_json, senadoras_json, vereadoras_json, output_json)
    success = consolidator.consolidate()
    
    if success:
        print("✅ Consolidação bem-sucedida!")
        print()
        print("ARQUIVO GERADO:")
        print(f"   {output_json} ← MULHERES NA POLITICA")
        print()
        print()
    else:
        print("❌ Erro na consolidação!")
        print()
        print("VERIFIQUE:")
        print("   • Se os arquivos de entrada existem (principalmente vereadoras.json)")
        print("   • Se há permissões de escrita")
        print()
    
    print("─" * 70)
    print()


if __name__ == "__main__":
    main()

# import json
# from datetime import datetime
# from pathlib import Path

# class JSONConsolidator:
#     def __init__(self, deputadas_json, senadoras_json, vereadoras_json, output_json):
#         self.files = {
#             'deputadas': deputadas_json,
#             'senadoras': senadoras_json,
#             'vereadoras': vereadoras_json
#         }
#         self.output_json = output_json
    
#     def load(self, path):
#         try:
#             with open(path, 'r', encoding='utf-8') as f:
#                 return json.load(f)
#         except: return {}

#     def consolidate(self):
#         print("\nCONSOLIDANDO DADOS UNIFICADOS...")
        
#         # ==========================================
#         # 1. CARREGAMENTO E NORMALIZAÇÃO DAS LISTAS
#         # ==========================================
#         data_raw = {k: self.load(v) for k, v in self.files.items()}
#         all_parlamentares = []
        
#         # Deputadas
#         deps = data_raw['deputadas'].get('deputadas', []) if isinstance(data_raw['deputadas'], dict) else []
#         for d in deps: d['cargo'] = 'Deputada Federal'
#         all_parlamentares.extend(deps)
        
#         # Senadoras
#         sens = data_raw['senadoras'].get('senadoras', []) if isinstance(data_raw['senadoras'], dict) else []
#         for s in sens: s['cargo'] = 'Senadora Federal'
#         all_parlamentares.extend(sens)
        
#         # Vereadoras
#         v_data = data_raw['vereadoras']
#         vers = v_data if isinstance(v_data, list) else v_data.get('vereadoras', [])
#         for v in vers: v['cargo'] = 'Vereadora'
#         all_parlamentares.extend(vers)

#         # ==========================================
#         # 2. CÁLCULO ESTATÍSTICO UNIFICADO (SOMA)
#         # ==========================================
#         stats_final = {
#             'total_mulheres': 0,
#             'total_homens': 0,
#             'total_geral': 0
#         }
        
#         # --- DEPUTADAS 
#         if isinstance(data_raw['deputadas'], dict):
#             meta = data_raw['deputadas'].get('metadata', {}).get('estatisticas_genero', {})
#             stats_final['total_mulheres'] += meta.get('total_mulheres', len(deps))
#             stats_final['total_homens'] += meta.get('total_homens', 0)

#         # --- SENADORAS 
#         if isinstance(data_raw['senadoras'], dict):
#             meta = data_raw['senadoras'].get('metadata', {}).get('estatisticas_genero', {})
#             stats_final['total_mulheres'] += meta.get('total_mulheres', len(sens))
#             stats_final['total_homens'] += meta.get('total_homens', 0)

#         # --- VEREADORAS 
#         if isinstance(v_data, dict):
#             meta = v_data.get('metadados', {})
#             stats_final['total_mulheres'] += meta.get('total_mulheres_eleitas', len(vers))
#             stats_final['total_homens'] += meta.get('total_homens_eleitos', 0)
        
#         # Totais Finais
#         stats_final['total_geral'] = stats_final['total_mulheres'] + stats_final['total_homens']
        
#         pct = 0
#         if stats_final['total_geral'] > 0:
#             pct = round((stats_final['total_mulheres'] / stats_final['total_geral']) * 100, 2)
            
#         print(f"   📊 ESTATÍSTICAS FINAIS:")
#         print(f"      • Mulheres: {stats_final['total_mulheres']}")
#         print(f"      • Homens:   {stats_final['total_homens']}")
#         print(f"      • Total:    {stats_final['total_geral']} ({pct}%)")

#         # ==========================================
#         # 3. CRIAÇÃO DO ARQUIVO FINAL
#         # ==========================================
#         consolidated = {
#             "metadata": {
#                 "projeto": "Mulheres na Política Brasileira",
#                 "data_consolidacao": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                 "total_registros_json": len(all_parlamentares),
#                 "estatisticas_genero": {
#                     "total_mulheres": stats_final['total_mulheres'],
#                     "total_homens": stats_final['total_homens'],
#                     "total_geral": stats_final['total_geral'],
#                     "porcentagem_mulheres": pct
#                 }
#             },
#             "parlamentares": all_parlamentares
#         }
        
#         Path(self.output_json).parent.mkdir(parents=True, exist_ok=True)
#         with open(self.output_json, 'w', encoding='utf-8') as f:
#             json.dump(consolidated, f, ensure_ascii=False, indent=2)
            
#         print(f"   ✓ Arquivo salvo: {self.output_json}")

# if __name__ == "__main__":
#     JSONConsolidator(
#         'data/deputadas.json',
#         'data/senadoras.json',
#         'data/vereadoras.json',
#         'data/mulheres_politica_consolidado.json'
#     ).consolidate()