import pandas as pd

mapa = pd.read_csv("grafo.csv", header= None).values
conexiones = pd.read_csv("conexiones15.csv", index_col = [0]).to_dict("index")