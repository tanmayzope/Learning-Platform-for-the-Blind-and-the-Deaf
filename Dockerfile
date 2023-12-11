FROM apache/airflow:latest  

USER root

# Install FFmpeg and FLAC
RUN apt-get update && \
    apt-get install -y ffmpeg flac && \
    rm -rf /var/lib/apt/lists/*

# Uncomment these if you want to use Pipenv
# Install Pipenv
# RUN pip install pipenv

# Copy Pipenv files
# COPY ./Airflow/Pipfile ./Airflow/Pipfile.lock /opt/airflow/

# Install Pipenv dependencies
# RUN cd /opt/airflow && pipenv install --deploy --ignore-pipfile

USER airflow
