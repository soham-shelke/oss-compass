import os
import sys
import requests
from dotenv import load_dotenv
from collections import Counter

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# --- Error Handling ---
if not GITHUB_TOKEN:
    raise ValueError("GitHub token not found. Please set GITHUB_TOKEN in your .env file.")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


def get_user_top_languages(username, count=3):
    """
    Fetches a user's repositories and determines their top languages.
    """
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
        print("No public repositories found for this user.")
        return []

    languages = [repo["language"] for repo in repos if repo["language"] is not None]
    if not languages:
        print("No repositories with a specified language.")
        return []

    top_languages = [lang for lang, count in Counter(languages).most_common(count)]
    print(f"-> Top languages found: {', '.join(top_languages)}")
    return top_languages


def find_good_first_issues(language):
    """
    Searches for "good first issue" OR "help wanted" labels for a given language.
    """
    print(f"-> Searching for beginner-friendly issues in {language}...")
    search_url = f"{GITHUB_API_URL}/search/issues"
    
    # CORRECTED QUERY: The extra "q=" at the beginning has been removed.
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
                print(f"{i+1}. [{repo_name}] - {issue['title']}")
                print(f"   Link: {issue['html_url']}\n")
            found_issues = True
            break 
    
    if not found_issues:
        print("\nCould not find any suitable 'good first issues' in the top languages at the moment.")