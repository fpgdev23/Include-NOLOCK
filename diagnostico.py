import pyodbc
import re

# --- Configurações ---
SERVER = '10.158.0.94'
DATABASE = 'FPG_MATRIZ_JAR_3.8'
USER = 'paloma'
PASSWORD = '020324Ip@'
TABELA = 'FR_FONTEDADOS'


def classificar_motivo(sql: str) -> str:
    """
    Heurística para dizer por que provavelmente o regex
    (do script que adiciona NOLOCK) não conseguiu tratar a query.
    """
    up = sql.upper()

    if "FROM(" in up or "FROM (" in up or "JOIN(" in up or "JOIN (" in up:
        return "FROM/JOIN com subselect ou derived table (parênteses após FROM/JOIN)."

    if "UNION ALL" in up or "UNION " in up:
        return "Query com UNION/UNION ALL (múltiplos SELECTs)."

    if "OPENQUERY(" in up:
        return "Uso de OPENQUERY (fonte de dados remota)."

    if "CROSS APPLY" in up or "OUTER APPLY" in up:
        return "Uso de CROSS/OUTER APPLY."

    if " PIVOT " in up or " UNPIVOT " in up:
        return "Uso de PIVOT/UNPIVOT."

    if "," in up.split("FROM", 1)[1].split("WHERE", 1)[0]:
        # Select ... FROM T1, T2, T3 ...
        return "Join por vírgula na cláusula FROM (sem JOIN explícito)."

    return "Sintaxe não suportada pelo regex (JOIN/alias diferente ou padrão não mapeado)."


def diagnostico():
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={SERVER};DATABASE={DATABASE};UID={USER};PWD={PASSWORD};"
        "TrustServerCertificate=yes;"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Pegamos também o FNT_CODIGO para identificar a fonte
    cursor.execute(f"SELECT FNT_CODIGO, FNT_SQLSELECT FROM {TABELA}")
    rows = cursor.fetchall()

    contador_ja_tem = 0
    contador_sem_from = 0
    contador_problema_regex = 0

    problemas = []  # lista com detalhamento das que não foram tratadas

    print(f"Analisando {len(rows)} linhas...")

    for fnt_codigo, sql in rows:
        if not sql:
            continue

        sql_up = sql.upper()

        # 1. Já tem NOLOCK
        if "NOLOCK" in sql_up:
            contador_ja_tem += 1
            continue

        # 2. Não tem FROM nem JOIN -> provavelmente não é SELECT em tabela
        if "FROM" not in sql_up and "JOIN" not in sql_up:
            contador_sem_from += 1
            problemas.append(
                {
                    "fnt_codigo": fnt_codigo,
                    "motivo": "Não contém FROM/JOIN (provavelmente EXEC, expressão ou comando não-SELECT).",
                    "sql": sql,
                }
            )
            continue

        # 3. Tem FROM/JOIN e não tem NOLOCK -> aqui é onde o regex falharia
        contador_problema_regex += 1
        motivo = classificar_motivo(sql)
        problemas.append(
            {
                "fnt_codigo": fnt_codigo,
                "motivo": motivo,
                "sql": sql,
            }
        )

    print("-" * 60)
    print("RESULTADO DO DIAGNÓSTICO:")
    print(f"Total de linhas analisadas: ............ {len(rows)}")
    print(f"1. Já possuíam NOLOCK: ................. {contador_ja_tem}")
    print(f"2. Sem FROM/JOIN (não são SELECT puros): {contador_sem_from}")
    print(f"3. Com FROM/JOIN sem NOLOCK (problema):  {contador_problema_regex}")
    print("-" * 60)

    if problemas:
        print("\nDETALHAMENTO DAS QUERIES NÃO TRATADAS:\n")
        for p in problemas:
            print(f"FNT_CODIGO: {p['fnt_codigo']}")
            print(f"Motivo: {p['motivo']}")
            # mostra só o começo para não explodir o terminal
            trecho = p["sql"].replace("\n", " ")
            if len(trecho) > 300:
                trecho = trecho[:300] + " ..."
            print(f"SQL: {trecho}")
            print("-" * 60)


if __name__ == "__main__":
    diagnostico()
