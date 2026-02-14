# IoT Tracking Platform (CoAP + Thread/OpenThread + MQTT + Web)



### Description
Ce projet met en place une architecture IoT complète pour un cas de tracking (GPS + température + batterie).  
Les capteurs (simulés) exposent des ressources CoAP (UDP). Le backend FastAPI interroge les capteurs, valide et persiste les données dans PostgreSQL, puis les publie en MQTT via Mosquitto pour un affichage temps réel dans une interface web (Leaflet). L’application permet également de consulter l’historique des sessions.









### Services (Docker Compose)
- **frontend** : page web (Leaflet) + MQTT WebSocket
- **backend** : FastAPI (API REST + client CoAP + publisher MQTT)
- **postgres** : stockage (`users`, `sessions`, `gps_points`, etc.)
- **mosquitto** : broker MQTT (TCP + WebSocket)
- **otbr** : OpenThread Border Router (mode host)
- **gps / temperature / battery** : capteurs OpenThread / CoAP (mode host)





## Prérequis
- Docker + Docker Compose


## Démarrage
```bash
docker compose up -d --build
```

Accès :
- Frontend : http://localhost:3000
- Backend : http://localhost:8000


## Utilisation (test rapide de l’application)
1. Ouvrir http://localhost:3000  
2. Utiliser l’utilisateur de test suivant :

- **Nom** : `user`  
- **Prénom** : `test`  
- **Adresse mail** : `test@gmail.com`

3. Cliquer sur Commencer le tracking**
4. Cliquer sur Arrêter le tracking**
5. Cliquer sur Voir l’historique**




## Points importants du projet
- **Simulateurs optimisés** : les valeurs ne sont pas totalement aléatoires ; elles évoluent de façon plus réaliste (inertie température, décharge batterie, parcours GPS cohérent).
- **Validation des données** : des règles (format, champs obligatoires, bornes plausibles) sont appliquées côté backend avant **persistance** et avant **publication MQTT**, afin de garantir des données cohérentes en base et dans l’UI.
- **Données seedées** : des enregistrements sont insérés pour permettre de tester rapidement les fonctionnalités (login, sessions, historique).






## Arrêt / Reset
Arrêter :
```bash
docker compose down
```

Reset complet (supprime les volumes / données) :
```bash
docker compose down -v
```

Auteur : Dyhia & Sarah
