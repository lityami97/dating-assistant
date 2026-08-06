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

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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

# ===== PARSE PROFILE TO JSON - IMPROVED =====
system_prompt_parse = f"""You are a JSON generator that extracts user profile information with absolute precision.

CRITICAL RULES:
1. Extract EVERY section header and ALL its content WITHOUT OMISSIONS
2. Preserve all key-value pairs and nested structures exactly as presented
3. For list items, split by commas, bullets, or line breaks and clean whitespace
4. DO NOT drop any data - completeness is mandatory
5. DO NOT hallucinate or infer data not explicitly present in the profile
6. Return ONLY valid JSON matching the provided schema with no explanations
7. If a section has no data, still include it with an empty array []
8. Common section headers: Identity, Personality, Interests, Skills, Relationships, Values, Goals, Preferences, Background, Style, Hobbies, Experience

Schema to follow strictly:
{schema}"""

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

# ===== CHAT LOGIC - IMPROVED =====
def get_relevant_section(question: str) -> str:
    """Classifies question to appropriate profile section with fuzzy matching and fallback"""
    
    available_sections = list(ticket.profile.keys())
    
    classifier_prompt = f"""You are a semantic section classifier. Your task is to map user questions to the most relevant profile section.

Available profile sections: {available_sections}

User question: "{question}"

MAPPING RULES:
- Questions like "what do you like?" or "your favorites?" → "Interests" or "Preferences"
- Questions like "who are you?" or "tell me about yourself" → "Identity" or "Background"
- Questions like "how are you?" or "your character" → "Personality"
- Questions like "what are your goals?" or "future plans" → "Goals"
- Questions like "what do you do?" or "your job" → "Skills" or "Experience"
- Questions like "your hobbies?" → "Interests" or "Hobbies"
- Questions like "what matters to you?" → "Values"
- Questions like "your style?" → "Style"
- Questions like "family?" or "friends?" → "Relationships"

OUTPUT INSTRUCTION:
Return ONLY the exact section name from the available sections list.
If no section matches, return only: UNKNOWN
Do not add explanations or reasoning."""

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
        
        # Fallback validation: ensure heading matches available sections
        for section in available_sections:
            if heading.upper() == section.upper():
                return section
        
        return "UNKNOWN"
    except Exception as e:
        print(f"❌ Classification error: {e}")
        return "UNKNOWN"

def answer_question(question: str, user_id: str = "default") -> str:
    """Main chat function with memory + profile context - IMPROVED SYSTEM PROMPT"""
    
    # Get relevant section
    heading = get_relevant_section(question)
    
    if heading.upper() == "UNKNOWN":
        relevant_data = []
    else:
        relevant_data = ticket.profile.get(heading, [])
        
    # Retrieve conversation history
    chat_history = memory_retrieval_tool(user_id)
    
    # Build full profile context
    full_profile_context = ""
    for key, values in ticket.profile.items():
        full_profile_context += f"{key}: {', '.join(values)}\n"
    
    # Build relevant section context
    relevant_context = ""
    if relevant_data:
        relevant_context = f"\nMost Relevant Information ({heading}):\n{', '.join(relevant_data)}"
    
    # Format chat history for context
    history_context = ""
    if chat_history:
        history_context = "\nPrevious Conversation:\n"
        for msg in chat_history[-4:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_context += f"{role}: {msg['content']}\n"
    
    # STRONG SYSTEM PROMPT - STRICT PROFILE ADHERENCE
    system_prompt_answer = f"""You are an AI assistant that embodies the personality, characteristics, knowledge, and communication style of a user based on their complete profile.

CORE IDENTITY RULES:
1. STRICT PROFILE ADHERENCE: Answer ONLY using information from the user's profile provided. NEVER hallucinate, invent, or assume facts not explicitly stated in the profile.
2. CHARACTER AUTHENTICITY: Maintain exact personality traits, communication style, tone, and behavioral patterns from the profile at all times.
3. CONTEXTUAL ACCURACY: Use the most relevant profile section to provide authentic, grounded responses that align with the user's documented information.
4. CONVERSATION CONTINUITY: Reference and maintain consistency with previous conversation points to preserve logical flow and conversation memory.
5. HONEST LIMITATIONS: If asked about something not in the profile, clearly state "I don't have that information in my profile" rather than guessing or fabricating details.
6. FIRST-PERSON CONSISTENCY: Always speak from the user's perspective using their profile data as the foundation for all statements.

COMPLETE USER PROFILE DATA:
{full_profile_context}
{relevant_context}
{history_context}

RESPONSE STYLE:
- Speak naturally using first person ("I", "my", "we" where applicable)
- Match the exact communication style and tone from the profile
- Keep responses conversational and concise (typically 1-3 sentences)
- Prioritize accuracy and profile-alignment over elaboration
- Maintain personality consistency even when discussing unfamiliar topics"""

    # Build messages array with system prompt + history + current question
    messages_answer = [
        {"role": "system", "content": system_prompt_answer}
    ]
    
    # Add existing chat history
    for msg in chat_history:
        messages_answer.append(msg)
    
    # Add current user question
    messages_answer.append({"role": "user", "content": question})
    
    try:
        response_answer = client.chat.completions.create(
            model=model,
            messages=messages_answer,
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response_answer.choices[0].message.content
        
        # Store Q&A in memory
        memory_storage_tool(user_id, "user", question)
        memory_storage_tool(user_id, "assistant", answer)
        
        return answer
    except Exception as e:
        print(f"❌ Answer generation error: {e}")
        return f"Error generating response: {str(e)}"

# ===== PYDANTIC REQUEST/RESPONSE MODELS =====
class ChatRequest(BaseModel):
    question: str
    user_id: str = "default"

class ChatResponse(BaseModel):
    question: str
    answer: str
    section_used: str

# ===== ROUTES =====
@app.get("/")
def read_root():
    return {"status": "✅ FastAPI with Groq is running"}

@app.get("/profile")
def get_profile():
    return {"profile": ticket.profile}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    heading = get_relevant_section(request.question)
    answer = answer_question(request.question, request.user_id)
    return ChatResponse(
        question=request.question,
        answer=answer,
        section_used=heading
    )

@app.get("/memory/{user_id}")
def get_memory(user_id: str):
    return {"user_id": user_id, "history": memory_retrieval_tool(user_id)}

@app.delete("/memory/{user_id}")
def clear_memory(user_id: str):
    if user_id in memory:
        del memory[user_id]
        return {"status": f"Memory cleared for {user_id}"}
    return {"status": f"No memory found for {user_id}"}

# ===== MAIN =====
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
