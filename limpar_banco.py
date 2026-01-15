import pyodbc
import re
import logging

# --- Configurações do Banco ---
SERVER = '10.158.0.94'
DATABASE = 'FPG_MATRIZ_JAR_3.8'
USER = 'paloma'
PASSWORD = '020324Ip@'

# Tabela e Colunas
TABELA = 'FR_FONTEDADOS'
COLUNA_ID = 'FNT_CODIGO'
COLUNA_SQL = 'FNT_SQLSELECT'

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def limpar_sql_bagunçado(sql: str) -> str:
    if not sql:
        return sql

    # 1. Regex Agressivo: Encontra sequências repetidas e "sujas" de NOLOCK
    # Ex: "WITH (NOLOCK) With WITH (NOLOCK)(NoLock)" vira "WITH (NOLOCK)"
    # Ex: "With(NoLock) WITH (NOLOCK)" vira "WITH (NOLOCK)"
    padrao_sujeira = r'(?i)(\s*WITH\s*\(\s*NOLOCK\s*\))+(?:\s*(?:WITH|\(\s*NOLOCK\s*\)))+'

    # Substitui toda a sujeira encontrada por um único comando limpo
    sql_limpo = re.sub(padrao_sujeira, ' WITH (NOLOCK)', sql)

    # 2. Normalização Extra: Garante que "With(NoLock)" (sem espaço) vire " WITH (NOLOCK)" (com espaço e maiúsculo)
    # Isso padroniza até os que não estavam duplicados, mas estavam mal formatados.
    sql_limpo = re.sub(r'(?i)\s*WITH\s*\(\s*NOLOCK\s*\)', ' WITH (NOLOCK)', sql_limpo)

    return sql_limpo


def executar_limpeza():
    conn_str = (
        f'DRIVER={{ODBC Driver 18 for SQL Server}};'
        f'SERVER={SERVER};DATABASE={DATABASE};UID={USER};PWD={PASSWORD};'
        f'TrustServerCertificate=yes;'
    )

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        logger.info("--- INICIANDO LIMPEZA DE NOLOCKS DUPLICADOS ---")
        logger.info("Lendo queries do banco...")

        cursor.execute(f"SELECT {COLUNA_ID}, {COLUNA_SQL} FROM {TABELA}")
        rows = cursor.fetchall()

        total = len(rows)
        corrigidos = 0

        for row in rows:
            id_registro = row[0]
            sql_original = row[1]

            if not sql_original:
                continue

            # Aplica a limpeza
            sql_novo = limpar_sql_bagunçado(sql_original)

            # Se houve mudança (ou seja, tinha sujeira), atualiza o banco
            if sql_original != sql_novo:
                try:
                    cursor.execute(
                        f"UPDATE {TABELA} SET {COLUNA_SQL} = ? WHERE {COLUNA_ID} = ?",
                        (sql_novo, id_registro)
                    )
                    corrigidos += 1
                    logger.info(f"[LIMPEZA] ID {id_registro} corrigido.")
                except Exception as e:
                    logger.error(f"[ERRO] Falha ao limpar ID {id_registro}: {e}")

        conn.commit()
        logger.info("-" * 40)
        logger.info(f"FIM DA LIMPEZA. Total analisado: {total}")
        logger.info(f"Total de queries 'sujas' que foram limpas: {corrigidos}")
        logger.info("-" * 40)

    except Exception as e:
        logger.error(f"Erro fatal de conexão: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    executar_limpeza()