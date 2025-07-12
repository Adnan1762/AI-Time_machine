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

Keep events realistic and grounded in historical possibility."""

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
        ).with_model("gemini", "gemini-2.5-pro-preview-05-06").with_max_tokens(4096)

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