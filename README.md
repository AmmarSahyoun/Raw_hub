
# Raw Hub - Fabric Airflow PoC

## Purpose

This project is a YAML-driven raw-data ingestion framework using Airflow and Microsoft Fabric.

The goal is to control and orchestrate data loading from different source systems using configuration files.
<img src="https://github.com/AmmarSahyoun/Raw_hub/blob/main/assets/raw_hub.png" alt="Draft diagram" width="450" height="300">

The main flow is:

```text
Source system
  → Extract notebook
  → Raw JSON landing
  → Flatten notebook
  → Parquet landing
  → Load notebook
  → Delta table in Fabric Lakehouse
```
  ### Architecture
 1. Local development is done with Airflow running in Docker Compose.
 ```Local PC
  → Docker Compose Airflow
  → Fabric DEV workspace: RAW_DEV
  → DEV Lakehouse tables
  ```
  2. Production, execution is done in Fabric Airflow.
```Fabric Airflow
  → Fabric notebooks
  → Fabric Prod workspace's Lakehouse : RAW
 ```
  ### Initializa and start Airflow 
  ```PS
    docker compose up airflow-init
    docker compose up -d

    docker compose ps
    docker compose down
  ```

  ### Build wheel
  ```PS
    python -m build
  ```
