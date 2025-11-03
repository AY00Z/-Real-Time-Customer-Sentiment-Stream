# -*- coding: utf-8 -*-
# Version 2 (V1 DStreams)
# MISE A JOUR: Ajout d'un dictionnaire de sentiments et d'un comptage des agregats.

from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils 
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType
import time
import json 

# --- 1. Dictionnaire de Mots-Cles (MIS A JOUR) ---
# (Nous utilisons des 'set' pour une recherche plus rapide)
MOTS_POSITIFS = set(['adore', 'incroyable', 'depasse', 'bon', 'super', 'excellent', 'parfait', 'magnifique', 'genial', 'ravi'])
MOTS_NEGATIFS = set(['decu', 'mediocre', 'regrette', 'mal', 'mauvais', 'terrible', 'horrible', 'fuir', 'nul', 'arnaque', 'catastrophe'])

# --- 2. Logique UDF (User Defined Function) (MISE A JOUR) ---

def classify_sentiment_from_dict(text):
    """
    Classifie le sentiment en fonction du dictionnaire de mots-cles.
    """
    if text is None:
        return "NEUTRE"
        
    text_lower = text.lower()
    mots = text_lower.split() # Separe le texte en mots
    
    score = 0
    for mot in mots:
        if mot in MOTS_POSITIFS:
            score += 1
        if mot in MOTS_NEGATIFS:
            score -= 1
            
    if score > 0:
        return "POSITIF"
    elif score < 0:
        return "NEGATIF"
    else:
        return "NEUTRE"

# Mise a jour de l'UDF pour utiliser la nouvelle fonction
classification_udf = udf(classify_sentiment_from_dict, StringType())


# --- 3. Logique de Flux (DStreams) (MISE A JOUR) ---

def process_rdd(time_val, rdd):
    """Processus execute sur chaque micro-lot (RDD)."""
    
    if rdd.isEmpty():
        return
        
    try:
        spark = SparkSession.builder.appName("SentimentAnalysisStream").getOrCreate()
        
        # 1. Extraction et conversion des donnees JSON
        rows_data = rdd.map(lambda x: json.loads(x[1])).collect()
        
        if not rows_data:
            return

        df = spark.createDataFrame(rows_data)
        
        # 2. Appliquer la Logique d'Analyse (UDF)
        df_classified = df.withColumn(
            "sentiment_label", 
            classification_udf(col("text")) # Utilise la nouvelle UDF
        ).select(
            col("batch_id"),
            col("id").alias("review_id"),
            col("client"),
            col("text").alias("review_text"),
            col("sentiment_label"),
            col("timestamp")
        )

        # 3. Ecrire les resultats dans HDFS (AVIS INDIVIDUELS)
        # (Nouveau chemin pour la V2)
        HDFS_OUTPUT_PATH = "hdfs://hadoop-master:9000/user/root/testProject/sentiment_output_v2"
        output_dir = HDFS_OUTPUT_PATH + "/batch-" + time_val.strftime('%Y%m%d%H%M%S')
        df_classified.write.json(output_dir, mode="append")
        
        print("\nLot (Avis Individuels) ecrit dans HDFS: %s" % output_dir)

        # 4. (NOUVEAU) Calculer les COMPTAGES et les ecrire dans HDFS
        df_counts = df_classified.groupBy("sentiment_label").count()
        
        HDFS_COUNTS_PATH = "hdfs://hadoop-master:9000/user/root/testProject/sentiment_counts_v2"
        output_dir_counts = HDFS_COUNTS_PATH + "/batch-" + time_val.strftime('%Y%m%d%H%M%S')
        df_counts.write.json(output_dir_counts, mode="append")

        print("Lot (Comptages) ecrit dans HDFS: %s" % output_dir_counts)

    except Exception as e:
        print("Erreur de traitement du lot: %s" % str(e))

def run_streaming_job():
    sc = SparkContext(appName="SentimentAnalysisStream")
    sc.setLogLevel("WARN")
    ssc = StreamingContext(sc, 5) # Lot de 5 secondes

    zk_quorum = "zookeeper:2181"
    group_id = "spark-sentiment-group-v8"
    topic_map = {"client_comments": 1} 

    kafka_stream = KafkaUtils.createStream(ssc, zk_quorum, group_id, topic_map)

    kafka_stream.foreachRDD(lambda time_val, rdd: process_rdd(time_val, rdd))

    ssc.start()
    print("\n*** Spark Streaming (V1 DStreams - Dictionnaire) demarre. ***\n") # (Message mis a jour)
    print("Consultez http://localhost:8088 pour le statut YARN. Appuyez sur Ctrl+C pour arreter le job.")
    ssc.awaitTermination()

if __name__ == "__main__":
    run_streaming_job()