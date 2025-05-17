# Placeholder for known Pokémon card names
KNOWN_NAMES = []

def fetch_known_names():
    global KNOWN_NAMES
    if not KNOWN_NAMES:
        headers = {"X-Api-Key": POKEMON_TCG_API_KEY}
        response = requests.get("https://api.pokemontcg.io/v2/cards?pageSize=250", headers=headers)
        cards = response.json().get("data", [])
        KNOWN_NAMES = list(set([card["name"] for card in cards if "name" in card]))

# pokemon_card_reader.py
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests, os
from rapidfuzz import process

app = FastAPI()

# CORS for mobile/FlutterFlow compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount folders for UI
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# API Key & Endpoint
POKEMON_TCG_API_KEY = os.getenv("POKEMON_TCG_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.pokemontcg.io/v2/cards"
HEADERS = {"X-Api-Key": POKEMON_TCG_API_KEY}
KNOWN_NAMES = []

def fetch_known_names():
    global KNOWN_NAMES
    if not KNOWN_NAMES:
        response = requests.get(f"{BASE_URL}?pageSize=250", headers=HEADERS)
        if response.status_code == 200:
            cards = response.json().get("data", [])
            KNOWN_NAMES = list(set([card.get("name", "") for card in cards]))

def correct_name(name: str):
    fetch_known_names()
    match, score, _ = process.extractOne(name.lower(), KNOWN_NAMES)
    return match if score > 70 else name

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, name: str = "", card_type: str = ""):
    query_parts = []
    fixed_name = name

    if name:
        corrected = correct_name(name)
        if corrected.lower() != name.lower():
            fixed_name = corrected
        query_parts.append(f'name:"{fixed_name}"')

    if card_type:
        query_parts.append(f'(subtypes:"{card_type}" OR rarity:"{card_type}")')

    q = " ".join(query_parts)
    params = {"q": q, "pageSize": 20}

    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    cards = response.json().get("data", []) if response.status_code == 200 else []

    return templates.TemplateResponse("index.html", {
        "request": request,
        "cards": cards,
        "search_name": name,
        "corrected_name": fixed_name,
        "search_type": card_type,
        "error": response.status_code != 200
    })