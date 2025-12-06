FROM apache/airflow:2.9.1

USER root

# --- CORREÇÃO DE REDE (FORÇAR HTTPS) ---
# O seu firewall/rede está bloqueando HTTP (porta 80), mas aceita HTTPS (porta 443).
# Aqui apagamos a config antiga e criamos uma nova usando APENAS links HTTPS.
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && echo "deb https://deb.debian.org/debian bookworm main contrib non-free" > /etc/apt/sources.list \
    && echo "deb https://deb.debian.org/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb https://security.debian.org/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list
# ---------------------------------------

# Instalar Dependências (Agora via HTTPS)
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         openjdk-17-jre-headless \
         git \
         libpq-dev \
         procps \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt