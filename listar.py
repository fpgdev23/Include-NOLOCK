import pyodbc

# Configurações
SERVER = 'preencha o endereço do servidor'
DATABASE = 'preencha o nome do banco de dados'
USER = 'preencha o usuário'
PASSWORD = 'preencha a senha'
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USER};PWD={PASSWORD};TrustServerCertificate=yes;'

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    print(f"--- LISTANDO TODAS AS TABELAS DO BANCO {DATABASE} ---")
    print("(Isso pode ser uma lista grande...)")
    print("-" * 50)

    # Query SEM FILTRO (WHERE) e ordenada por nome
    cursor.execute("SELECT table_schema, table_name FROM information_schema.tables ORDER BY table_name")

    tabelas = cursor.fetchall()

    for schema, nome in tabelas:
        print(f"📄 {schema}.{nome}")

    print("-" * 50)
    print(f"Total encontrado: {len(tabelas)} tabelas.")

except Exception as e:
    print(f"Erro: {e}")