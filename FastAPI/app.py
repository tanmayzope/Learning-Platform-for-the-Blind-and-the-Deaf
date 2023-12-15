# FastAPI Backend Code

from fastapi import FastAPI, HTTPException, FileResponse
from transformers import MBartForConditionalGeneration, MBart50Tokenizer
import asyncio
from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv
import openai
import requests

app = FastAPI()

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)
OPENAI_KEY = os.getenv('OPENAI_KEY')
API_TOKEN = os.getenv('API_TOKEN')
API_URL = "https://api-inference.huggingface.co/models/damerajee/hindi-english"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

# async def load_model():
#     global model, tokenizer
#     model_name = "facebook/mbart-large-50-many-to-many-mmt"
#     model = MBartForConditionalGeneration.from_pretrained(model_name)
#     tokenizer = MBart50Tokenizer.from_pretrained(model_name)

# @app.on_event("startup")
# async def startup_event():
#     loop = asyncio.get_event_loop()
#     loop.create_task(load_model())

# def translate_to_hindi(text: str):
#     # Ensure that the model and tokenizer are global
#     global model, tokenizer
#     tokenizer.src_lang = "en_XX"  # Set source language to English
#     encoded_english_text = tokenizer(text, return_tensors="pt")
#     generated_tokens = model.generate(**encoded_english_text, forced_bos_token_id=tokenizer.lang_code_to_id["hi_IN"])
#     out = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
#     return out[0]

@app.post("/translate/")
async def translate(text: str):
    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    # else:
    #     raise HTTPException(status_code=500, detail="Translation failed.")

@app.get("/get_data/")
async def get_data():
    query = "SELECT url, video_title FROM youtube"
    try:
        data = pd.read_sql_query(query, engine)
        return data.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_transcribed_text/")
async def get_transcribed_text(url: str):
    query = f"SELECT transcribed_text FROM youtube WHERE url = '{url}'"
    try:
        data = pd.read_sql_query(query, engine)
        if not data.empty:
            # Return only the content of 'transcribed_text' from the first record
            return data['transcribed_text'].iloc[0]
        else:
            return "No transcribed text found for the provided URL."
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def summarize_transcription(transcription, max_tokens=250):

    openai.api_key = OPENAI_KEY

    response = openai.Completion.create(
        engine="text-davinci-003",  # or any other suitable model
        prompt= "Please summarize the transcription provided, emphasizing important details and insights. Highlight information that could be particularly informative or valuable for a deeper understanding of the subject matter discussed in the text." + transcription,
        max_tokens=max_tokens
    )
    return response.choices[0].text.strip()

@app.get("/get_summary/")
async def get_summary(url: str):
    query = f"SELECT transcribed_text FROM youtube WHERE url = '{url}'"
    try:
        data = pd.read_sql_query(query, engine)
        if not data.empty:
            # Return only the content of 'transcribed_text' from the first record 
            testtext = summarize_transcription(data['transcribed_text'].iloc[0])
            return testtext
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # Placeholder for text summarization logic
    # Implement the logic to return text summarization based on the transcribed text
    pass

def generate_quiz_questions(context, difficulty):
    openai.api_key = OPENAI_KEY
    questions = 5
    formatted_prompt = f"""Always create {questions} advanced, master's level standard multiple choice quiz questions based on the following {difficulty} text. Each question should:
 
                        1. Challenge deep understanding and critical analysis of the text.
                        2. Include 4 well-crafted options (labeled A to D), with one correct answer and three plausible but incorrect alternatives that encourage critical thinking.
                        3. Reflect high academic standards in both content and formulation.
                        4. Provide a brief explanation for the correct answer, highlighting key concepts or reasoning.
 
                        Format all the questions exactly in the below manner:
                        Q1: What is the primary purpose of an object store in the Mule runtime?
                        A. To act as a general replacement for a database
                        B. To store data about customers
                        C. To segment data into different chunks
                        D. To store snippets of values for tracking purposes
                        Correct Answer: D. To store snippets of values for tracking purposes.
                        Explanation: The object store in the Mule runtime is designed to store small snippets of values for the purpose of tracking, as opposed to replacing a database for storing large data sets. It is not transactional and instead operates as a key-value pair structure.
 
                        Context for questions:\n\n{context}\n\n"""


    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=formatted_prompt,
        max_tokens=250 * questions
    )
    return response.choices[0].text.strip()

def parse_quiz_questions(quiz_text):
    quiz_data = []

    for lines in quiz_text.split("\n\n"):
      qb = lines.split("\n")[0:5]
      ans = lines.split("\n")[5:]
      # if len(lines) > 2:   # Skip incomplete question blocks
      question = qb[0].split(":", 1)[1].strip()
      options = qb[1:5]
      options = [option.strip() for option in options]
      # else:
      correct_answer = ans[0].split(":", 1)[1].strip()
      explanation = ans[1].split(":", 1)[1].strip()
      quiz_data.append({"question": question, "options": options, "correct_answer": correct_answer, "explanation": explanation})
 
    return quiz_data

@app.get("/get_quizzes/")
async def get_quizzes(url: str):
    # Fetch the context (transcribed text) based on URL
    
    query = f"SELECT transcribed_text FROM youtube WHERE url = '{url}'"
    try:
        data = pd.read_sql_query(query, engine)
        if not data.empty:
            # Return only the content of 'transcribed_text' from the first record 
            context = data['transcribed_text'].iloc[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Generate quiz questions
    difficulty = "easy"  # Adjust as needed
    #number_of_questions = 5  # Adjust as needed
    quiz_text = generate_quiz_questions(context, difficulty)
    print(f"quiz_text:{quiz_text}")
    tt = parse_quiz_questions(quiz_text)
    print(f"TT:{tt}")

    # Generate audio files
    questions_audio_filename = f"questions_{url}.mp3"
    answers_audio_filename = f"answers_{url}.mp3"
    speak(get_summarized_question(tt), questions_audio_filename)
    speak(get_summarized_answers(tt), answers_audio_filename)

    # Return quiz data
    return tt
   

@app.get("/questions_audio/{url}")
async def get_questions_audio(url: str):
    return FileResponse(f"questions_{url}.mp3")

@app.get("/answers_audio/{url}")
async def get_answers_audio(url: str):
    return FileResponse(f"answers_{url}.mp3")


from gtts import gTTS
import os


def speak(text,filename, lang='en'):
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    os.system(f"start {filename}")  # This will play the audio file

def get_summarized_question(quiz_data):
  summarized_question = ""
  for index, quiz in enumerate(quiz_data):
    summarized_question += f"Question Number {index + 1}: {quiz['question']}.\n Options are:\n"
    for option in quiz['options']:
      summarized_question += f"Option : {option}\n"

  return summarized_question

def get_summarized_answers(quiz_data):
  summarized_answers = ""
  for index,answer in enumerate(quiz_data):
    summarized_answers += f"For Question{index + 1}: the Correct Answer is Option {answer['correct_answer']}.\n and the explanation behind this is {answer['explanation']}"

  return summarized_answers


@app.get("/")
def read_root():
    return {"Hello": "FastAPI"}

def main():
    import uvicorn
    uvicorn.run("main:app", port=8504)

if __name__ == "__main__":
    main()

