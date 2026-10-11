import sqlite3
import ollama

MODELO = "qwen2.5-coder:7b"

def get_schema(conn):
    rows = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    return "\n\n".join(r[0] for r in rows)

def gerar_sql(pergunta, schema):
    resp = ollama.chat(
        model=MODELO,
        messages=[
            {"role": "system", "content": f"Você gera queries SQLite. Responda APENAS com o SQL, sem markdown e sem explicações.\n\nSchema:\n{schema}"},
            {"role": "user", "content": pergunta},
        ],
    )
    sql = resp["message"]["content"].strip()
    return sql.replace("```sql", "").replace("```", "").strip()

def validar(sql):
    s = sql.strip().rstrip(";").lower()
    if not s.startswith(("select", "with")) or ";" in s:
        raise ValueError("Só consultas SELECT são permitidas")

def executar(sql):
    validar(sql)
    conn = sqlite3.connect("file:olist.db?mode=ro", uri=True)
    return conn.execute(sql).fetchmany(100)

if __name__ == "__main__":
    conn = sqlite3.connect("olist.db")
    schema = get_schema(conn)
    pergunta = input("Pergunte algo sobre os dados: ")
    sql = gerar_sql(pergunta, schema)
    print("\nSQL gerado:\n", sql, "\n")
    print(executar(sql))