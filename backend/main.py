import os
import requests
from collections import Counter
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# --- NEW GOOGLE LIBRARY (v1.0+) ---
from google import genai
from google.genai import types

# --- Load Environment ---
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# --- Gemini Setup (3 Keys for Round-Robin) ---
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY_PRIMARY"),
    os.getenv("GEMINI_API_KEY_SECONDARY"),
    os.getenv("GEMINI_API_KEY_TERTIARY")
]
# Filter out empty keys just in case
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

# --- Checks ---
if not GITHUB_TOKEN: 
    print("WARNING: GITHUB_TOKEN not found. GitHub features will fail.")
if not GEMINI_KEYS:
    print("WARNING: No Gemini API keys found. AI features will fail.")
else:
    print(f"INFO: Loaded {len(GEMINI_KEYS)} Gemini API Keys.")

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
GITHUB_API_URL = "https://api.github.com"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    username: str

# --- Helper Functions (GitHub API) ---

def get_user_top_languages(username: str, count: int = 3):
    print(f"-> Finding top {count} languages for user: {username}...")
    try:
        repos_url = f"{GITHUB_API_URL}/users/{username}/repos?type=owner&sort=updated"
        response = requests.get(repos_url, headers=HEADERS)
        response.raise_for_status()
        repos = response.json()
        
        if not repos or not isinstance(repos, list): return []
        
        # Filter out repos without language data
        languages = [repo["language"] for repo in repos if repo.get("language")]
        if not languages: return []
        
        # Count and return top 3
        return [lang for lang, count in Counter(languages).most_common(count)]
    except Exception as e:
        print(f"Error fetching repos: {e}")
        return []

def find_good_first_issues(language: str):
    print(f"-> Searching for beginner-friendly issues in {language}...")
    try:
        search_url = f"{GITHUB_API_URL}/search/issues"
        # Search query: Language + (Good First Issue OR Help Wanted) + Open State
        query = f'language:{language} (label:"good first issue" OR label:"help wanted") state:open is:issue'
        params = {"q": query, "sort": "updated", "order": "desc", "per_page": 5}
        
        response = requests.get(search_url, headers=HEADERS, params=params)
        if response.status_code == 403: 
            print("GitHub Rate Limit Hit for Search API")
            return None
        response.raise_for_status()
        return response.json().get("items", [])
    except Exception as e:
        print(f"Error searching issues: {e}")
        return None

# --- The AI Function (New Google GenAI SDK) ---

def get_ai_analysis(issue_title: str, issue_body: str):
    if not issue_body: issue_body = "No description provided."
    
    prompt = f"""
    Analyze the following GitHub issue and explain in a single, concise sentence why it is a good first issue for a new open-source contributor.
    Focus on the task's nature (e.g., "documentation update," "simple bug fix," "UI improvement").

    Issue Title: {issue_title}
    Issue Description: {issue_body[:500]}

    Reason:
    """

    # Try keys one by one until success
    for i, key in enumerate(GEMINI_KEYS):
        print(f"--> [Gemini] Attempting with Key #{i+1}...")
        try:
            # Initialize client with the current key
            client = genai.Client(api_key=key)
            
            # Call the new API model: gemini-2.5-flash
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()
            
        except Exception as e:
            # If rate limited (429) or other error, print and try next key
            print(f"    x Key #{i+1} Failed: {e}")
            continue 
    
    return "AI Analysis Failed (All Keys Exhausted)"

# --- Main API Endpoint ---

@app.post("/analyze")
async def analyze_github_user(request: AnalyzeRequest):
    username_to_check = request.username
    
    # 1. Get Top Languages
    top_langs = get_user_top_languages(username_to_check)
    if not top_langs:
        return {"error": f"Could not determine top languages for user {username_to_check}."}

    # 2. Find Issues for those languages
    for lang in top_langs:
        issues = find_good_first_issues(lang)
        if issues:
            results = []
            for issue in issues:
                # 3. Use AI to analyze each issue
                ai_reason = get_ai_analysis(issue['title'], issue['body'])
                
                # Parse repo name safely
                repo_name = "Unknown Repo"
                if 'repository_url' in issue:
                    parts = issue['repository_url'].split('/')
                    if len(parts) >= 2:
                        repo_name = f"{parts[-2]}/{parts[-1]}"

                results.append({
                    "repo_name": repo_name,
                    "title": issue['title'],
                    "link": issue['html_url'],
                    "ai_reason": ai_reason
                })
            return {"language": lang, "issues": results}
    
    return {"error": "Could not find any suitable issues."}