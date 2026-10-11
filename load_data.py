import sqlite3, glob, os
import pandas as pd

conn = sqlite3.connect("olist.db")
for f in glob.glob("data/*.csv"):
    nome = os.path.basename(f).replace("olist_", "").replace("_dataset.csv", "").replace(".csv", "")
    pd.read_csv(f).to_sql(nome, conn, if_exists="replace", index=False)
    print("carregou", nome)
conn.close()