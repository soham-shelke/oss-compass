import os
import sys
import requests
from dotenv import load_dotenv
from collections import Counter
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# NEW: Import FastAPI and Pydantic
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


# --- Load Environment Variables and Configure APIs ---
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_KEYS = [key for key in [os.getenv("GEMINI_API_KEY_PRIMARY"), os.getenv("GEMINI_API_KEY_SECONDARY")] if key]

if not GITHUB_TOKEN: raise ValueError("GitHub token not found in .env file.")
if not GEMINI_KEYS: raise ValueError("No Gemini API keys found in .env file.")

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
GITHUB_API_URL = "https://api.github.com"


# --- NEW: Create the FastAPI app instance ---
app = FastAPI()

# NEW: Add CORS middleware to allow your frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# NEW: Define the request data model
class AnalyzeRequest(BaseModel):
    username: str


# --- Helper Functions (Your existing logic, mostly unchanged) ---

def get_user_top_languages(username: str, count: int = 3):
    # ... (This function remains the same as before)
    print(f"-> Finding top {count} languages for user: {username}...")
    repos_url = f"{GITHUB_API_URL}/users/{username}/repos?type=owner&sort=updated"
    try:
        response = requests.get(repos_url, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return []
    repos = response.json()
    if not repos: return []
    languages = [repo["language"] for repo in repos if repo["language"] is not None]
    if not languages: return []
    top_languages = [lang for lang, count in Counter(languages).most_common(count)]
    print(f"-> Top languages found: {', '.join(top_languages)}")
    return top_languages

def find_good_first_issues(language: str):
    # ... (This function remains the same as before)
    print(f"-> Searching for beginner-friendly issues in {language}...")
    search_url = f"{GITHUB_API_URL}/search/issues"
    query = f'language:{language} (label:"good first issue" OR label:"help wanted") state:open is:issue'
    params = {"q": query, "sort": "updated", "order": "desc", "per_page": 10}
    try:
        response = requests.get(search_url, headers=HEADERS, params=params)
        if response.status_code == 403: return None
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return None
    return response.json().get("items", [])

def get_ai_analysis(issue_title: str, issue_body: str):
    # ... (This function remains the same as before)
    if not issue_body: issue_body = "No description provided."
    prompt = f"""Analyze the following GitHub issue and explain in a single, concise sentence why it is a good first issue for a new open-source contributor. Focus on the task's nature (e.g., "documentation update," "simple bug fix," "UI improvement").
    Issue Title: {issue_title}
    Issue Description: {issue_body[:500]}
    Reason:"""
    for i, key in enumerate(GEMINI_KEYS):
        print(f"--> Attempting AI analysis with key #{i+1}...")
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('models/gemini-pro-latest') 
            response = model.generate_content(prompt)
            return response.text.strip()
        except google_exceptions.ResourceExhausted:
            print(f"    - Key #{i+1} is rate-limited. Trying next key...")
            continue
        except Exception as e:
            break
    return "AI analysis failed: All API keys are rate-limited or invalid."


# --- NEW: The Main API Endpoint ---

@app.post("/analyze")
async def analyze_github_user(request: AnalyzeRequest):
    username_to_check = request.username
    top_langs = get_user_top_languages(username_to_check)
    
    if not top_langs:
        return {"error": f"Could not determine top languages for user {username_to_check}."}

    for lang in top_langs:
        issues = find_good_first_issues(lang)
        if issues:
            # We found issues, now add AI analysis to each one
            results = []
            for issue in issues:
                ai_reason = get_ai_analysis(issue['title'], issue['body'])
                results.append({
                    "repo_name": issue['repository_url'].split('/')[-2] + '/' + issue['repository_url'].split('/')[-1],
                    "title": issue['title'],
                    "link": issue['html_url'],
                    "ai_reason": ai_reason
                })
            return {"language": lang, "issues": results}
    
    return {"error": "Could not find any suitable issues in the user's top languages."}