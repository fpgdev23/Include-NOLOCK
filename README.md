# IncludeNoLock

Este projeto contém scripts Python desenvolvidos para automatizar a inclusão da instrução `WITH (NOLOCK)` em consultas SQL armazenadas em um banco de dados SQL Server. O objetivo principal é garantir que as leituras no banco não bloqueiem outras transações (Dirty Read), melhorando a performance em ambientes com alta concorrência.

## 🚀 Funcionalidades

- **Adição Automática de NOLOCK**: Varre uma tabela do banco de dados e atualiza colunas que contenham comandos SQL, inserindo `WITH (NOLOCK)` após o nome das tabelas em cláusulas `FROM` e `JOIN`.
- **Prevenção de Duplicidade**: O script identifica se o `WITH (NOLOCK)` já existe para evitar repetições desnecessárias.
- **Limpeza de NOLOCKs Duplicados**: Remove repetições bagunçadas ou mal formatadas de `WITH (NOLOCK)`, padronizando a sintaxe.
- **Diagnóstico de Queries**: Analisa as queries do banco para identificar quantas já possuem `NOLOCK`, quantas não possuem cláusulas de junção/origem e onde o script de atualização pode ter falhado.
- **Listagem de Tabelas**: Script utilitário para listar todas as tabelas disponíveis no banco de dados configurado.
- **Logs Detalhados**: Acompanhamento do processo através de logs informando o sucesso ou erro de cada operação.

## 📋 Requisitos

- Python 3.12
- Driver ODBC 18 para SQL Server (ou versão compatível)
- Bibliotecas listadas no `requirements.txt`

Instale as dependências com:
```bash
pip install -r requirements.txt
```

## ⚙️ Configuração

Antes de executar os scripts, você deve preencher as informações de conexão nos arquivos correspondentes.

### Nos arquivos `atualizar_banco.py`, `limpar_banco.py` e `diagnostico.py`:
Edite as variáveis na seção `--- Configurações do Banco ---` (ou similar):
- `SERVER`: Endereço do servidor SQL Server.
- `DATABASE`: Nome do banco de dados.
- `USER`: Seu usuário.
- `PASSWORD`: Sua senha.
- `TABELA`: Nome da tabela que contém as queries a serem processadas.
- `COLUNA_ID`: Nome da coluna de identificação única (ID).
- `COLUNA_SQL`: Nome da coluna que armazena o texto da query SQL.

### No arquivo `listar.py`:
Edite as variáveis `SERVER`, `DATABASE`, `USER` e `PASSWORD` para permitir a conexão.

## 📖 Como Usar

### 1. Listar Tabelas
Para verificar as tabelas disponíveis no seu banco:
```bash
python listar.py
```

### 2. Diagnóstico de Queries
Para analisar o estado atual das queries no banco antes de aplicar mudanças:
```bash
python diagnostico.py
```

### 3. Atualizar Queries
Para processar e adicionar o `WITH (NOLOCK)` nas queries da tabela configurada:
```bash
python atualizar_banco.py
```

### 4. Limpeza de Sujeira
Caso existam queries com múltiplos `NOLOCK` repetidos ou mal formatados, execute:
```bash
python limpar_banco.py
```

## ⚠️ Aviso
Sempre faça um backup dos seus dados antes de executar scripts que realizam `UPDATE` em massa no banco de dados.
