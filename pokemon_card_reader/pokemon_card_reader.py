# Placeholder for known Pokémon card names
KNOWN_NAMES = []

def fetch_known_names():
    global KNOWN_NAMES
    if not KNOWN_NAMES:
        headers = {"X-Api-Key": POKEMON_TCG_API_KEY}
        response = requests.get("https://api.pokemontcg.io/v2/cards?pageSize=250", headers=headers)
        cards = response.json().get("data", [])
        KNOWN_NAMES = list(set([card["name"] for card in cards if "name" in card]))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests, os
from rapidfuzz import process

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount UI folders
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# API key & endpoint
POKEMON_TCG_API_KEY = os.getenv("POKEMON_TCG_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.pokemontcg.io/v2/cards"

# Caching known Pokémon names
KNOWN_NAMES = []

def fetch_known_names():
    global KNOWN_NAMES
    if not KNOWN_NAMES:
        headers = {"X-Api-Key": POKEMON_TCG_API_KEY}
        response = requests.get(BASE_URL + "?pageSize=250", headers=headers)
        if response.status_code == 200:
            cards = response.json().get("data", [])
            KNOWN_NAMES = list(set([card.get("name", "") for card in cards]))

def correct_name(name):
    fetch_known_names()
    match, score, _ = process.extractOne(name.lower(), KNOWN_NAMES)
    return match if score > 70 else name

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, name: str = "", card_type: str = ""):
    query_parts = []
    fixed_name = name  # default to original

    # Fuzzy name correction
    if name:
        corrected = correct_name(name)
        if corrected.lower() != name.lower():
            fixed_name = corrected
        query_parts.append(f'name:"{fixed_name}"')

    # Card type search (subtypes or rarity)
    if card_type:
        query_parts.append(f'(subtypes:"{card_type}" OR rarity:"{card_type}")')

    q = " ".join(query_parts)
    params = {
        "q": q,
        "pageSize": 20
    }

    headers = {"X-Api-Key": POKEMON_TCG_API_KEY}
    response = requests.get(BASE_URL, headers=headers, params=params)
    cards = response.json().get("data", [])

    return templates.TemplateResponse("index.html", {
        "request": request,
        "cards": cards,
        "search_name": name,
        "fixed_name": fixed_name,
        "search_type": card_type
    })
