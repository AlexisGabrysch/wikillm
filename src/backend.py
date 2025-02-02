from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for quiz sessions
sessions = {}  # {quiz_id: {"students": {}, "answers": [], "quiz_started": False}}
connections = {}  # {quiz_id: [websocket]}
@app.get("/")
async def read_root():
    return {"Initial": "Hello World"}

@app.get("/create_quiz")
async def create_quiz():
    """Create a new quiz session with a unique ID."""
    quiz_id = str(uuid.uuid4())[:8]
    sessions[quiz_id] = {"students": {}, "answers": [], "quiz_started": False}
    return {"quiz_id": quiz_id, "link": f"http://localhost:8501/{quiz_id}"}

# New endpoint to create a quiz with questions provided by the professor.
@app.post("/create_quiz_with_questions")
async def create_quiz_with_questions(payload: dict):
    questions = payload.get("questions", [])
    quiz_id = str(uuid.uuid4())[:8]
    sessions[quiz_id] = {"students": {}, "answers": [], "quiz_started": False, "questions": questions}
    return {"quiz_id": quiz_id, "link": f"http://localhost:8501/{quiz_id}"}

@app.get("/validate_quiz/{quiz_id}")
async def validate_quiz(quiz_id: str):
    """Validate if a quiz ID exists."""
    if quiz_id in sessions:
        return {"valid": True}
    return {"valid": False, "message": "Invalid Quiz ID"}


@app.websocket("/ws/{quiz_id}")
async def websocket_endpoint(websocket: WebSocket, quiz_id: str):
    await websocket.accept()

    if quiz_id not in sessions:
        await websocket.send_json({"error": "Invalid Quiz ID"})
        await websocket.close()
        return

    if quiz_id not in connections:
        connections[quiz_id] = []

    connections[quiz_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            student_id = data.get("student_id")
            answer = data.get("answer")

            # Student joining the room
            if action == "join":
                if len(sessions[quiz_id]["students"]) >= 5:
                    await websocket.send_json({"error": "Room is full. Maximum 5 students allowed."})
                elif student_id in sessions[quiz_id]["students"]:
                    await websocket.send_json({"error": "Username already taken. Please choose another."})
                else:
                    sessions[quiz_id]["students"][student_id] = websocket
                    for conn in connections[quiz_id]:
                        await conn.send_json({
                            "students": list(sessions[quiz_id]["students"].keys()),
                            "quiz_started": sessions[quiz_id]["quiz_started"]
                        })

            # Student leaving the room
            elif action == "leave":
                if student_id in sessions[quiz_id]["students"]:
                    del sessions[quiz_id]["students"][student_id]
                    for conn in connections[quiz_id]:
                        await conn.send_json({"students": list(sessions[quiz_id]["students"].keys())})

            # Starting the quiz
            elif action == "start_quiz":
                sessions[quiz_id]["quiz_started"] = True
                questions = sessions[quiz_id].get("questions", [])
                for conn in connections[quiz_id]:
                    await conn.send_json({"quiz_started": True, "questions": questions})

            # Submitting an answer
            elif action == "answer":
                question_id = data.get("question_id")
                # Check if the student already answered this question.
                if any(a["student_id"] == student_id and a["question_id"] == question_id for a in sessions[quiz_id]["answers"]):
                    await websocket.send_json({"error": "You have already submitted your answer for this question."})
                else:
                    sessions[quiz_id]["answers"].append({
                        "student_id": student_id, 
                        "question_id": question_id, 
                        "answer": answer
                    })
                    for conn in connections[quiz_id]:
                        await conn.send_json({"answers": sessions[quiz_id]["answers"]})

            # Ending the quiz: compute leaderboard based on correct answers
            elif action == "end_quiz":
                # Compute score per student using questions' correct answers
                leaderboard = {}
                questions = sessions[quiz_id].get("questions", [])
                # Map each question by its id
                questions_map = {q["question_id"]: q for q in questions}
                for ans in sessions[quiz_id]["answers"]:
                    qid = ans["question_id"]
                    q = questions_map.get(qid)
                    if not q: 
                        continue
                    correct_option = q.get(f"option{q.get('correct_index')}")
                    if ans["answer"] == correct_option:
                        leaderboard[ans["student_id"]] = leaderboard.get(ans["student_id"], 0) + 1
                leaderboard_list = [{"student_id": student, "score": score} for student, score in leaderboard.items()]
                leaderboard_list.sort(key=lambda x: x["score"], reverse=True)
                for conn in connections[quiz_id]:
                    await conn.send_json({
                        "quiz_ended": True,
                        "leaderboard": leaderboard_list
                    })
                    await conn.close()
                del sessions[quiz_id]
                del connections[quiz_id]
                break  # Exit the loop

    except WebSocketDisconnect:
        connections[quiz_id].remove(websocket)
        if not connections[quiz_id]:
            del connections[quiz_id]
