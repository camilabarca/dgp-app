FROM python:3.7-slim

RUN apt-get update && apt-get install --no-install-recommends -y gcc libc6-dev linux-libc-dev libpq-dev && \
    adduser --disabled-password --home /app etl && update-ca-certificates && \
    pip install --upgrade gunicorn numpy 'pandas<1.0.0' dgp-server pyproj && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ADD requirements.txt .
RUN pip install -r requirements.txt

# TODO: Remove VV
RUN apt-get update && apt-get install --no-install-recommends -y postgresql-client sudo
RUN echo "etl ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

ADD . .
RUN pip install -e .
RUN pip install https://github.com/frictionlessdata/tabulator-py/archive/fix/full-html-table-support.zip
RUN pip install https://github.com/frictionlessdata/tableschema-py/archive/fix/281.zip
# RUN pip install -U -e deps/dgp-server

ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV AIRFLOW__CORE__DAGS_FOLDER=/app/dags
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False

RUN mkdir /var/dgp && chown -R etl:etl /var/ && chown -R etl:etl .

EXPOSE 5000
USER etl

ENTRYPOINT [ "/app/entrypoint.sh" ]