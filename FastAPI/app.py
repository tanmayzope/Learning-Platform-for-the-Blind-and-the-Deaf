# FastAPI Backend Code
from fastapi import Body
from fastapi import FastAPI, HTTPException,Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from transformers import MBartForConditionalGeneration, MBart50Tokenizer
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
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

 
 
DBURL = "sqlite:///./test.db"

Base = declarative_base()

engine1 = create_engine(DBURL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine1)
 
# Dependency

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()
 
# Security and password context setup

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
# Your secret key and algorithm

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Replace with a secure key
ALGORITHM = "HS256"
 
# SQLAlchemy ORM models

class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, index=True)

    hashed_password = Column(String)
 
# Pydantic models for request and response

class UserRegister(BaseModel):

    username: str

    password: str
 
# Create the database tables

Base.metadata.create_all(bind=engine1)
 
# Utility functions

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
 
def get_user(db, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict):
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
 
# Routes

@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already registered")
    access_token = create_access_token(data={"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer"}
 
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/translate/")
async def translate(text: str):
    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload)
    print(response)
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

    # Return quiz data
    return tt

@app.get("/")
def read_root():
    return {"Hello": "FastAPI"}

def main():
    import uvicorn
    uvicorn.run("main:app", port=8504)

if __name__ == "__main__":
    main()

