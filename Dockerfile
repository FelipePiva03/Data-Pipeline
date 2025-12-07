FROM apache/airflow:2.9.1

USER root

# 1. Adicionar repositório do Debian 11 (Bullseye) APENAS para baixar o Java 11
# O Debian 12 (Bookworm) removeu o Java 11 nativo, então buscamos no anterior.
RUN echo "deb http://deb.debian.org/debian bullseye main" > /etc/apt/sources.list.d/bullseye.list

# 2. Atualizar e Instalar Java 11
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
           openjdk-11-jre-headless \
           git \
           libpq-dev \
           procps \
    # --- TRUQUE DE MESTRE ---
    # Cria link simbólico pegando qualquer arquitetura (arm64 ou amd64)
    && ln -s /usr/lib/jvm/java-11-openjdk-* /usr/lib/jvm/java-11-openjdk \
    # ------------------------
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Define JAVA_HOME apontando para o Java 11
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt