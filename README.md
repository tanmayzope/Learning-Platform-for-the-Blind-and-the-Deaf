# Big_Data_Final_Project: AllAccessEd

#### [Codelabs Document](https://codelabs-preview.appspot.com/?file_id=1FdCYFk82QYMPheCuaJK0NwihoGXUnLx4QDOUzCcPWcM#0)
#### [YouTube Video](https://youtu.be/34sq0Lbhi_g)

#### Application link : 

## Introduction

The Accessible Learning Platform is a dedicated initiative focused on enhancing inclusivity and accessibility within the realm of online education. Our primary objective is to create an inclusive space for language learners and individuals with visual or auditory impairments. Leveraging cutting-edge technologies, including Natural Language Processing (NLP), FastAPI, and PostgreSQL, our platform efficiently integrates with YouTube links. It facilitates audio transcription, quiz generation, and delivers interactive learning experiences tailored for the deaf and blind communities.

## Overview

The goal of this project is to develop a comprehensive platform that enhances accessibility for video content sourced from YouTube. The platform will cater to users with varying needs, including the deaf, blind, and those who prefer content in different languages.

### Feature list:
#### Audio Transcription and Quiz Generation
* Transcription of audio from videos to text.
* Automatic generation of quizzes for enhanced engagement and learning.
* Summerization

#### Accessibility for the Deaf
* Interactive transcripts for improved understanding.
* Translation of content into multiple languages, including Hindi.

### Accessibility for the Blind
* Conversion of quizzes into audio playlists for seamless consumption.

## Tech Stack

FastAPI | PosgreSQL| Airflow | Streamlit | GCP | Docker

## For environment variables

* Create an .env file on the root folder after cloning
* The format of the env file is:
```
AIRFLOW_UID=
AIRFLOW_PROJ_DIR=
OPENAI_KEY= API Keys from Open AI
FASTAPI_ENDPOINT= 
DATABASE_URL= (pg admin local URL)
API_TOKEN= (Hugging Face API for translation into hindi Token from - https://huggingface.co/damerajee/hindi-english)
```

## Setup Instructions

* Just initiate docker settings and open terminal under this cloned folder
* Make sure you have the above mentioned .env file ready
* Run - docker compose up -d --build

## Application Components

* User Registration & User Login 
* Choosing from transcribed Videos
* Summarization
* Generating quizzes
* Generating Audio Playlist


### Data Sourcing
YouTube video links serve as the primary data source
### Data Staging
Data Staging is done using PostgreSQL
### Data Processing
* Downloading audio from Youtube
* Transcribing Audio
* Fetching text from audio
### Data Service
FAST API endpoints:
* /translate/: Accepts a POST request with text and translates it using the Hugging Face translation API.
* /get_data/: Retrieves video data (URL and title) from a PostgreSQL database.
* /get_transcribed_text/: Retrieves transcribed text for a given video URL from the database.
* /get_summary/: Summarizes the transcribed text using OpenAI's GPT-3 summarization model.
* /get_quizzes/: Generates quiz questions based on the transcribed text and returns them as structured data.
* /questions_audio/{url} and /answers_audio/{url}: Returns audio files for quiz questions and answers, respectively.
## Aditional Notes

WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR PROJECT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK


