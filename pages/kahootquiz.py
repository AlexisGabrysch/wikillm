import asyncio
import json
import websockets
import requests
import qrcode
import streamlit as st
from io import BytesIO
from PIL import Image
from src.db.utils import QuizDatabase
from pages.ressources.components import Navbar
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Kahoot‑Style Quiz", layout="wide")

# ------------------------------------------------------------------------------
# FONCTION PRINCIPALE
# ------------------------------------------------------------------------------
def kahoot_quiz():
    if st.button("Leave Room", key="leave_room"):
        for key in ["quiz_id", "quiz_started", "role", "connected", "answers_sent", "current_question_index"]:
            st.session_state.pop(key, None)
        st.rerun()

    db_manager = QuizDatabase()
    BACKEND_URL = "http://localhost:8000"
    print(st.session_state.username)

    # Initialize session state variables
    st.session_state.setdefault("quiz_id", None)
    st.session_state.setdefault("quiz_started", False)
    st.session_state.setdefault("role", None)
    st.session_state.setdefault("connected", False)
    st.session_state.setdefault("answers_sent", False)

    # Role selection (Professor or Student)
    role = st.radio("Select Role", options=["Professor", "Student"], key="role")

    if role == "Professor":
        st.title("Professor Dashboard")
        
        # Section to filter questions by subject and chapter
        st.subheader("Filtrer les questions par Matière et Chapitre")
        subjects = db_manager.get_subjects()  # Assurez-vous que cette méthode est implémentée dans QuizDatabase.
        if subjects:
            subject = st.selectbox("Sélectionnez une Matière", options=subjects, key="subject_select")
            chapters = db_manager.get_chapters_by_subject(subject)  # Implémenter cette méthode dans QuizDatabase.
            if chapters:
                chapter = st.selectbox("Sélectionnez un Chapitre", options=chapters, key="chapter_select")
                if st.button("Charger les Questions", key="load_questions"):
                    questions = db_manager.get_questions_by_subject_and_chapter(subject, chapter)
                    st.session_state["questions"] = questions  # Stocker les questions chargées
                    st.write("Questions Loaded!")
                    
            else:
                st.info("Aucun chapitre trouvé pour cette matière.")
        else:
            st.info("Aucune matière trouvée.")
        
        # Create Quiz
        if st.button("Create Room", key="create_room"):
            if st.session_state.get("questions"):
                # Créer une room avec les questions récupérées
                response = requests.post(f"{BACKEND_URL}/create_quiz_with_questions", json={"questions": st.session_state["questions"]})
            else:
                # Cas par défaut sans questions chargées
                response = requests.get(f"{BACKEND_URL}/create_quiz")
            print("Response text:", response.text)  # Debug print
            data = response.json()  # Traiter la réponse JSON
            st.session_state["quiz_id"] = data["quiz_id"]
            st.success(f"Quiz Created! Quiz ID: {st.session_state['quiz_id']}")
            st.write(f"Quiz Link: {data['link']}")

            # Generate QR Code
            qr = qrcode.make(data["link"])
            buffer = BytesIO()
            qr.save(buffer)
            buffer.seek(0)
            qr_image = Image.open(buffer)
            st.image(qr_image, caption="Scan to Join Quiz")

        # Show quiz management if quiz ID exists
        if st.session_state["quiz_id"]:
            st.subheader(f"Quiz ID: {st.session_state['quiz_id']}")
            start_button = st.button("Start Quiz")
            end_button = st.button("End Quiz")
            student_placeholder = st.empty()
            answer_placeholder = st.empty()
            leaderboard_placeholder = st.empty()

            async def manage_room():
                """Manage WebSocket for professor."""
                async with websockets.connect(f"ws://127.0.0.1:8000/ws/{st.session_state['quiz_id']}") as websocket:
                    if start_button:
                        await websocket.send(json.dumps({"action": "start_quiz"}))
                        st.success("Quiz started!")

                    if end_button:
                        await websocket.send(json.dumps({"action": "end_quiz"}))
                        st.success("Quiz has been ended.")
                        # Wait a moment for the leaderboard response
                    while True:
                        try:
                            data = await websocket.recv()
                            data = json.loads(data)

                            if "students" in data:
                                student_placeholder.write(f"Students in Room: {data['students']}")

                            if "answers" in data:
                                answer_placeholder.write(f"Student Answers: {data['answers']}")

                            if "leaderboard" in data:
                                leaderboard_placeholder.subheader("Leaderboard")
                                leaderboard_placeholder.table(data["leaderboard"])

                            if "quiz_ended" in data:
                                st.warning("The quiz has ended.")
                                break  # Stop listening once the quiz ends
                        except websockets.ConnectionClosed:
                            break

            asyncio.run(manage_room())

    elif role == "Student":
        st.title("Student Quiz Interface")

        quiz_id = st.text_input("Enter Quiz ID", key="quiz_id_input")
        student_id = st.session_state.get("username", "Anonymous")
        join_button = st.button("Join Room")

        async def join_quiz():
            """Join quiz room."""
            async with websockets.connect(f"ws://127.0.0.1:8000/ws/{quiz_id}") as websocket:
                await websocket.send(json.dumps({"action": "join", "student_id": student_id}))

                while True:
                    try:
                        data = await websocket.recv()
                        data = json.loads(data)

                        if "error" in data:
                            st.error(data["error"])
                            break

                        if "quiz_started" in data and data["quiz_started"]:
                            st.session_state["quiz_started"] = True
                            # Save the real questions sent from the professor
                            if "questions" in data:
                                st.session_state["questions"] = data["questions"]
                            st.success("Quiz has started!")
                            break

                        if "quiz_ended" in data:
                            st.warning("The quiz has ended.")
                            if "leaderboard" in data:
                                st.subheader("Leaderboard")
                                st.table(data["leaderboard"])
                            break
                    except websockets.ConnectionClosed:
                        break

        if join_button:
            if not quiz_id or not student_id:
                st.error("Please enter both Quiz ID and your name.")
            elif st.session_state["connected"]:
                st.error("You are already connected.")
            else:
                asyncio.run(join_quiz())
                st.session_state["connected"] = True

        if st.session_state["quiz_started"]:
            # Track which question is being displayed
            if "current_question_index" not in st.session_state:
                st.session_state["current_question_index"] = 0

            # Display the question at the current index
            current_index = st.session_state["current_question_index"]
            questions = st.session_state.get("questions", [])

            if questions and current_index < len(questions):
                current_question = questions[current_index]
                question_text = current_question.get("question_text", "No question text available")
                st.subheader("Question: " + question_text)

                choices = [
                    current_question.get("option1", ""), 
                    current_question.get("option2", ""), 
                    current_question.get("option3", ""), 
                    current_question.get("option4", "")
                ]
                # Use a unique key for each question
                answer = st.radio("Select Your Answer", 
                                  options=choices, 
                                  key=f"answer_choice_{current_index}")
                submit_button = st.button("Submit Answer", key=f"submit_button_{current_index}")

                async def submit_answer(answer_text):
                    """Submit an answer."""
                    async with websockets.connect(f"ws://127.0.0.1:8000/ws/{quiz_id}") as websocket:
                        payload = {
                            "action": "answer",
                            "student_id": student_id,
                            "answer": answer_text,
                            "question_id": current_question.get("question_id")
                        }
                        await websocket.send(json.dumps(payload))
                        st.success("Answer Submitted!")

                if submit_button:
                    st.session_state["answers_sent"] = True
                    asyncio.run(submit_answer(answer))
                    st.session_state["current_question_index"] += 1
            else:
                st.info("No more questions available or quiz not started.")


def main():
    Navbar()
    st.markdown(
        """
        <style>
        div.stButton > button {
            width: 100%;
            padding: 10px;
            font-size: 16px;
        }
        .button-row {
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.get('authenticated'):
        st.warning("You must be logged in to access the quiz.")
        return

    kahoot_quiz()
    

if __name__ == "__main__":
    main()
