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
system_prompt_parse = f"""You are a profile parser. Your task is to extract ALL information from a user profile and convert it into structured JSON.

CRITICAL RULES:
1. Extract EVERY section header and ALL its content
2. Preserve hierarchical structure - nested keys must be included
3. For lists, split by commas or bullets and clean whitespace
4. Do NOT drop any data - completeness is mandatory
5. Do NOT hallucinate or infer data not present
6. Return ONLY valid JSON matching this schema, no explanations
7. If a section is empty, still include it with empty array []

Schema to follow strictly:
{schema}

Common section headers to look for:
- Identity (name, age, location, profession, title)
- Personality (traits, characteristics, behavioral style)
- Interests (hobbies, passions, likes, activities)
- Skills (competencies, expertise, abilities)
- Relationships (family, friends, connections, people)
- Values (beliefs, principles, what matters)
- Goals (aspirations, targets, future plans)
- Preferences (likes, dislikes, favorites)
- Background (history, education, experience)
- Style (communication, aesthetics, approach)"""

messages_parse = [
    {"role": "system", "content": system_prompt_parse},
    {"role": "user", "content": f"Parse this profile into JSON:\n\n{profile_text}"}
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
    print(f"📋 Sections: {list(ticket.profile.keys())}")
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
    """Classifies question to appropriate profile section with fuzzy matching"""
    
    available_sections = list(ticket.profile.keys())
    
    classifier_prompt = f"""You are a semantic classifier. Map user questions to profile sections with high accuracy.

Available profile sections:
{json.dumps(available_sections)}

User question: "{question}"

MAPPING RULES:
- "what do you like?" → "Interests" or "Preferences"
- "who are you?" → "Identity"
- "how are you?" → "Personality"
- "what are your goals?" → "Goals"
- "tell me about yourself" → "Background" or "Identity"
- "what do you do?" → "Skills" or "Profession"
- "your hobbies" → "Interests"
- "your values" → "Values"
- "your style" → "Style"
- "family/friends" → "Relationships"

OUTPUT RULE:
Return ONLY the exact section name from available sections, or "UNKNOWN" if no match.
Do not add anything else - no explanations, no reasoning."""

    messages_classify = [
        {"role": "system", "content": classifier_prompt},
        {"role": "user", "content": question}
    ]

    try:
        response_classify = client.chat.completions.create(
            model=model,
            messages=messages_classify
        )
        heading = response_classify.choices[0].message.content.strip().upper()
        
        # Fallback: check if heading is in available sections
        for section in available_sections:
            if heading == section.upper():
                return section
        
        return "UNKNOWN"
    except Exception as e:
        print(f"❌ Classification error: {e}")
        return "UNKNOWN"

def answer_question(question: str, user_id: str = "default") -> str:
    """Main chat function with memory + profile context - IMPROVED"""
    
    # Get relevant section
    section = get_relevant_section(question)
    
    if section == "UNKNOWN":
        relevant_data = []
    else:
        relevant_data = ticket.profile.get(section, [])
    
    # Retrieve conversation history
    conversation_history = memory_retrieval_tool(user_id)
    
    # Format context
    profile_context = "USER PROFILE CONTEXT:\n"
    for section_name, section_data in ticket.profile.items():
        profile_context += f"\n{section_name}:\n"
        for item in section_data:
            profile_context += f"  - {item}\n"
    
    # Build conversation history for context
    history_text = ""
    if conversation_history:
        history_text = "\nRECENT CONVERSATION HISTORY:\n"
        for msg in conversation_history[-6:]:  # Last 3 exchanges
            role = "User" if msg["role"] == "user" else "You"
            history_text += f"{role}: {msg['content']}\n"
    
    # Build relevant section context
    relevant_section_text = ""
    if relevant_data:
        relevant_section_text = f"\nRELEVANT PROFILE SECTION ({section}):\n"
        for item in relevant_data:
            relevant_section_text += f"  - {item}\n"
    
    # System prompt - STRONG IDENTITY & ADHERENCE
    system_prompt_answer = f"""You are an AI assistant embodying the personality and knowledge of the user based on their profile.

CORE DIRECTIVES:
1. STRICT ADHERENCE: Answer ONLY using information from the provided profile. Do NOT hallucinate or invent facts.
2. CHARACTER CONSISTENCY: Maintain the exact personality, tone, and characteristics described in the profile.
3. CONTEXTUAL AWARENESS: Use relevant profile sections to inform your responses with authenticity.
4. MEMORY INTEGRATION: Reference previous conversation points to maintain continuity and coherence.
5. ACCURACY FIRST: If information is not in the profile, explicitly state "I don't have that information in my profile" rather than guessing.

PROFILE DATA:
{profile_context}
{relevant_section_text}
{history_text}

RESPONSE FORMAT:
- Keep responses natural and conversational
- Use first-person perspective ("I", "my", "we" if applicable)
- Match the communication style from the profile
- Be authentic to the personality traits listed
- Keep responses concise and relevant (2-3 sentences typically)"""

    # Build messages for LLM
    messages_answer = [
        {"role": "system", "content": system_prompt_answer},
    ]
    
    # Add conversation history
    for msg in conversation_history:
        messages_answer.append(msg)
    
    # Add current question
    messages_answer.append({"role": "user", "content": question})
    
    try:
        response_answer = client.chat.completions.create(
            model=model,
            messages=messages_answer,
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response_answer.choices[0].message.content
        
        # Store in memory
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
    section = get_relevant_section(request.question)
    answer = answer_question(request.question, request.user_id)
    return ChatResponse(
        question=request.question,
        answer=answer,
        section_used=section
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
