import os
from pathlib import Path
from pyspark.sql import SparkSession
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class SparkSessionBuilder:
    @staticmethod
    def get_spark_session(app_name: str = "DefaultApp") -> SparkSession:

        # Use local JARs instead of downloading from Maven
        jars_path = "/opt/airflow/spark-jars"
        jars = [
            f"{jars_path}/hadoop-aws-3.3.4.jar",
            f"{jars_path}/aws-java-sdk-bundle-1.12.262.jar",
            f"{jars_path}/postgresql-42.6.0.jar"
        ]

        return (SparkSession.builder
            .appName(app_name)
            .config("spark.jars", ",".join(jars))
            # S3A Endpoint and Credentials
            .config("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_ENDPOINT"))
            .config("spark.hadoop.fs.s3a.access.key", os.getenv("AWS_ACCESS_KEY_ID"))
            .config("spark.hadoop.fs.s3a.secret.key", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
            .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
            # Connection and timeout configurations (numeric milliseconds ONLY)
            .config("spark.hadoop.fs.s3a.connection.timeout", "300000")
            .config("spark.hadoop.fs.s3a.connection.establish.timeout", "60000")
            .config("spark.hadoop.fs.s3a.attempts.maximum", "10")
            .config("spark.hadoop.fs.s3a.retry.interval", "500")
            .config("spark.hadoop.fs.s3a.retry.limit", "5")
            # Threadpool configurations - CRITICAL to override "60s" defaults
            .config("spark.hadoop.fs.s3a.threads.max", "10")
            .config("spark.hadoop.fs.s3a.threads.core", "5")
            .config("spark.hadoop.fs.s3a.threads.keepalivetime", "60000")
            .config("spark.hadoop.fs.s3a.max.total.tasks", "10")
            # Socket timeout
            .config("spark.hadoop.fs.s3a.socket.recv.buffer", "65536")
            .config("spark.hadoop.fs.s3a.socket.send.buffer", "65536")
            # Multipart upload configurations - override "24h" defaults
            .config("spark.hadoop.fs.s3a.multipart.size", "67108864")  # 64MB
            .config("spark.hadoop.fs.s3a.multipart.threshold", "134217728")  # 128MB
            .config("spark.hadoop.fs.s3a.multipart.purge", "false")
            .config("spark.hadoop.fs.s3a.multipart.purge.age", "86400000")  # 24h in milliseconds
            .getOrCreate())