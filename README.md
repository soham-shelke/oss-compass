🧭 OSS Compass
OSS Compass is a full-stack web application designed to help new open-source contributors find suitable first issues. It uses AI to analyze a user's GitHub profile and match them with relevant, beginner-friendly tasks.

🔴 Live Demo: https://oss-compass.vercel.app/

(To add a screenshot: take one of your live app, upload it to a site like Imgur, and paste the link here)

✨ Features
Personalized Recommendations: Analyzes a user's public repositories to determine their top 3 programming languages.

Intelligent Issue Finding: Searches GitHub for issues labeled "good first issue" or "help wanted" in the user's top languages.

AI-Powered Analysis: Uses the Google Gemini API to provide a concise, one-sentence summary explaining why each issue is a good match for a newcomer.

Modern UI: A polished, responsive frontend built with Next.js, featuring skeleton loaders and animations for a seamless user experience.

🛠️ Tech Stack
Frontend: Next.js (React), TypeScript, Tailwind CSS, Framer Motion

Backend: Python, FastAPI

AI: Google Gemini API

APIs: GitHub REST API

Deployment: Vercel (Frontend) & Render (Backend)

🚀 Running Locally
Prerequisites
Node.js and npm

Python 3.10+ and pip

Git

1. Clone the Repository
git clone [https://github.com/soham-shelke/oss-compass.git](https://github.com/soham-shelke/oss-compass.git)
cd oss-compass

2. Setup Backend
The backend server provides the data and AI analysis.

# Navigate to the backend folder
cd backend

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create a .env file and add your secret keys
# GITHUB_TOKEN=...
# GEMINI_API_KEY_PRIMARY=...

# Run the server
uvicorn main:app --reload

The API will be running at http://127.0.0.1:8000.

3. Setup Frontend
The frontend is the user-facing website.

# In a new terminal, navigate to the frontend folder
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev

The application will be accessible at http://localhost:3000.