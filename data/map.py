A = "Autoroute"
V = "Voie rapide"
N = "Nationale"
D = "Départementale"

{"Toulouse":{"Blagnac":[10,A], "Colomiers":[15, N],"Tournefeuille":[8, A]},
"Blagnac":{"Toulouse":[10, A], "Aussonne":[9,D], "Colomiers":[7, V]},
"Colomiers":{"Toulouse":[15, N], "Blagnac":[7, V],"Tournefeuille":[5,D], "Aussonne":[12,N]},
"Tournefeuille":{"Toulouse":[8,A], "Colomiers":[5, D]},
"Aussonne":{"Blagnac":[9,D], "Colomiers":[12, N]}
}