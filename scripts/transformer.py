import sys
import os
from pathlib import Path
from pyspark.sql.functions import col, current_timestamp, broadcast, to_timestamp, year, month
from pyspark.sql.types import TimestampType
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

try:
    from utils.logger import Logger
    from utils.spark_session import SparkSessionBuilder
    logger = Logger.setup_logger("Transformer_NYC_Taxi")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Transformer_NYC_Taxi")

class Transformer():
    """
    Lê dados da camada bronze, transforma com Spark e salva na camada silver (Postgres).
    """
    def __init__(self):
        self.bucket_name = "ingestion-data-lake" # Confirme se o bucket no MinIO é 'landing' ou 'ingestion-data-lake'
        self.spark_session = SparkSessionBuilder.get_spark_session("Transformer_NYC_Taxi")
        self.logger = logger
        
        # Detalhes da conexão com o Postgres
        self.postgres_db = os.getenv("POSTGRES_DB", "nyc_taxi_db") 
        self.postgres_user = os.getenv("POSTGRES_USER", "post_aiflow")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "airflow_123")
        self.postgres_host = os.getenv("POSTGRES_HOST", "postgres-airflow") 
        self.postgres_port = os.getenv("POSTGRES_PORT", "5432")
        
        self.postgres_url = f"jdbc:postgresql://{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        self.postgres_properties = {
            "user": self.postgres_user,
            "password": self.postgres_password,
            "driver": "org.postgresql.Driver"
        }

    def read_bronze_data(self, year="2024", month="01"):
        """Lê os dados de viagens e zonas da camada bronze."""
        self.logger.info(f"Iniciando leitura da camada bronze para {year}-{month}...")
        
        trips_path = f"s3a://{self.bucket_name}/bronze/nyc_taxi/trips/{year}/{month}/"
        zones_path = f"s3a://{self.bucket_name}/bronze/nyc_taxi/zones/taxi_zone_lookup.csv"
        
        try:
            trips_df = self.spark_session.read.parquet(trips_path)
            # InferSchema=True no CSV é importante para pegar inteiros corretamente
            # Adiciona charset UTF-8 explicitamente e ignora espaços em branco
            zones_df = self.spark_session.read \
                .option("header", "true") \
                .option("inferSchema", "true") \
                .option("encoding", "UTF-8") \
                .option("ignoreLeadingWhiteSpace", "true") \
                .option("ignoreTrailingWhiteSpace", "true") \
                .csv(zones_path)

            self.logger.info(f"Leitura concluída. Viagens: {trips_df.count()} linhas.")
            self.logger.info(f"Zonas - Colunas: {zones_df.columns}")
            return trips_df, zones_df
        except Exception as e:
            self.logger.error(f"Erro ao ler Bronze: {e}")
            raise

    def transform_data(self, trips_df, zones_df):
        """
        Aplica limpeza, normalização e enriquecimento (Joins).
        Transforma dados Bronze (Raw) em Silver (Refined).
        """
        self.logger.info("Iniciando transformações de negócio...")

        # 1. LIMPEZA E TIPAGEM (Data Quality)
        # Garante que timestamps são do tipo correto e remove dados inválidos
        clean_df = trips_df \
            .withColumn("tpep_pickup_datetime", to_timestamp(col("tpep_pickup_datetime"))) \
            .withColumn("tpep_dropoff_datetime", to_timestamp(col("tpep_dropoff_datetime"))) \
            .filter(
                (col("trip_distance") > 0) & 
                (col("total_amount") > 0)
            )

        # 2. PREPARAÇÃO DAS ZONAS (Evitar ambiguidade de colunas)
        # Selecionamos apenas o necessário e renomeamos antes do join
        zones_pu = zones_df.select(
            col("LocationID").alias("pu_loc_id"),
            col("Borough").alias("pickup_borough"),
            col("Zone").alias("pickup_zone"),
            col("service_zone").alias("pickup_service_zone")
        )

        zones_do = zones_df.select(
            col("LocationID").alias("do_loc_id"),
            col("Borough").alias("dropoff_borough"),
            col("Zone").alias("dropoff_zone"),
            col("service_zone").alias("dropoff_service_zone")
        )

        # 3. JOINS COM BROADCAST (Enriquecimento)
        
        # Join Pickup
        df_joined_pu = clean_df.join(
            broadcast(zones_pu),
            clean_df.PULocationID == zones_pu.pu_loc_id,
            "left"
        ).drop("pu_loc_id") # Remove a chave duplicada do join

        # Join Dropoff (usando o resultado do anterior)
        final_df = df_joined_pu.join(
            broadcast(zones_do),
            df_joined_pu.DOLocationID == zones_do.do_loc_id,
            "left"
        ).drop("do_loc_id")

        # 4. METADADOS E PARTICIONAMENTO
        # Adiciona timestamp de processamento e colunas auxiliares para partição
        final_df = final_df \
            .withColumn("processing_ts", current_timestamp()) \
            .withColumn("partition_year", year(col("tpep_pickup_datetime"))) \
            .withColumn("partition_month", month(col("tpep_pickup_datetime")))

        self.logger.info(f"Transformação concluída. Linhas resultantes: {final_df.count()}")
        
        return final_df

    def write_silver_data(self, df, table_name="public.nyc_trips_silver"):
        """Escreve o DataFrame transformado no Postgres."""
        self.logger.info(f"Escrevendo na camada Silver (Tabela: {table_name})...")
        
        try:
            df.write.jdbc(
                url=self.postgres_url,
                table=table_name,
                mode="overwrite", 
                properties=self.postgres_properties
            )
            self.logger.info("Escrita na camada Silver concluída com sucesso.")
        except Exception as e:
            self.logger.error(f"Falha ao escrever no Postgres: {e}")
            raise

    def run(self, year: str, month: str):
        """Orquestra o pipeline."""
        try:
            trips_df, zones_df = self.read_bronze_data(year, month)
            transformed_df = self.transform_data(trips_df, zones_df)
            self.write_silver_data(transformed_df)
        except Exception as e:
            self.logger.error(f"Erro Crítico no Pipeline: {e}")
            sys.exit(1)
        finally:
            self.spark_session.stop()

if __name__ == "__main__":
    import argparse
    
    # Configura argumentos via linha de comando (Excelente para o Airflow)
    parser = argparse.ArgumentParser(description="ETL Bronze -> Silver NYC Taxi")
    parser.add_argument("--year", default="2024", help="Ano (YYYY)")
    parser.add_argument("--month", default="01", help="Mês (MM)")
    
    args = parser.parse_args()

    transformer = Transformer()
    transformer.run(year=args.year, month=args.month)