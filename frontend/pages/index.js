import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';

export default function Home() {
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [validating, setValidating] = useState(false);

  // GitHub username validation rules
  const validateUsername = (input) => {
    if (!input.trim()) {
      return 'Please enter a GitHub username';
    }
    
    const trimmed = input.trim();
    
    // Check length (GitHub usernames are 1-39 characters)
    if (trimmed.length > 39) {
      return 'Username cannot exceed 39 characters';
    }
    
    // Check if starts or ends with hyphen
    if (trimmed.startsWith('-') || trimmed.endsWith('-')) {
      return 'Username cannot start or end with a hyphen';
    }
    
    // Check for valid characters (alphanumeric and hyphens only)
    if (!/^[a-zA-Z0-9-]+$/.test(trimmed)) {
      return 'Username can only contain letters, numbers, and hyphens';
    }
    
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate format
    const validationError = validateUsername(username);
    if (validationError) {
      setError(validationError);
      return;
    }
    
    // Check if username exists on GitHub
    setValidating(true);
    try {
      const response = await fetch(`http://localhost:8001/api/v1/analyze/${username.trim()}`);
      setValidating(false);
      
      if (response.status === 404) {
        setError('❌ Invalid GitHub username - user not found');
        return;
      }
      
      if (!response.ok) {
        setError('Error checking username. Please try again.');
        return;
      }
      
      // Username is valid, redirect to profile
      window.location.href = `/profile/${username.trim()}`;
    } catch (err) {
      setValidating(false);
      setError('Error validating username. Please try again.');
    }
  };

  return (
    <>
      <Head>
        <title>GitHub Developer Skill Intelligence Platform</title>
        <meta name="description" content="Analyze developer skills from GitHub profiles" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 md:p-12 max-w-md w-full">
          <h1 className="text-4xl font-bold text-center text-gray-900 mb-2">
            🧠 Skill Intelligence
          </h1>
          <p className="text-center text-gray-600 mb-8">
            Analyze GitHub profiles and discover developer skills
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                GitHub Username
              </label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setError('');
                }}
                placeholder="e.g., octocat"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                disabled={validating}
              />
              {error && (
                <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-800 text-sm font-medium">{error}</p>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={validating}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg transition flex items-center justify-center gap-2"
            >
              {validating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Validating...
                </>
              ) : (
                <>
                  Analyze Profile →
                </>
              )}
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3">What you'll see:</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>✨ ML-powered skill score (0-10)</li>
              <li>📊 Language breakdown & expertise</li>
              <li>💪 Technical strengths analysis</li>
              <li>📈 Code complexity metrics</li>
              <li>🔄 Activity level classification</li>
            </ul>
          </div>
        </div>
      </main>
    </>
  );
}
