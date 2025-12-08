FROM apache/airflow:2.9.1

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
           openjdk-17-jre-headless \
           git \
           libpq-dev \
           procps \
    && ln -s /usr/lib/jvm/java-17-openjdk-* /usr/lib/jvm/java-17-openjdk \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Define JAVA_HOME apontando para o Java 17
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt