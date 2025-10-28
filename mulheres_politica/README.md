# Mulheres na Política Brasileira

Este projeto coleta e visualiza dados sobre a representatividade feminina no Congresso Nacional brasileiro, incluindo informações da Câmara dos Deputados e do Senado Federal.

## Estrutura do Projeto

```
mulheres_politica/
│
├── scraping/
│   ├── webscraping_camara.py    # Script para coletar dados da Câmara
│   ├── webscraping_senado.py    # Script para coletar dados do Senado
│   └── utils.py                 # Funções utilitárias para processamento
│
├── data/
│   ├── mulheres_politica.json   # Dados em formato JSON
│   └── mulheres_politica.csv    # Dados em formato CSV
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
cd T-INE5454/mulheres_politica
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

### Coleta de Dados

Para coletar dados da Câmara dos Deputados:
```bash
python scraping/webscraping_camara.py
```

Para coletar dados do Senado Federal:
```bash
python scraping/webscraping_senado.py
```

### Visualização

Para visualizar os dados, abra o arquivo `app_simulado/app_demo.html` em um navegador web.

## Funcionalidades

- **Web Scraping**: Coleta automatizada de dados sobre mulheres parlamentares
- **Processamento de Dados**: Limpeza e formatação dos dados coletados
- **Exportação**: Dados disponíveis em formatos JSON e CSV
- **Visualização**: Interface web interativa para análise dos dados

## Dados Coletados

O projeto coleta as seguintes informações:
- Nome da parlamentar
- Partido político
- Estado que representa
- Cargo (Deputada/Senadora)
- Legislatura

## Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto é desenvolvido como parte do trabalho da disciplina INE5454 da UFSC.

## Autores

- Vanessa Cunha

## Disciplina

INE5454 - Universidade Federal de Santa Catarina (UFSC)
