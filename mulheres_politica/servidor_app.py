#!/usr/bin/env python3
"""
Servidor HTTP simples para servir a aplicação Mulheres na Política.
A página principal será servida diretamente na rota raiz (/).
"""

import http.server
import socketserver
import os
import urllib.parse
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Definir o diretório base como o diretório atual
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def do_GET(self):
        # Se a requisição for para a raiz (/), servir o app_demo.html
        if self.path == '/' or self.path == '/index.html':
            self.path = '/app_simulado/app_demo.html'
        
        # Servir outros arquivos normalmente
        return super().do_GET()
    
    def end_headers(self):
        # Adicionar headers CORS para permitir requisições do JSON
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    PORT = 8080
    
    # Mudar para o diretório do projeto
    os.chdir('/Users/vanessacunha/T-INE5454/mulheres_politica')
    
    # Verificar se os arquivos necessários existem
    app_file = Path('app_simulado/app_demo.html')
    json_file = Path('data/deputadas_filtrado.json')
    
    if not app_file.exists():
        print(f"⚠️  Arquivo não encontrado: {app_file}")
        return
    
    if not json_file.exists():
        print(f"⚠️  Arquivo não encontrado: {json_file}")
        print("Execute primeiro o conversor para gerar o arquivo JSON filtrado.")
        return
    
    print(f"🚀 Iniciando servidor na porta {PORT}")
    print(f"📁 Diretório base: {os.getcwd()}")
    print(f"🌐 Acesse: http://localhost:{PORT}")
    print(f"📄 Página principal: app_simulado/app_demo.html")
    print(f"📊 Dados JSON: data/deputadas_filtrado.json")
    print("\nPressione Ctrl+C para parar o servidor")
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Servidor parado.")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")

if __name__ == "__main__":
    main()