from datetime import timedelta
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator
import speech_recognition as sr
from pytube import YouTube
import os
import tempfile
from pydub import AudioSegment
from pydub.silence import split_on_silence

dag = DAG(
    dag_id="playlist1",
    schedule_interval="0 0 * * *",
    start_date=days_ago(0),
    catchup=False,
    dagrun_timeout=timedelta(minutes=60),
    tags=["bigdata", "damg7245"]
)

def transcribe_audio(path):
    r = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio_listened = r.record(source)
        try:
            text = r.recognize_google(audio_listened)
            return text
        except sr.UnknownValueError as e:
            return "Error: " + str(e)
        except sr.RequestError as e:
            return "API Error: " + str(e)

def get_large_audio_transcription_on_silence(path):
    sound = AudioSegment.from_file(path)
    chunks = split_on_silence(sound, min_silence_len=500, silence_thresh=sound.dBFS-14, keep_silence=500)

    folder_name = tempfile.mkdtemp()
    whole_text = ""
    for i, audio_chunk in enumerate(chunks, start=1):
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")
        text = transcribe_audio(chunk_filename)
        if not text.startswith("Error"):
            text = f"{text.capitalize()}. "
            whole_text += text

    # Clean up
    for file in os.listdir(folder_name):
        os.remove(os.path.join(folder_name, file))
    os.rmdir(folder_name)

    return whole_text

def download_and_transcribe(url):
    output_path = tempfile.gettempdir()
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_stream.download(output_path=output_path)
    audio_file = os.path.join(output_path, audio_stream.default_filename)

    transcribed_text = get_large_audio_transcription_on_silence(audio_file)

    # Log the transcribed text
    print(transcribed_text)

    return transcribed_text


# Task to transcribe a single video
transcribe_task = PythonOperator(
    task_id='transcribe_video',
    python_callable=download_and_transcribe,
    op_kwargs={'url': 'https://www.youtube.com/watch?v=gI-qXk7XojA'},
    dag=dag
)

transcribe_task