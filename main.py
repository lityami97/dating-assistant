import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
import json

# ===== INIT =====
load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("❌ API key missing! Set GROQ_API_KEY in environment")

client = Groq(api_key=my_api_key)
model = "llama-3.3-70b-versatile"

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== PROFILE LOADING =====
profile_path = Path(__file__).parent / "USER PROFILE — YASH.txt"

try:
    profile_text = profile_path.read_text()
except FileNotFoundError:
    print(f"⚠️ Warning: Profile file not found at {profile_path}")
    profile_text = "Default profile - No user data loaded"

# ===== PYDANTIC SCHEMA =====
class Profile(BaseModel):
    profile: dict[str, list[str]]

schema = Profile.model_json_schema()

# ===== PARSE PROFILE TO JSON =====
system_prompt_parse = f"""
You are a JSON generator.
Convert the profile into JSON using ONLY this schema.
Do not add explanations.
{schema}
"""

messages_parse = [
    {"role": "system", "content": system_prompt_parse},
    {"role": "user", "content": f"Convert this profile into JSON:\n{profile_text}"}
]

try:
    response_parse = client.chat.completions.create(
        model=model,
        messages=messages_parse,
        response_format={"type": "json_object"}
    )
    raw_json = response_parse.choices[0].message.content
    data_file = json.loads(raw_json)
    ticket = Profile(**data_file)
    print("✅ Profile loaded successfully")
except json.JSONDecodeError as e:
    print(f"⚠️ JSON parsing error: {e}")
    ticket = Profile(profile={})
except Exception as e:
    print(f"⚠️ Profile parsing error: {e}")
    ticket = Profile(profile={})

# ===== MEMORY STORAGE =====
memory = {}

def memory_storage_tool(user_id: str, role: str, content: str):
    if user_id not in memory:
        memory[user_id] = []
    memory[user_id].append({"role": role, "content": content})

def memory_retrieval_tool(user_id: str):
    return memory.get(user_id, [])

# ===== TOOLS =====
def introduction_tool():
    try:
        return {
            "Identity": ticket.profile.get("Identity", []),
            "Personality": ticket.profile.get("Personality", []),
            "Interests": ticket.profile.get("Interests", []),
            "Relationship": ticket.profile.get("Relationship", []),
        }
    except KeyError as e:
        return {"error": f"Missing profile section: {e}"}

# ===== CHAT LOGIC =====
def get_relevant_section(question: str) -> str:
    """Classifies question to appropriate profile section"""
    
    available_sections = list(ticket.profile.keys())
    
    classifier_prompt = f"""You are a classifier.
Available sections: {available_sections}

User question: {question}

Rules:
- Return ONLY one section name if the answer can be found there
- If no section matches, return only: UNKNOWN
- Do not explain. Do not output anything except section name or UNKNOWN."""

    messages_classify = [
        {"role": "system", "content": classifier_prompt},
        {"role": "user", "content": question}
    ]

    try:
        response_classify = client.chat.completions.create(
            model=model,
            messages=messages_classify
        )
        heading = response_classify.choices[0].message.content.strip()
        return heading
    except Exception as e:
        print(f"❌ Classification error: {e}")
        return "UNKNOWN"

def answer_question(question: str, user_id: str = "default") -> str:
    """Main chat function with memory + profile context"""
    
    # Get relevant section
    section = get_relevant_section(question)
    
    if section.upper() == "UNKNOWN":
        relevant_data = []
    else:
        relevant_data = ticket.profile.get(section, [])
    
    # Build context with memory
    memory_context = memory_retrieval_tool(user_id)
    
    system_prompt_chat = f"""You are roleplaying as Yash.
You're a comedian who flirts and does comedy.

Use ONLY the profile information below. Never invent info.

Profile data: {relevant_data}

If profile doesn't have enough info, reply:
"That's something you'd have to ask Yash personally. He hasn't shared that with me yet."

Keep responses funny, flirty, and charming."""

    messages_chat = memory_context + [
        {"role": "system", "content": system_prompt_chat},
        {"role": "user", "content": question}
    ]

    # Stream response
    answer = ""
    try:
        chat_response = client.chat.completions.create(
            model=model,
            messages=messages_chat,
            stream=True,
            temperature=0.7
        )

        for chunk in chat_response:
            if chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                answer += text
                print(text, end="", flush=True)
        
        print()  # newline after stream
    except Exception as e:
        print(f"❌ Chat error: {e}")
        answer = "Something went wrong. Try again!"
    
    # Store in memory
    memory_storage_tool(user_id, "user", question)
    memory_storage_tool(user_id, "assistant", answer)
    
    return answer

# ===== API ENDPOINTS =====
@app.get("/")
def home():
    return {
        "message": "Hey, this is Yash's AI dating assistant 😎",
        "endpoints": {
            "/intro": "Get Yash's intro",
            "/chat": "POST with question in body",
            "/memory": "GET memory for user"
        }
    }

@app.get("/intro")
def get_intro():
    return introduction_tool()

class ChatRequest(BaseModel):
    question: str
    user_id: str = "default"

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    print(f"\n👤 {req.user_id}: {req.question}")
    response = answer_question(req.question, req.user_id)
    return {"response": response}

@app.get("/memory/{user_id}")
def get_memory(user_id: str):
    return {"memory": memory_retrieval_tool(user_id)}

@app.delete("/memory/{user_id}")
def clear_memory(user_id: str):
    if user_id in memory:
        del memory[user_id]
        return {"status": "Memory cleared"}
    return {"status": "No memory found"}

# ===== RUN =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)