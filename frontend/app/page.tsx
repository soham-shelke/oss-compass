'use client';

import { useState } from 'react';
// NEW: Import the motion component from Framer Motion
import { motion } from 'framer-motion';

// Types remain the same
type Issue = {
  repo_name: string;
  title: string;
  link: string;
  ai_reason: string;
};

type ApiResponse = {
  language?: string;
  issues?: Issue[];
  error?: string;
};

// --- NEW: A component for the loading skeleton card ---
const SkeletonCard = () => (
  <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
    <div className="h-4 bg-gray-700 rounded w-1/3 mb-3 animate-pulse"></div>
    <div className="h-6 bg-gray-700 rounded w-full mb-4 animate-pulse"></div>
    <div className="bg-gray-900/70 border border-gray-600 rounded-md p-3">
      <div className="h-4 bg-gray-700 rounded w-full animate-pulse"></div>
    </div>
  </div>
);

export default function HomePage() {
  const [username, setUsername] = useState<string>('');
  const [issues, setIssues] = useState<Issue[]>([]);
  const [language, setLanguage] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  
  // --- NEW: Example usernames to display ---
  const exampleUsernames = ['kennethreitz', 'gaearon', 'sindresorhus', 'yyx990803'];

  // --- UPDATED: The handleAnalyze function can now take an argument ---
  const handleAnalyze = async (userToAnalyze?: string) => {
    const targetUsername = userToAnalyze || username;
    if (!targetUsername) return;

    setIsLoading(true);
    setError('');
    setIssues([]);
    setLanguage('');

    const apiUrl = 'http://127.0.0.1:8000/analyze';

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: targetUsername }),
      });

      if (!response.ok) throw new Error('Network response was not ok');
      const data: ApiResponse = await response.json();

      if (data.error) setError(data.error);
      else if (data.issues && data.language) {
        setIssues(data.issues);
        setLanguage(data.language);
      }
    } catch (err) {
      setError('Failed to fetch data. Is the backend server running?');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // --- NEW: Animation variants for Framer Motion ---
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1, // This makes each child animate one by one
      },
    },
  };
  
  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
    },
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-6 sm:p-12 md:p-24 bg-gray-900 text-white font-sans">
      <div className="w-full max-w-3xl">
        <header className="text-center mb-10">
          <h1 className="text-5xl md:text-6xl font-bold mb-2">OSS Compass 🧭</h1>
          <p className="text-lg md:text-xl text-gray-400">Your AI guide to meaningful open source contributions.</p>
        </header>
        
        {/* UPDATED: Input section with a keypress handler */}
        <div className="flex flex-col sm:flex-row gap-4 mb-4">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            placeholder="Enter a GitHub username..."
            className="flex-grow p-3 bg-gray-800 border border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          />
          <button
            onClick={() => handleAnalyze()}
            disabled={isLoading || !username}
            className="p-3 bg-blue-600 rounded-md font-semibold hover:bg-blue-700 transition-colors disabled:bg-gray-600 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Analyzing...' : 'Find Issues'}
          </button>
        </div>

        {/* NEW: Example usernames */}
        <div className="text-center mb-10">
          <span className="text-gray-400 mr-2">Or try an example:</span>
          {exampleUsernames.map((name) => (
            <button
              key={name}
              onClick={() => {
                setUsername(name);
                handleAnalyze(name);
              }}
              className="text-blue-400 hover:text-blue-300 hover:underline mr-4"
            >
              {name}
            </button>
          ))}
        </div>

        {/* UPDATED: Results section with skeleton loaders and animations */}
        <div className="space-y-6">
          {error && <p className="text-center text-red-400 bg-red-900/50 p-4 rounded-md">{error}</p>}
          
          {isLoading && (
            // Show 5 skeleton cards while loading
            <>
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </>
          )}

          {!isLoading && issues.length > 0 && (
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="space-y-6"
            >
              <div className="text-center bg-gray-800/50 p-4 rounded-md">
                <h2 className="text-2xl font-semibold">
                  Found Issues in <span className="text-blue-400">{language}</span>
                </h2>
              </div>
              
              {issues.map((issue) => (
                <motion.div key={issue.link} variants={itemVariants}>
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-5 transition-transform hover:scale-[1.02] hover:border-blue-500">
                    <h3 className="text-gray-400 text-sm mb-1">{issue.repo_name}</h3>
                    <a href={issue.link} target="_blank" rel="noopener noreferrer" className="text-xl font-semibold text-white hover:underline">
                      {issue.title}
                    </a>
                    <div className="mt-3 bg-gray-900/70 border border-gray-600 rounded-md p-3">
                      <p className="text-gray-300"><span className="font-bold text-blue-400">💡 AI Reason:</span> {issue.ai_reason}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </main>
  );
}