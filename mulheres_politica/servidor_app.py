"""
Servidor HTTP para servir a aplicação Mulheres na Política.
"""

import http.server
import socketserver
import os
import urllib.parse
from pathlib import Path


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.path = '/app_simulado/app_demo.html'
        
        return super().do_GET()
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def main():
    PORT = 8080
    
    caminho_script = Path(__file__).resolve().parent
    os.chdir(caminho_script)
    
    app_file = Path('app_simulado/app_demo.html')
    consolidado_json = Path('data/mulheres_politica_consolidado.json')
    deputadas_json = Path('data/deputadas.json')
    senadoras_json = Path('data/senadoras.json')
    vereadoras_json = Path('data/vereadoras.json')
 
    if not app_file.exists():
        print(f"⚠️  Arquivo não encontrado: {app_file}")
        return

    if not consolidado_json.exists():
        print(f"⚠️  Consolidado não encontrado: {consolidado_json} (Execute consolidar_json.py)")
        
    if not deputadas_json.exists():
        print(f"⚠️  Deputadas não encontrado: {deputadas_json}")
    
    if not senadoras_json.exists():
        print(f"⚠️  Senadoras não encontrado: {senadoras_json}")

    if not vereadoras_json.exists():
        print(f"⚠️  Vereadoras não encontrado: {vereadoras_json}")

    print(f"🚀 Iniciando servidor na porta {PORT}")
    print(f"📁 Diretório base: {os.getcwd()}")
    print(f"🌐 Acesse: http://localhost:{PORT}")
    print(f"📄 Página principal: app_simulado/app_demo.html")
    print(f"📊 Dados JSON: data/deputadas.json")
    print(f"📊 Dados JSON: data/senadoras.json")
    print(f"📊 Dados JSON: data/vereadoras.json")
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