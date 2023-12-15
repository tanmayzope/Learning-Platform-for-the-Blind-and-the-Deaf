import streamlit as st
import requests
import os
from gtts import gTTS
import io


# Backend API URL
FASTAPI_ENDPOINT = os.getenv('FASTAPI_ENDPOINT')

# Function to fetch data from backend
def fetch_data(endpoint, params={}):
    response = requests.get(f"{FASTAPI_ENDPOINT}/{endpoint}", params=params)
    return response.json() if response.status_code == 200 else None

# JWT Authentication Function (from your provided template)
def jwt_auth():
    st.title("User Authentication")

    # Register User
    if st.button("Register a New User"):
        st.session_state['selected_option'] = "register"

    # Login User
    if st.button("Log in"):
        st.session_state['selected_option'] = "login"

    # Display the appropriate form based on the user's choice
    if st.session_state.get('selected_option') == "register":
        with st.form("Register Form"):
            reg_username = st.text_input("Choose a Username")
            reg_password = st.text_input("Choose a Password", type="password")
            submit_reg = st.form_submit_button("Register")

            if submit_reg:
                registration_data = {"username": reg_username, "password": reg_password}
                try:
                    response = requests.post(f"{FASTAPI_ENDPOINT}/register", json=registration_data)
                    if response.status_code == 200:
                        st.session_state['jwt_token'] = response.json().get('access_token')
                        st.session_state['logged_in'] = True
                        st.success("Successfully registered and logged in!")
                        st.session_state['selected_option'] = None
                    else:
                        st.error(response.json().get('detail', "Registration failed. Please try again."))
                except requests.exceptions.RequestException as e:
                    st.error(f"An error occurred while connecting to the server: {e}")

    elif st.session_state.get('selected_option') == "login":
        with st.form("Login Form"):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")

            if submit_login:
                login_data = {"username": login_username, "password": login_password}
                try:
                    response = requests.post(f"{FASTAPI_ENDPOINT}/token", data=login_data)
                    if response.status_code == 200:
                        st.session_state['jwt_token'] = response.json().get('access_token')
                        st.session_state['logged_in'] = True
                        st.success("Logged in successfully!")
                        st.session_state['selected_option'] = None
                    else:
                        st.error("Incorrect username or password. Please try again.")
                except requests.exceptions.RequestException as e:
                    st.error(f"An error occurred while connecting to the server: {e}")

    # Allow user to reset the choice and go back to the main menu
    if st.session_state.get('selected_option'):
        if st.button("Back"):
            st.session_state['selected_option'] = None

    if st.button("Log Out"):
        st.session_state['logged_in'] = False
        st.session_state['jwt_token'] = None
        st.info("You have successfully logged out.")

# Your existing functions for different pages
def main_page():
    st.title("YouTube Video Viewer")
    data = fetch_data("get_data")
    if data:
        video_options = [d['video_title'] for d in data]
        selected_title = st.selectbox("Select a Video:", options=video_options)

        if st.button("View Details"):
            selected_video = next((d for d in data if d['video_title'] == selected_title), None)
            if selected_video:
                st.session_state['selected_video'] = selected_video
                st.session_state['page'] = 'details'

        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.session_state['jwt_token'] = None
            st.info("You have successfully logged out.")

def details_page():
    st.title("Details - " + st.session_state['selected_video']['video_title'])
    if st.button("Back to Main Page"):
        st.session_state['page'] = 'main'
    elif st.button("Get Transcribed Text"):
        st.session_state['page'] = 'transcribed_text'
    elif st.button("Get Summary"):
        st.session_state['page'] = 'summary'
    elif st.button("Get Quizzes"):
        st.session_state['page'] = 'quizzes'

def transcribed_text_page():
    st.title("Transcribed Text")
    if st.button("Back"):
        st.session_state['page'] = 'details'
    else:
        url = st.session_state['selected_video']['url']
        transcribed_text = fetch_data("get_transcribed_text", {"url": url})
        if transcribed_text:
            st.write(transcribed_text)
            # Add a button to translate the text
            if st.button("Translate to Hindi"):
                translated_text = translate_text(transcribed_text)
                st.write(translated_text)

def summary_page():
    st.title("Summary")
    if st.button("Back"):
        st.session_state['page'] = 'details'
    else:
        url = st.session_state['selected_video']['url']
        summary = fetch_data("get_summary", {"url": url})
        if summary:
            st.write(summary)
            # Add a button to translate the text
            if st.button("Translate Summary to Hindi"):
                translated_summary = translate_text(summary)
                st.write(translated_summary)

def translate_text(text):
    response = requests.get(f"{FASTAPI_ENDPOINT}/translate", json={"text": text})
    return response.json()
    
    #if response.status_code == 200 else print(response.status_code)


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


def quizzes_page():
    st.title("Quizzes - " + st.session_state['selected_video']['video_title'])

    # Navigate back to the details page
    if st.button("Back"):
        st.session_state['page'] = 'details'
        return

    # Fetch the quiz questions once and store them in session state
    if 'quizzes' not in st.session_state or 'url' not in st.session_state or st.session_state['url'] != st.session_state['selected_video']['url']:
        st.session_state['quizzes'] = fetch_data("get_quizzes", {"url": st.session_state['selected_video']['url']})
        st.session_state['url'] = st.session_state['selected_video']['url']

    quizzes = st.session_state['quizzes']

    # Check if quizzes are available
    if quizzes:
        # Initialize a container to hold the users' answers
        answers = {}

        # Create a form for quiz submission
        with st.form(key='quiz_form'):
            # Iterate over quizzes to display questions and answer inputs
            for i, quiz in enumerate(quizzes):
                st.subheader(f"Question {i+1}: {quiz['question']}")
                # Display options
                st.text("Options:")
                for option in quiz['options']:
                    st.text(option)
                # Input for the answer
                answer = st.text_input(f"Enter your answer for Question {i+1} (A, B, C, or D):", key=f"answer_{i}")
                answers[i] = answer.upper()  # Store the answer in uppercase

            # Submit button for the form
            submit_button = st.form_submit_button(label='Submit Answers')

        # If the form has been submitted, validate the answers
        if submit_button:
            correct_answers = 0
            # Iterate over the quizzes and answers to validate
            for i, quiz in enumerate(quizzes):
                # Check if the answer is correct
                if answers[i] == quiz['correct_answer'][0]:
                    correct_answers += 1
                    st.success(f"Question {i+1}: Correct!")
                else:
                    st.error(f"Question {i+1}: Incorrect. Correct answer: {quiz['correct_answer']}. Explanation: {quiz['explanation']}")

            # Display the total score
            st.success(f"Your score is {correct_answers} out of {len(quizzes)}.")
    else:
        st.error("No quizzes available for this video.")

    tts = gTTS(text=get_summarized_question(st.session_state['quizzes']), lang='en')
    tta = gTTS(text=get_summarized_answers(st.session_state['quizzes']), lang='en')

    audio_buffer = io.BytesIO()
    audio_buffera = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    tta.write_to_fp(audio_buffera)
    audio_buffer.seek(0)
    audio_buffera.seek(0)

    st.audio(audio_buffer, format='audio/mpeg')
    st.audio(audio_buffera, format='audio/mpeg')

# Initialize session state for authentication and page navigation
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'page' not in st.session_state:
    st.session_state['page'] = 'main'

# Page routing with authentication check
if not st.session_state['logged_in']:
    jwt_auth()
else:
    if st.session_state['page'] == 'main':
        main_page()
    elif st.session_state['page'] == 'details':
        details_page()
    elif st.session_state['page'] == 'transcribed_text':
        transcribed_text_page()
    elif st.session_state['page'] == 'summary':
        summary_page()
    elif st.session_state['page'] == 'quizzes':
        quizzes_page()