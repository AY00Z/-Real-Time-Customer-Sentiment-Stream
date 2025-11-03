Real-Time Customer Sentiment Stream (Hadoop/Spark/Kafka)

Project Overview

This project implements a highly resilient, end-to-end Big Data pipeline for real-time sentiment analysis of customer reviews. It demonstrates core skills in distributed computing, data streaming, and cross-platform container orchestration.

Technologies Used:

Apache Spark (2.2, DStreams)

Apache Kafka (0.8 API)

Apache Hadoop (YARN/HDFS)

Python (Producer)

Docker / Docker Compose

🚀 Environment Setup Guide (Start-to-Finish)

This guide provides the exact steps to launch the entire pipeline from scratch, assuming only Git and Docker Desktop are installed on your machine.

Prerequisites

Git and Docker Desktop (Running).

All project files (docker-compose.yml, producer.py, sentiment_analysis.py, data.ndjson, etc.) must be in your current directory.

Phase 1: Deploying the Core Hadoop Cluster

The Hadoop cluster (Master/Slaves) must be launched manually to set up the foundation network (hadoop).

# 1. Download the legacy Hadoop/Spark image (needed for Spark 2.2 compatibility)
docker pull liliasfaxi/spark-hadoop:hv-2.7.2

# 2. Create the internal 'hadoop' network
docker network create --driver=bridge hadoop

# 3. Launch Hadoop Master (NameNode/YARN) and Slaves (DataNodes)
docker run -itd --net=hadoop -p 9870:9870 -p 8088:8088 -p 7077:7077 -p 16010:16010 --name hadoop-master --hostname hadoop-master liliasfaxi/spark-hadoop:hv-2.7.2
docker run -itd -p 8040:8042 --net=hadoop --name hadoop-slave1 --hostname hadoop-slave1 liliasfaxi/spark-hadoop:hv-2.7.2
docker run -itd -p 8041:8042 --net=hadoop --name hadoop-slave2 --hostname hadoop-slave2 liliasfaxi/spark-hadoop:hv-2.7.2
