# -*- coding: utf-8 -*-
# Ce script lit un fichier NDJSON local (monte par Docker)
# et le stream vers Kafka.

import json
import time
from kafka import KafkaProducer
import os

# --- Configuration ---
KAFKA_BROKER = 'kafka-broker:9092'
TOPIC_NAME = 'client_comments'
SLEEP_TIME = 1  # 1 seconde entre chaque avis

# Le chemin A L'INTERIEUR du conteneur ou le fichier sera monte
# (Ceci est defini dans le docker-compose.yml)
FILE_PATH = '/app/data.ndjson' 

def create_producer():
    """Initialise le producteur Kafka."""
    print("Connexion au broker Kafka a %s..." % KAFKA_BROKER)
    try:
        # Nous devons envoyer des 'bytes'
        # Le script Spark (API 0.8) s'attend a recevoir des 'bytes' 
        # qu'il decode automatiquement en 'str'.
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: v.encode('utf-8') 
        )
        print("Producteur connecte avec succes.")
        return producer
    except Exception as e:
        print("ERREUR: Impossible de se connecter a Kafka. Nouvelle tentative dans 5s...")
        print(e)
        time.sleep(5)
        return create_producer()

def stream_file(producer):
    """Lit le fichier NDJSON et l'envoie a Kafka, en boucle."""
    
    # Verifie si le fichier est accessible a l'interieur du conteneur
    if not os.path.exists(FILE_PATH):
        print("ERREUR FATALE: Fichier non trouve a %s" % FILE_PATH)
        print("Assurez-vous que le fichier 'data.ndjson' est dans le meme dossier que 'docker-compose.yml'")
        print("et que le 'docker-compose.yml' contient la section 'volumes'.")
        return

    print("Debut du streaming du fichier: %s" % FILE_PATH)
    
    batch_id = 0
    while True: # Boucle infinie pour simuler un flux
        with open(FILE_PATH, 'r') as f:
            for line in f:
                try:
                    # 1. Lire la ligne du fichier
                    line_data = line.strip()
                    if not line_data:
                        continue # Ignorer les lignes vides
                    
                    # 2. Convertir la ligne JSON en objet Python
                    data = json.loads(line_data)
                    
                    # 3. Ajouter les metadonnees
                    data['batch_id'] = batch_id
                    data['timestamp'] = time.time()
                    
                    # 4. Re-convertir en string JSON pour l'envoi
                    message_string = json.dumps(data)
                    
                    # 5. Envoyer a Kafka (le serializer s'occupe de l'encodage en bytes)
                    producer.send(TOPIC_NAME, value=message_string)
                    print("Envoye (Batch %d): %s..." % (batch_id, data['text'][:40]))
                    
                    batch_id += 1
                    time.sleep(SLEEP_TIME)

                except json.JSONDecodeError:
                    print("Erreur: Ligne mal formatee ignoree: %s" % line)
                except Exception as e:
                    print("Erreur d'envoi Kafka: %s" % e)
        
        print("Fin du fichier atteinte. Reprise au debut.")
        time.sleep(5) # Pause avant de relire le fichier

if __name__ == "__main__":
    producer = create_producer()
    stream_file(producer)