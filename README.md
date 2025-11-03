## Real-Time Customer Sentiment Stream (Hadoop/Spark/Kafka)

### Project Overview

This project implements a highly resilient, end-to-end Big Data pipeline for real-time sentiment analysis of customer reviews. It demonstrates core skills in distributed computing, data streaming, and cross-platform container orchestration.

### Key Features:

Real-time Ingestion: Leverages Kafka for high-throughput, fault-tolerant data streaming.

Distributed Processing: Utilizes Apache Spark Streaming on a Hadoop YARN cluster for scalable sentiment analysis.

Persistent Storage: Stores processed data in HDFS for archival 

Containerized Environment: Orchestrates all services using Docker and Docker Compose for easy deployment and isolation.

### Technologies Used:

Apache Spark (2.2.0, DStreams)

Apache Kafka (0.8 API)

Apache Hadoop (2.7.2, YARN/HDFS)

Python (Producer, Sentiment Analysis)

Docker / Docker Compose

## Explication du Pipeline (Schéma)

Votre architecture est divisée en trois phases principales, toutes orchestrées par Docker :

| Phase | Description | Technologies |
|-------|-------------|--------------|
| **1. Ingestion & Réception (Vélocité)** | Votre conteneur Producer (Python) lit le fichier `data.ndjson` depuis votre PC local (via un volume Docker) et publie chaque avis, ligne par ligne, dans le Topic Kafka (`client_comments`). | Python, Docker, Kafka |
| **2. Traitement & Analyse** | Spark Streaming (sur YARN) agit comme un consommateur. Il lit le flux Kafka, utilise une UDF (votre dictionnaire) pour classer le sentiment, et agrège les résultats toutes les 5 secondes. | Spark Streaming, YARN |
| **3. Persistance ** | Spark écrit les résultats dans deux systèmes différents : **Archivage (Volume)** : Les avis bruts et analysés sont stockés dans des dossiers horodatés sur HDFS. | HDFS |



### 🚀 Guide de Démarrage (Pour un Nouvel Utilisateur)

Ce guide fournit la séquence de commandes complète pour lancer le pipeline depuis zéro.

### Pré-requis

Git et Docker Desktop (Doit être en cours d'exécution).

Le dossier du projet contient tous les fichiers (y compris docker-compose.yml, sentiment_analysis.py, et votre fichier de données data.ndjson).

## Phase 1: Déploiement et Démarrage du Cluster Hadoop

Le cluster Hadoop (Master/Slaves) est lancé manuellement pour créer le réseau de base (hadoop) nécessaire à tous les autres services.

# Entrer dans le dossier du projet
```bash
cd votre-dossier-de-projet
```

# 1. Télécharger l'image de base Hadoop/Spark
```bash
docker pull liliasfaxi/spark-hadoop:hv-2.7.2
```

# 2. Créer le réseau interne 'hadoop'
```bash
docker network create --driver=bridge hadoop
```

# 3. Lancer le Master Hadoop (NameNode/YARN)
```bash
docker run -itd --net=hadoop -p 9870:9870 -p 8088:8088 -p 7077:7077 -p 16010:16010 --name hadoop-master --hostname hadoop-master liliasfaxi/spark-hadoop:hv-2.7.2
```

# 4. Lancer les deux Slaves Hadoop (DataNodes/NodeManagers)
```bash
docker run -itd -p 8040:8042 --net=hadoop --name hadoop-slave1 --hostname hadoop-slave1 liliasfaxi/spark-hadoop:hv-2.7.2
docker run -itd -p 8041:8042 --net=hadoop --name hadoop-slave2 --hostname hadoop-slave2 liliasfaxi/spark-hadoop:hv-2.7.2
```

## Phase 2: Activation des Services Hadoop/YARN

Les services internes sont souvent bloqués ou arrêtés au démarrage du conteneur. Nous devons les démarrer et débloquer YARN.

# 1. Entrer dans le Master et exécuter le script de démarrage
```bash
docker exec -it hadoop-master bash -c "./start-hadoop.sh"
```

# 2. Forcer la désactivation du mode sécurisé HDFS (Safe Mode)
# C'est crucial pour débloquer YARN et permettre à Spark de sauvegarder les données.
```bash
docker exec -it hadoop-master hdfs dfsadmin -safemode leave
```

## Phase 3: Déploiement de la Pipeline de Flux (Kafka/Producer)

Nous utilisons docker-compose pour lancer les services de streaming et monter le fichier de données local.

# 1. Construire l'image du Producteur et démarrer Kafka/Zookeeper/Producer
# Le Producer lira le fichier data.ndjson de votre machine hôte grâce à la section 'volumes' du docker-compose.yml.
```bash
docker-compose up -d --build
```

## Phase 4: Lancement du Job Spark Streaming

L'infrastructure est stable et le Producteur envoie des données. Nous lançons l'analyse.

# 1. Copier le script PySpark (sentiment_analysis.py) dans le Master
```bash
docker cp sentiment_analysis.py hadoop-master:/opt/
```

# 2. Lancer le Job Spark sur YARN
# NOTE: La commande inclut la compatibilité Python 3 et le package Kafka 0.8 nécessaire.
```bash
docker exec -it hadoop-master bash -c "PYSPARK_PYTHON=python3 spark-submit --packages org.apache.spark:spark-streaming-kafka-0-8-assembly_2.11:2.2.0 --master yarn --deploy-mode client /opt/sentiment_analysis.py"
```

## ✅ Vérification et Sortie des Données

1. Vérification de la Persistance HDFS

Pour vérifier que le job écrit les données :

# Entrer dans le Master container
```bash
docker exec -it hadoop-master bash
```
# Lister le dossier des comptages (Batch et Comptages)
```bash
hdfs dfs -ls /user/root/testProject/sentiment_counts_v2

# Pour lire le contenu d'un fichier de comptage (ex: POSITIF/NEGATIF)
# REMPLACER les placeholders XXXXXX par les vrais noms de fichiers
# hdfs dfs -cat /user/root/testProject/sentiment_counts_v2/batch-XXXXXX/part-XXXXXX.json
```

2. Surveillance

Statut YARN (Applications) : http://localhost:8088

🛑 Arrêt de la Pipeline

Pour arrêter tous les services proprement :

# 1. Arrêter le Job Spark (Ctrl+C dans le terminal où il tourne)
# 2. Arrêter les services Kafka/Zookeeper/Producer
```bash
docker-compose down
```
# 3. Arrêter les conteneurs Hadoop Master et Slaves
```bash
docker stop hadoop-master hadoop-slave1 hadoop-slave2
docker rm hadoop-master hadoop-slave1 hadoop-slave2
```
# 4. Supprimer le réseau Docker
```bash
docker network rm hadoop
```
