import json
A= "Autoroute"
V = "Voie rapide"
N = "Nationale"
D = "Départementale"

maping = {
"Toulouse":{
    "Blagnac":[10,A,True,4.6],
    "Colomiers":[15,N,False,10.0],
    "Tournefeuille":[7,A,True,3.2]
},
"Blagnac":{
    "Toulouse":[10,A,True,4.6],
    "Aussonne":[9,D,False,6.8],
    "Colomiers":[7,V,False,3.8]
},
"Colomiers":{
    "Toulouse":[15,N,False,10.0],
    "Blagnac":[7,V,False,3.8],
    "Tournefeuille":[5,D,False,3.8],
    "Aussonne":[12,N,False,8.0]
},
"Tournefeuille":{
    "Toulouse":[8,A,True,3.7],
    "Colomiers":[5,D,False,3.8]
},
"Aussonne":{
    "Blagnac":[9,D,False,6.8],
    "Colomiers":[12,N,False,8.0]
}
}

with open(r"src\data\dico_final.json",encoding="utf-8") as f:
    maping1 = json.load(f)

