#!/bin/bash

# Script para baixar os JARs necessários para o Spark
# Execute este script a partir do diretório spark-jars/

set -e

echo "🚀 Baixando JARs necessários para o Spark..."
echo ""

# PostgreSQL JDBC Driver
if [ ! -f "postgresql-42.6.0.jar" ]; then
    echo "📥 Baixando PostgreSQL JDBC Driver..."
    wget -q --show-progress https://jdbc.postgresql.org/download/postgresql-42.6.0.jar
    echo "✅ PostgreSQL JDBC Driver baixado"
else
    echo "✅ PostgreSQL JDBC Driver já existe"
fi

echo ""

# Hadoop AWS
if [ ! -f "hadoop-aws-3.4.1.jar" ]; then
    echo "📥 Baixando Hadoop AWS..."
    wget -q --show-progress https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.1/hadoop-aws-3.4.1.jar
    echo "✅ Hadoop AWS baixado"
else
    echo "✅ Hadoop AWS já existe"
fi

echo ""

# AWS SDK Bundle v1
if [ ! -f "aws-java-sdk-bundle-1.12.772.jar" ]; then
    echo "📥 Baixando AWS SDK Bundle v1 (370MB - pode demorar)..."
    wget -q --show-progress https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.772/aws-java-sdk-bundle-1.12.772.jar
    echo "✅ AWS SDK Bundle v1 baixado"
else
    echo "✅ AWS SDK Bundle v1 já existe"
fi

echo ""
echo "🎉 Todos os JARs foram baixados com sucesso!"
echo ""
echo "📋 Arquivos no diretório:"
ls -lh *.jar 2>/dev/null || echo "Nenhum JAR encontrado"
echo ""
echo "✅ Você pode iniciar os containers agora: docker compose up -d"