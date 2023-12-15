from datetime import timedelta
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator
import speech_recognition as sr
from pytube import YouTube, Playlist
import os
import tempfile
from pydub import AudioSegment
from pydub.silence import split_on_silence
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

DB_URL = os.getenv("DB_URL", "postgresql://root:root@db:5432/youtube")

# DAG Configuration
dag = DAG(
    dag_id="playlist_transcription",
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

def download_audio_from_youtube(url):
    output_path = tempfile.gettempdir()
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_stream.download(output_path=output_path)
    return os.path.join(output_path, audio_stream.default_filename)

    

def download_and_transcribe(playlist_url):
    playlist = Playlist(playlist_url)
    count = 1
    for video_url in playlist.video_urls[1:6]:

        
        vid_url = str(playlist.video_urls[count])  # Return the first video URL
        
        yt = YouTube(video_url) #URL
        video_title = yt.title  # Title of the video
        yt = str(yt)

        audio_path = download_audio_from_youtube(video_url)
        transcription = get_large_audio_transcription_on_silence(audio_path)

        #Insert Data in Postgre SQL
        data = {
        'url': [vid_url],
        'video_title': [video_title],
        'transcribed_text': [transcription]
        }

        current_time = datetime.now()
        data['timestamp'] = current_time

        df = pd.DataFrame(data)

        engine = create_engine(DB_URL)
        engine.connect()
        len(transcription)

        df.to_sql(name='youtube', con=engine, index=False, if_exists='append')

        # Retrieve the inserted data from the database
        query = "SELECT transcribed_text FROM youtube WHERE url = %s AND timestamp = %s"
        retrieved_data = pd.read_sql_query(query, engine, params=(yt, current_time))

        # Assuming that each URL and timestamp combination is unique
        if not retrieved_data.empty:
            retrieved_text = retrieved_data['transcribed_text'].iloc[0]    
            assert len(transcription) == len(retrieved_text)
        else:
            print("No data retrieved from the database.")

        count += 1

        os.remove(audio_path)

    return len(transcription)

def download_and_transcribe_wrapper(playlist_url):
    return download_and_transcribe(playlist_url)

playlist_urls = [
    'https://www.youtube.com/watch?v=1WjfkyL6OhA&list=PLiONnRuKRuJCo4H5VoQLNanQtDNDjcrNi&index=1',
    'https://www.youtube.com/watch?v=lLeFVA6rFX8&list=PLJqiHnBNjacq6AAH3EHWhvGL6yak7usXz&index=1',
    'https://www.youtube.com/watch?v=pwwVOpXrazs&list=PL4g1oAdmuCfqmYvURLzVFkMMUI7839biN&index=1',
    'https://www.youtube.com/watch?v=DjFz-LC0Et4&list=PLiC1doDIe9rDjk9tSOIUZJU4s5NpEyYtE&index=1'
]

# Task to transcribe a single video
for i, playlist_url in enumerate(playlist_urls):
    task = PythonOperator(
        task_id=f'transcribe_playlist_{i+1}',
        python_callable=download_and_transcribe_wrapper,
        op_kwargs={'playlist_url': playlist_url},
        dag=dag
    )

task