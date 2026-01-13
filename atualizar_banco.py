import pyodbc
import re
import logging

# --- Configurações do Banco ---
SERVER = 'preencha o endereço do servidor'
DATABASE = 'preencha o nome do banco de dados'
USER = 'preencha o usuário'
PASSWORD = 'preencha a senha'

# Tabela e Colunas
TABELA = 'preencha o nome da tabela'
COLUNA_ID = 'preencha o nome da coluna de ID'
COLUNA_SQL = 'preencha o nome da coluna que contém o SQL'

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Lógica para forçar WITH (NOLOCK) em todas as tabelas de FROM / JOIN ---
def add_nolock_to_sql(sql: str) -> str:
    if not sql:
        return sql

    # 1) Normaliza duplicações de NOLOCK: "WITH (NOLOCK) WITH (NOLOCK)" -> "WITH (NOLOCK)"
    sql = re.sub(
        r'WITH\s*\(\s*NOLOCK\s*\)(\s*WITH\s*\(\s*NOLOCK\s*\))+',
        'WITH (NOLOCK)',
        sql,
        flags=re.IGNORECASE
    )

    # Palavras que NÃO podem ser consideradas Alias de tabela
    SQL_KEYWORDS = {
        "WHERE", "ON", "GROUP", "ORDER", "HAVING", "UNION", "LIMIT",
        "JOIN", "INNER", "LEFT", "RIGHT", "FULL", "CROSS", "OUTER",
        "GO", ")", "AND", "OR", "WITH"   # <- importante para não tratar WITH como alias
    }

    # FROM / JOIN + (comentários opcionais) + tabela + alias opcional (mas NÃO 'WITH') + hint opcional
    pattern = re.compile(
        r"""(?P<prefix>\b(?:FROM|(?:INNER|LEFT|RIGHT|FULL|CROSS|OUTER\s+)?JOIN)\s+(?:/\*.*?\*/\s*)*)"""
        r"""(?P<table>[\w\.\[\]"']+)"""
        r"""(?P<alias>\s+(?:AS\s+)?(?!WITH\b)[\w\[\]"']+)?"""
        r"""(?P<hint>\s+WITH\s*\(\s*NOLOCK\s*\))?""",
        re.IGNORECASE | re.DOTALL
    )

    def replacement(match):
        prefix = match.group('prefix')
        table = match.group('table')
        alias = match.group('alias') or ''
        hint = match.group('hint')

        # Já tem WITH (NOLOCK) nessa referência → mantém como está
        if hint:
            return match.group(0)

        clean_alias = alias.strip().upper()
        if clean_alias.startswith("AS "):
            clean_alias = clean_alias[3:].strip()

        # Se o "alias" na verdade é uma palavra reservada (ex.: WHERE, ON),
        # colocamos o NOLOCK ANTES desse pseudo-alias
        if clean_alias in SQL_KEYWORDS and clean_alias != "":
            return f"{prefix}{table} WITH (NOLOCK){alias}"

        # Caso normal: tabela + alias real (ou sem alias)
        return f"{prefix}{table}{alias} WITH (NOLOCK)"

    return pattern.sub(replacement, sql)


def processar_banco():
    conn_str = (
        f'DRIVER={{ODBC Driver 18 for SQL Server}};'
        f'SERVER={SERVER};DATABASE={DATABASE};UID={USER};PWD={PASSWORD};'
        f'TrustServerCertificate=yes;'
    )

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        logger.info("Lendo dados do banco...")
        cursor.execute(f"SELECT {COLUNA_ID}, {COLUNA_SQL} FROM {TABELA}")
        rows = cursor.fetchall()

        total = len(rows)
        atualizados = 0

        logger.info(f"Total de linhas para analisar: {total}")

        for row in rows:
            id_registro = row[0]
            sql_original = row[1]

            if not sql_original:
                continue

            sql_novo = add_nolock_to_sql(sql_original)

            if sql_original != sql_novo:
                try:
                    cursor.execute(
                        f"UPDATE {TABELA} SET {COLUNA_SQL} = ? WHERE {COLUNA_ID} = ?",
                        (sql_novo, id_registro)
                    )
                    atualizados += 1
                    logger.info(f"[UPDATE] ID {id_registro} atualizado com sucesso.")
                except Exception as e:
                    logger.error(f"[ERRO] Falha ao atualizar ID {id_registro}: {e}")

        conn.commit()
        logger.info(f"Processo finalizado! {atualizados} queries foram modificadas de um total de {total}.")

    except Exception as e:
        logger.error(f"Erro de conexão ou execução: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    processar_banco()
