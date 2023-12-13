FROM apache/airflow:latest  

USER root

# Install FFmpeg and FLAC
RUN apt-get update && \
    apt-get install -y ffmpeg flac && \
    rm -rf /var/lib/apt/lists/*

USER airflow
