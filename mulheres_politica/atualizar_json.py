#!/usr/bin/env python3
"""
Atualiza o arquivo deputadas_filtrado.json para:
1. Adicionar propriedade 'cargo' = 'Deputada' 
2. Filtrar registros inválidos (como "Comunicar erro")
3. Limpar dados problemáticos
"""

import json
import pandas as pd
from datetime import datetime

def atualizar_json():
    """Atualiza o JSON com melhorias."""
    
    # Ler o arquivo JSON atual
    with open('data/deputadas_filtrado.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    deputadas_originais = data['deputadas']
    print(f"Total de registros originais: {len(deputadas_originais)}")
    
    # Filtrar registros válidos (remover "Comunicar erro" e outros inválidos)
    deputadas_validas = []
    
    for deputada in deputadas_originais:
        nome_civil = deputada.get('nome_civil', '').strip()
        
        # Filtrar registros inválidos
        if (nome_civil and 
            nome_civil != 'N/A' and 
            'Comunicar erro' not in nome_civil and
            len(nome_civil) > 3):
            
            # Adicionar propriedade 'cargo'
            deputada['cargo'] = 'Deputada'
            
            # Limpar dados nulos/problemáticos
            for key, value in deputada.items():
                if value == 'N/A' or value == 'null':
                    deputada[key] = None
                elif isinstance(value, str) and value.strip() == '':
                    deputada[key] = None
            
            deputadas_validas.append(deputada)
    
    print(f"Total de registros válidos: {len(deputadas_validas)}")
    print(f"Registros removidos: {len(deputadas_originais) - len(deputadas_validas)}")
    
    # Atualizar metadados
    data_atualizacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Criar nova estrutura JSON
    json_atualizado = {
        "metadata": {
            "fonte": "Câmara dos Deputados",
            "url_fonte": "https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=&sexo=F",
            "data_extracao": data_atualizacao,
            "total_registros": len(deputadas_validas),
            "metodo_extracao": "Web Scraping - BeautifulSoup",
            "descricao": "Dados de deputadas federais brasileiras com informações detalhadas"
        },
        "deputadas": deputadas_validas
    }
    
    # Salvar arquivo atualizado
    with open('data/deputadas_filtrado.json', 'w', encoding='utf-8') as f:
        json.dump(json_atualizado, f, indent=2, ensure_ascii=False)
    
    print(f"Arquivo atualizado salvo com {len(deputadas_validas)} deputadas válidas")
    
    # Mostrar alguns exemplos dos dados atualizados
    print("\nPrimeiros 3 registros:")
    for i, deputada in enumerate(deputadas_validas[:3]):
        print(f"{i+1}. {deputada['nome_civil']} - {deputada['partido']} - Cargo: {deputada['cargo']}")

if __name__ == "__main__":
    atualizar_json()