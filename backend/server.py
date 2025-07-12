from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import requests
import json
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Models
class TimelineEvent(BaseModel):
    year: int
    date: str
    event: str
    impact: str
    probability: str
    image_url: str
    image_description: str

class AlternateTimeline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_scenario: str
    historical_context: List[str]
    timeline_events: List[TimelineEvent]
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TimelineRequest(BaseModel):
    scenario: str
    depth: str = "brief"  # "brief" or "detailed"

class HistoricalFact(BaseModel):
    title: str
    summary: str
    url: str
    
# Wikipedia API functions
def search_wikipedia(query: str, limit: int = 3) -> List[Dict]:
    """Search Wikipedia for relevant historical facts"""
    try:
        # Search for relevant pages
        search_url = "https://en.wikipedia.org/api/rest_v1/page/search"
        search_params = {
            'q': query,
            'limit': limit
        }
        search_response = requests.get(search_url, params=search_params)
        search_results = search_response.json()
        
        facts = []
        for page in search_results.get('pages', [])[:limit]:
            page_title = page['title']
            page_key = page['key']
            
            # Get page summary
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_key}"
            summary_response = requests.get(summary_url)
            summary_data = summary_response.json()
            
            facts.append({
                'title': page_title,
                'summary': summary_data.get('extract', ''),
                'url': f"https://en.wikipedia.org/wiki/{page_key}"
            })
        
        return facts
    except Exception as e:
        logger.error(f"Wikipedia search error: {e}")
        return []

def extract_historical_context(scenario: str) -> List[str]:
    """Extract historical context from Wikipedia based on the scenario"""
    # Parse the scenario to extract key terms for search
    search_terms = []
    
    # Simple keyword extraction (could be enhanced with NLP)
    if "gandhi" in scenario.lower():
        search_terms.append("Mahatma Gandhi")
        search_terms.append("Indian independence movement")
    if "world war" in scenario.lower():
        search_terms.append("World War")
    if "einstein" in scenario.lower():
        search_terms.append("Albert Einstein")
    if "1940" in scenario or "1950" in scenario:
        search_terms.append("1940s history")
    
    # Add general terms from scenario
    words = scenario.split()
    for word in words:
        if len(word) > 4 and word.lower() not in ['what', 'would', 'happen', 'during']:
            search_terms.append(word)
    
    all_facts = []
    for term in search_terms[:3]:  # Limit to avoid too many API calls
        facts = search_wikipedia(term, 2)
        all_facts.extend(facts)
    
    return [f"{fact['title']}: {fact['summary'][:200]}..." for fact in all_facts[:5]]

def get_contextual_image(event_text: str, year: int) -> tuple[str, str]:
    """Get contextual image for timeline event"""
    # Curated historical images for different eras and contexts
    historical_images = {
        'ancient': {
            'url': 'https://images.unsplash.com/photo-1728242410475-b4a44c08ebb3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHwzfHxoaXN0b3JpY2FsJTIwdGltZWxpbmV8ZW58MHx8fHwxNzUyMzQ5MzcwfDA&ixlib=rb-4.1.0&q=85',
            'description': 'Ancient historical artifacts and hieroglyphs'
        },
        'medieval': {
            'url': 'https://images.pexels.com/photos/29082058/pexels-photo-29082058.jpeg',
            'description': 'Medieval architecture and historical buildings'
        },
        'renaissance': {
            'url': 'https://images.unsplash.com/photo-1574438041772-09c77dc8c1dc?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHwyfHxoaXN0b3JpY2FsJTIwdGltZWxpbmV8ZW58MHx8fHwxNzUyMzQ5MzcwfDA&ixlib=rb-4.1.0&q=85',
            'description': 'Renaissance period education and knowledge'
        },
        'industrial': {
            'url': 'https://images.pexels.com/photos/32957809/pexels-photo-32957809.jpeg',
            'description': 'Industrial age documents and newspapers'
        },
        'modern': {
            'url': 'https://images.unsplash.com/photo-1623990671462-0aa112e1ed32?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwxfHx2aW50YWdlJTIwdGVjaG5vbG9neXxlbnwwfHx8fDE3NTIzNDkzNzd8MA&ixlib=rb-4.1.0&q=85',
            'description': 'Early modern technology and communications'
        },
        'contemporary': {
            'url': 'https://images.unsplash.com/photo-1620046311691-5d93d65f69e9?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwzfHx2aW50YWdlJTIwdGVjaG5vbG9neXxlbnwwfHx8fDE3NTIzNDkzNzd8MA&ixlib=rb-4.1.0&q=85',
            'description': 'Computer age and digital technology'
        },
        'futuristic': {
            'url': 'https://images.pexels.com/photos/30845986/pexels-photo-30845986.jpeg',
            'description': 'Future pathways and possibilities'
        },
        'default': {
            'url': 'https://images.unsplash.com/photo-1689712550124-0dab4dc855f1?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHwxfHxoaXN0b3JpY2FsJTIwdGltZWxpbmV8ZW58MHx8fHwxNzUyMzQ5MzcwfDA&ixlib=rb-4.1.0&q=85',
            'description': 'Historical timeline and chronological events'
        }
    }
    
    # Determine era based on year and content
    event_lower = event_text.lower()
    
    if year < 500:
        era = 'ancient'
    elif 500 <= year < 1400:
        era = 'medieval'
    elif 1400 <= year < 1750:
        era = 'renaissance'
    elif 1750 <= year < 1950:
        era = 'industrial'
    elif 1950 <= year < 2000:
        era = 'modern'
    elif 2000 <= year < 2050:
        era = 'contemporary'
    else:
        era = 'futuristic'
    
    # Content-based overrides
    if any(word in event_lower for word in ['computer', 'digital', 'internet', 'ai', 'technology']):
        era = 'contemporary'
    elif any(word in event_lower for word in ['radio', 'television', 'communication', 'wireless']):
        era = 'modern'
    elif any(word in event_lower for word in ['printing', 'press', 'book', 'education', 'knowledge']):
        era = 'renaissance'
    elif any(word in event_lower for word in ['ancient', 'egypt', 'rome', 'greece', 'pyramid']):
        era = 'ancient'
    
    image_data = historical_images.get(era, historical_images['default'])
    return image_data['url'], image_data['description']

async def generate_timeline_with_llm(scenario: str, historical_context: List[str], depth: str) -> AlternateTimeline:
    """Generate alternate timeline using LLM"""
    try:
        # Create system message for historical timeline generation
        system_message = """You are an expert historian and speculative fiction writer. Your job is to create plausible alternate history timelines based on hypothetical changes to real historical events.

When given a scenario, you should:
1. Analyze the historical context provided
2. Create a believable chain of cause and effect
3. Generate specific events with dates, descriptions, and impacts
4. Maintain historical plausibility while exploring the consequences

Format your response as a JSON object with this structure:
{
    "summary": "Brief overview of how this change would have affected history",
    "timeline_events": [
        {
            "year": 1947,
            "date": "August 15, 1947",
            "event": "Specific event description",
            "impact": "Immediate and long-term consequences",
            "probability": "High/Medium/Low likelihood of this occurring"
        }
    ]
}

Keep events realistic and grounded in historical possibility. Do not include image_url or image_description fields - those will be added separately."""

        # Create the prompt
        context_text = "\n".join([f"- {fact}" for fact in historical_context])
        event_count = 10 if depth == "detailed" else 5
        
        user_prompt = f"""
SCENARIO: {scenario}

HISTORICAL CONTEXT:
{context_text}

Generate a {depth} alternate timeline with {event_count} key events showing how this change would have rippled through history. Focus on major political, social, and technological consequences.

Respond with valid JSON only."""

        # Initialize LLM chat
        chat = LlmChat(
            api_key=os.environ.get('GOOGLE_API_KEY'),
            session_id=str(uuid.uuid4()),
            system_message=system_message
        ).with_model("gemini", "gemini-2.5-flash").with_max_tokens(4096)

        # Send message and get response
        user_message = UserMessage(text=user_prompt)
        response = await chat.send_message(user_message)
        
        # Parse the JSON response
        try:
            # Clean the response to extract JSON
            response_text = response.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            timeline_data = json.loads(response_text)
            
            # Create timeline events
            events = []
            for event_data in timeline_data.get('timeline_events', []):
                events.append(TimelineEvent(**event_data))
            
            timeline = AlternateTimeline(
                original_scenario=scenario,
                historical_context=historical_context,
                timeline_events=events,
                summary=timeline_data.get('summary', 'An alternate timeline exploring the consequences of this historical change.')
            )
            
            return timeline
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Fallback timeline
            return AlternateTimeline(
                original_scenario=scenario,
                historical_context=historical_context,
                timeline_events=[
                    TimelineEvent(
                        year=2024,
                        date="Present Day",
                        event=f"In this alternate timeline: {response[:200]}...",
                        impact="The world would be fundamentally different today.",
                        probability="Speculative"
                    )
                ],
                summary="An alternate timeline exploring historical possibilities."
            )
            
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate timeline: {str(e)}")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "AI Time Machine API"}

@api_router.post("/generate-timeline", response_model=AlternateTimeline)
async def generate_timeline(request: TimelineRequest):
    """Generate an alternate history timeline"""
    try:
        # Extract historical context from Wikipedia
        logger.info(f"Generating timeline for scenario: {request.scenario}")
        historical_context = extract_historical_context(request.scenario)
        
        # Generate timeline using LLM
        timeline = await generate_timeline_with_llm(request.scenario, historical_context, request.depth)
        
        # Save to database
        await db.timelines.insert_one(timeline.dict())
        
        return timeline
        
    except Exception as e:
        logger.error(f"Timeline generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/timelines", response_model=List[AlternateTimeline])
async def get_timelines():
    """Get all generated timelines"""
    timelines = await db.timelines.find().sort("created_at", -1).to_list(50)
    return [AlternateTimeline(**timeline) for timeline in timelines]

@api_router.get("/timeline/{timeline_id}", response_model=AlternateTimeline)
async def get_timeline(timeline_id: str):
    """Get a specific timeline by ID"""
    timeline = await db.timelines.find_one({"id": timeline_id})
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return AlternateTimeline(**timeline)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()