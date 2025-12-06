import sys
import os
from pyspark.sql.functions import col, current_timestamp

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
            zones_df = self.spark_session.read.option("header", "true").option("inferSchema", "true").csv(zones_path)
            
            self.logger.info(f"Leitura concluída. Viagens: {trips_df.count()} linhas.")
            return trips_df, zones_df
        except Exception as e:
            self.logger.error(f"Erro ao ler Bronze: {e}")
            raise

    def transform_data(self, trips_df, zones_df):
        """Aplica transformações, joins e limpeza."""
        self.logger.info("Iniciando transformação (Bronze -> Silver)...")
        
        # Join para adicionar informações de Pickup (Origem)
        trips_with_pickup = trips_df.join(
            zones_df.withColumnRenamed("LocationID", "PULocationID_join"),
            trips_df.PULocationID == col("PULocationID_join"),
            "left"
        ).withColumnRenamed("Borough", "pickup_borough") \
         .withColumnRenamed("Zone", "pickup_zone") \
         .withColumnRenamed("service_zone", "pickup_service_zone") \
         .drop("PULocationID_join")

        # Join para adicionar informações de Dropoff (Destino)
        transformed_df = trips_with_pickup.join(
            zones_df.withColumnRenamed("LocationID", "DOLocationID_join"),
            trips_with_pickup.DOLocationID == col("DOLocationID_join"),
            "left"
        ).withColumnRenamed("Borough", "dropoff_borough") \
         .withColumnRenamed("Zone", "dropoff_zone") \
         .withColumnRenamed("service_zone", "dropoff_service_zone") \
         .drop("DOLocationID_join")
        
        # Timestamp de processamento
        final_df = transformed_df.withColumn("processing_ts", current_timestamp())
        
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