import os
import sys
import requests
from dotenv import load_dotenv
from collections import Counter
import google.generativeai as genai
# We need to import the specific exception for rate limiting
from google.api_core import exceptions as google_exceptions

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# --- NEW: Load both Gemini keys into a list ---
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY_PRIMARY"),
    os.getenv("GEMINI_API_KEY_SECONDARY")
]
# Filter out any keys that might be missing
GEMINI_KEYS = [key for key in GEMINI_KEYS if key is not None]

# --- Error Handling ---
if not GITHUB_TOKEN:
    raise ValueError("GitHub token not found. Please set GITHUB_TOKEN in your .env file.")
if not GEMINI_KEYS:
    raise ValueError("No Gemini API keys found. Please set them in your .env file.")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

def get_ai_analysis(issue_title, issue_body):
    """
    Uses the Gemini API to generate a summary, with fallback for multiple API keys.
    """
    if not issue_body:
        issue_body = "No description provided."

    prompt = f"""
    Analyze the following GitHub issue and explain in a single, concise sentence why it is a good first issue for a new open-source contributor.
    Focus on the task's nature (e.g., "documentation update," "simple bug fix," "UI improvement").

    Issue Title: {issue_title}
    Issue Description: {issue_body[:500]}

    Reason:
    """

    for i, key in enumerate(GEMINI_KEYS):
        print(f"--> Attempting AI analysis with key #{i+1}...")
        try:
            genai.configure(api_key=key)
            # --- THIS IS THE FINAL CORRECTED LINE ---
            model = genai.GenerativeModel('models/gemini-pro-latest') 
            response = model.generate_content(prompt)
            return response.text.strip()
        
        except google_exceptions.ResourceExhausted as e:
            print(f"    - Key #{i+1} is rate-limited. Trying next key...")
            continue
        
        except Exception as e:
            print(f"    - An unexpected error occurred with key #{i+1}: {e}")
            break
            
    return "AI analysis failed: All API keys are rate-limited or invalid."


# --- (The rest of your code remains the same) ---

def get_user_top_languages(username, count=3):
    print(f"-> Finding top {count} languages for user: {username}...")
    repos_url = f"{GITHUB_API_URL}/users/{username}/repos?type=owner&sort=updated"
    try:
        response = requests.get(repos_url, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repositories: {e}")
        return []
    repos = response.json()
    if not repos:
        return []
    languages = [repo["language"] for repo in repos if repo["language"] is not None]
    if not languages:
        return []
    top_languages = [lang for lang, count in Counter(languages).most_common(count)]
    print(f"-> Top languages found: {', '.join(top_languages)}")
    return top_languages


def find_good_first_issues(language):
    print(f"-> Searching for beginner-friendly issues in {language}...")
    search_url = f"{GITHUB_API_URL}/search/issues"
    query = f'language:{language} (label:"good first issue" OR label:"help wanted") state:open is:issue'
    params = {"q": query, "sort": "updated", "order": "desc", "per_page": 10}
    try:
        response = requests.get(search_url, headers=HEADERS, params=params)
        if response.status_code == 403:
            print(f"\n!!! ERROR: GitHub API rate limit exceeded. Please wait and try again.\n")
            return None
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error searching for issues: {e}")
        return None
    return response.json().get("items", [])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <github_username>")
        sys.exit(1)

    username_to_check = sys.argv[1]
    top_langs = get_user_top_languages(username_to_check)
    found_issues = False

    if not top_langs:
        print("Could not determine top languages. Exiting.")
        sys.exit(1)

    for lang in top_langs:
        issues = find_good_first_issues(lang)
        if issues:
            print(f"\n--- Top 10 Recommended Issues in {lang} for {username_to_check} ---")
            for i, issue in enumerate(issues):
                repo_name = issue['repository_url'].split('/')[-2] + '/' + issue['repository_url'].split('/')[-1]
                ai_reason = get_ai_analysis(issue['title'], issue['body'])
                print(f"{i+1}. [{repo_name}] - {issue['title']}")
                print(f"   Link: {issue['html_url']}")
                print(f"   💡 AI Reason: {ai_reason}\n")
            found_issues = True
            break 
    
    if not found_issues:
        print("\nCould not find any suitable 'good first issues' in the top languages at the moment.")