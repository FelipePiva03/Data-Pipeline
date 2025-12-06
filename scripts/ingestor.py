import requests
import boto3
import os
from botocore.exceptions import ClientError

try:
    from utils.logger import Logger
    # Chamamos o método estático da classe
    logger = Logger.setup_logger("Ingestor_NYC_Taxi")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Ingestor_NYC_Taxi")


class Ingestor():
    """
    Classe responsável pela ingestão de dados do NYC Taxi (Yellow) e Zonas.
    Baixa da web e salva no Data Lake (MinIO).
    """

    def __init__(self):

        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.endpoint = os.getenv("MINIO_ENDPOINT")
        self.bucket_name = "ingestion-data-lake"

        self.s3_client = self._get_minio_client()
        self._ensure_bucket_exists()
    
    def _get_minio_client(self):
        """
        Configura o cliente MinIO usando boto3.
        """
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )
    
    def _ensure_bucket_exists(self):
        """Verifica se o bucket existe e cria se necessário."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' já existe.")
        except ClientError:
            logger.info(f"Bucket '{self.bucket_name}' não encontrado. Criando...")
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info("Bucket criado com sucesso.")
            except Exception as e:
                logger.error(f"Falha crítica ao criar bucket: {e}")
                raise

    def download_and_upload(self, url, s3_path):
        """
        Baixa o arquivo da URL via stream e envia para o MinIO sem carregar tudo na RAM.
        """
        logger.info(f"Iniciando download de: {url}")
        
        try:
            # stream=True é essencial para arquivos grandes (Parquet)
            with requests.get(url, stream=True) as response:
                response.raise_for_status() # Lança erro se a URL estiver quebrada (404, 500)
                
                logger.info(f"Enviando para MinIO em: {s3_path}")
                self.s3_client.upload_fileobj(
                    response.raw, 
                    self.bucket_name, 
                    s3_path
                )
                logger.info(f"Upload concluído: s3://{self.bucket_name}/{s3_path}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão ao baixar arquivo: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado no upload: {e}")
            raise

    def run(self, year: str, month: str):
        """Método principal que orquestra a execução da ingestão."""
        
        # 1. Ingestão do Arquivo de Viagens (Parquet)
        trip_filename = f"yellow_tripdata_{year}-{month}.parquet"
        trip_url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{trip_filename}"
        
        # Caminho organizado: bronze/tipo/ano/mes/arquivo
        trip_s3_path = f"bronze/nyc_taxi/trips/{year}/{month}/{trip_filename}"
        
        self.download_and_upload(trip_url, trip_s3_path)

        # 2. Ingestão da Tabela de Zonas (CSV) - Necessário para saber os bairros
        zone_url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
        zone_s3_path = "bronze/nyc_taxi/zones/taxi_zone_lookup.csv"
        
        self.download_and_upload(zone_url, zone_s3_path)

# Bloco para execução manual (Debug)
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingestor de dados do NYC Taxi para o Data Lake.")
    parser.add_argument("--year", required=True, help="Ano dos dados a serem ingeridos (ex: 2024).")
    parser.add_argument("--month", required=True, help="Mês dos dados a serem ingeridos (ex: 01).")
    
    args = parser.parse_args()
    
    ingestor = Ingestor()
    ingestor.run(year=args.year, month=args.month)
    
