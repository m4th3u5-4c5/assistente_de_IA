import sqlite3
import ollama

MODELO = "qwen2.5-coder:7b"
MAX_TENTATIVAS = 3

def get_schema(conn):
    rows = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    return "\n\n".join(r[0] for r in rows)

def limpar(sql):
    return sql.replace("```sql", "").replace("```", "").strip()

def chamar_modelo(system, messages):
    resp = ollama.chat(
        model=MODELO,
        messages=[{"role": "system", "content": system}] + messages,
    )
    return limpar(resp["message"]["content"])

def validar(sql):
    s = sql.strip().rstrip(";").lower()
    if not s.startswith(("select", "with")) or ";" in s:
        raise ValueError("Só consultas SELECT são permitidas")

def executar(sql):
    validar(sql)
    conn = sqlite3.connect("file:olist.db?mode=ro", uri=True)
    cursor = conn.execute(sql)
    colunas = [c[0] for c in cursor.description]
    return colunas, cursor.fetchmany(100)

def responder(pergunta, schema):
    system = (
        "Você gera queries SQLite. Responda APENAS com o SQL, "
        "sem markdown e sem explicações.\n\nSchema:\n" + schema
    )
    messages = [{"role": "user", "content": pergunta}]

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        sql = chamar_modelo(system, messages)
        print(f"\n[tentativa {tentativa}] SQL gerado:\n{sql}\n")
        try:
            return sql, executar(sql)
        except Exception as erro:
            print(f"Erro: {erro}")
            if tentativa == MAX_TENTATIVAS:
                return sql, None
            # devolve o erro pro modelo corrigir
            messages.append({"role": "assistant", "content": sql})
            messages.append({
                "role": "user",
                "content": f"Essa query deu erro: {erro}\n"
                           "Corrija e responda APENAS com o SQL corrigido.",
            })

if __name__ == "__main__":
    conn = sqlite3.connect("olist.db")
    schema = get_schema(conn)
    pergunta = input("Pergunte algo sobre os dados: ")
    sql, resultado = responder(pergunta, schema)

    if resultado is None:
        print("\nNão consegui gerar uma query válida depois de várias tentativas.")
    else:
        colunas, linhas = resultado
        print("Colunas:", colunas)
        for linha in linhas:
            print(linha)