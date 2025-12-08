# Spark JARs

Este diretório contém os JARs necessários para o Apache Spark se conectar ao PostgreSQL e MinIO (S3).

## ⚠️ Os JARs não estão no repositório

Devido ao tamanho dos arquivos (>100MB), os JARs não estão incluídos no repositório Git.

## 📥 Como Obter os JARs

### Opção 1: Download Automático (Recomendado)

Execute o script de download que baixará todos os JARs necessários:

```bash
# A partir da raiz do projeto
cd spark-jars
chmod +x download_jars.sh
./download_jars.sh
```

### Opção 2: Download Manual

Baixe os seguintes JARs do Maven Central e coloque-os neste diretório:

#### PostgreSQL JDBC Driver
```bash
wget https://jdbc.postgresql.org/download/postgresql-42.6.0.jar
```

#### Hadoop AWS (para MinIO/S3)
```bash
wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.1/hadoop-aws-3.4.1.jar
```

#### AWS SDK Bundle
```bash
wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.772/aws-java-sdk-bundle-1.12.772.jar
```

#### SDK Bundle v2 (opcional, para features mais recentes)
```bash
wget https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.24.6/bundle-2.24.6.jar
```

## 📋 Lista de JARs Necessários

| JAR | Versão | Tamanho | Propósito |
|-----|--------|---------|-----------|
| `postgresql-42.6.0.jar` | 42.6.0 | ~1MB | Driver JDBC PostgreSQL |
| `hadoop-aws-3.4.1.jar` | 3.4.1 | ~500KB | Suporte Hadoop para S3 |
| `aws-java-sdk-bundle-1.12.772.jar` | 1.12.772 | ~370MB | AWS SDK v1 (completo) |
| `bundle-2.24.6.jar` | 2.24.6 | ~532MB | AWS SDK v2 (opcional) |

## 🔍 Verificar JARs

Após o download, verifique se todos os JARs estão presentes:

```bash
ls -lh spark-jars/
```

Você deve ver os arquivos listados acima.

## 🐳 Docker

Quando você executa `docker compose up`, o Docker montará esta pasta dentro do container do Airflow em `/opt/airflow/spark-jars`. O Spark irá carregar automaticamente esses JARs.

## ⚠️ Troubleshooting

### Erro: "ClassNotFoundException: org.postgresql.Driver"
**Causa**: JAR do PostgreSQL não foi encontrado
**Solução**: Baixe o `postgresql-42.6.0.jar`

### Erro: "java.lang.NoClassDefFoundError: com/amazonaws/..."
**Causa**: AWS SDK Bundle não foi encontrado
**Solução**: Baixe o `aws-java-sdk-bundle-1.12.772.jar`

### Erro: "No FileSystem for scheme: s3a"
**Causa**: hadoop-aws JAR não foi encontrado
**Solução**: Baixe o `hadoop-aws-3.4.1.jar`

## 🔗 Links Úteis

- [PostgreSQL JDBC Driver](https://jdbc.postgresql.org/download/)
- [Maven Central - Hadoop AWS](https://mvnrepository.com/artifact/org.apache.hadoop/hadoop-aws)
- [Maven Central - AWS SDK Bundle](https://mvnrepository.com/artifact/com.amazonaws/aws-java-sdk-bundle)