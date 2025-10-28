# Mulheres na Política Brasileira

Este projeto coleta e visualiza dados sobre a representatividade feminina no Congresso Nacional brasileiro, incluindo informações da Câmara dos Deputados, Senado Federal e Câmaras Municipais. O projeto utiliza **web scraping real** de páginas HTML para coletar dados atualizados sobre mulheres parlamentares.

## Estrutura do Projeto

```
mulheres_politica/
│
├── scraping/
│   ├── webscraping_deputadas.py # Script para coletar dados da Câmara dos Deputados (PRONTO)
│   ├── webscraping_senadoras.py # Script para coletar dados do Senado (em desenvolvimento)
│   ├── webscraping_vereadoras.py# Script para coletar dados municipais (em desenvolvimento)
│   └── utils.py                 # Funções utilitárias para processamento
│
├── data/
│   ├── deputadas.csv            # Dados das deputadas federais (344 registros) (PRONTO)
│   ├── senadoras.csv            # Dados das senadoras (em desenvolvimento)
│   └── vereadoras.csv           # Dados das vereadoras (em desenvolvimento)
│
├── app_simulado/
│   ├── app_demo.html            # Interface web para visualização
│   └── prints/                  # Screenshots da aplicação
│
├── README.md
└── requirements.txt
```

## Requisitos

- Python 3.7+
- Bibliotecas listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/CunhaVanessa/T-INE5454.git
cd T-INE5454
```

2. Navegue para o diretório do projeto:
```bash
cd mulheres_politica
```

3. Crie um ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

### Coleta de Dados das Deputadas Federais (PRONTO)

O scraper das deputadas está **totalmente funcional** e coleta dados de todas as mulheres deputadas federais:

```bash
cd scraping
python webscraping_deputadas.py
```

**Características do scraper:**
- Coleta **344 deputadas federais** (dados completos de 2024)
- **Web scraping real** de HTML (não usa APIs - conforme requisitos do curso)
- **Paginação automática** - processa todas as páginas até encontrar "Nenhuma ocorrência encontrada"
- **Filtro de gênero** aplicado corretamente (`sexo=F`)
- **Delay entre requisições** (2 segundos) para evitar sobrecarga do servidor
- **Tratamento de erros** robusto com retry automático
- **Dados salvos em CSV** com encoding UTF-8

**Dados coletados:**
- Nome completo da deputada
- Partido político
- Estado (UF)
- Legislatura
- Situação (Em exercício/Ex-deputado)
- Link do perfil oficial
- Metadados de coleta (data, método, fonte)

### Próximos Scrapers (Em Desenvolvimento)

Para coletar dados do Senado Federal:
```bash
python scraping/webscraping_senadoras.py  # Em desenvolvimento
```

Para coletar dados municipais:
```bash
python scraping/webscraping_vereadoras.py  # Em desenvolvimento
```

### Visualização dos Dados

Para visualizar os dados coletados:
```bash
# Abrir o dashboard web
open app_simulado/app_demo.html  # macOS
# ou abrir manualmente no navegador
```

### Verificação dos Dados

Para verificar os dados coletados:
```bash
# Ver estatísticas rápidas
wc -l data/deputadas.csv        # Contar linhas (deve mostrar 345: 344 deputadas + cabeçalho)
head -5 data/deputadas.csv      # Ver primeiros registros
tail -5 data/deputadas.csv      # Ver últimos registros
```

### Exemplo de Saída do Scraper

```
INICIANDO WEB SCRAPING - DEPUTADAS FEDERAIS
============================================================
Acessando página da Câmara dos Deputados...
URL: https://www.camara.leg.br/deputados/quem-sao
Status da requisição: 200
Acessando diretamente página filtrada para deputadas mulheres...
URL de busca: https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=&sexo=F
Status da busca filtrada: 200
Busca filtrada realizada com sucesso!
Processando resultados paginados...
Processando página 1...
Página 1: 25 deputadas encontradas
...
Processando página 14: 
Página 14: 19 deputadas encontradas
Processando página 15:
Página 15: encontrada mensagem de fim da busca
Finalizando coleta - todas as páginas foram processadas
RESULTADO FINAL: 344 deputadas coletadas de 15 páginas processadas

SCRAPING CONCLUÍDO COM SUCESSO!
Total de deputadas coletadas: 344
Dados salvos em: ../data/deputadas.csv
============================================================
```

## Funcionalidades Técnicas

### Web Scraping Avançado
- **Requisições HTTP com sessão persistente** usando `requests.Session()`
- **Parsing HTML robusto** com `BeautifulSoup4` e múltiplos seletores CSS
- **User-Agent personalizado** para evitar bloqueios
- **Paginação automática inteligente** até encontrar fim dos resultados
- **Tratamento de erros** com retry automático e fallbacks

### Características do Código
- **Documentação completa** com docstrings em português
- **Type hints** para melhor legibilidade e manutenção
- **Logging detalhado** do processo de coleta
- **Validação de dados** antes da gravação
- **Estrutura modular** com funções especializadas

### Conformidade com Requisitos Acadêmicos
- **Web scraping real de HTML** (não utiliza APIs REST)
- **Múltiplas fontes de dados** (Câmara, Senado, Municípios)
- **Processamento de grandes volumes** (centenas de registros por fonte)
- **Tratamento de diferentes estruturas HTML** por site
- **Dados salvos em formato padrão** (CSV com UTF-8)

## Dados Coletados

### Deputadas Federais (344 registros)
| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `nome` | Nome completo | "Adriana Ventura (NOVO-SP)" |
| `partido` | Sigla do partido | "NOVO" |
| `uf` | Estado | "SP" |
| `legislatura` | Período do mandato | "Múltiplas legislaturas" |
| `situacao` | Status atual | "Em exercício" |
| `link_perfil` | URL oficial | "https://www.camara.leg.br/deputados/204528" |
| `fonte_dados` | Método de coleta | "Web Scraping HTML" |
| `url_fonte` | URL de origem | URL da página de resultados |
| `data_extracao` | Timestamp | "2025-10-28 15:31:14" |
| `metodo_extracao` | Ferramenta usada | "BeautifulSoup - Câmara dos Deputados" |

### Próximas Coletas
- **Senadoras**: ~15-20 registros esperados
- **Vereadoras**: Volume variável por município selecionado

## Licença

Este projeto é desenvolvido como parte do trabalho da disciplina INE5454 da UFSC.

## Autores

- Vanessa Cunha
- Jaqueline Bieber
- Arthur  Lorenzetti

## Disciplina

INE5454 - Universidade Federal de Santa Catarina (UFSC)
