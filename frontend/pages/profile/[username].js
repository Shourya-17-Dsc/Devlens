import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
} from 'chart.js';
import { Doughnut, Bar, Line } from 'react-chartjs-2';

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement
);

export default function Profile() {
  const router = useRouter();
  const { username } = router.query;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!username) return;

    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`http://localhost:8001/api/v1/analyze/${username}`);
        
        if (response.status === 404) {
          setError(`❌ Invalid GitHub Username: '${username}' does not exist on GitHub. Please check the username and try again.`);
          setLoading(false);
          return;
        }
        
        if (!response.ok) {
          const errorMsg = response.status === 429 
            ? 'GitHub API rate limit exceeded. Please try again later.'
            : `Failed to analyze profile (Error ${response.status})`;
          setError(errorMsg);
          setLoading(false);
          return;
        }
        
        const result = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError(`Error: ${err.message || 'Failed to fetch profile'}`);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [username]);

  if (!username) return <div>Loading...</div>;

  return (
    <>
      <Head>
        <title>{username} - GitHub Skill Analysis</title>
        <meta name="description" content={`Skill analysis for ${username}`} />
      </Head>

      <main className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
          <div className="max-w-6xl mx-auto">
            <Link href="/" className="text-blue-200 hover:text-white mb-4 inline-block">
              ← Back
            </Link>
            <h1 className="text-4xl font-bold">{username}</h1>
            <p className="text-blue-100">GitHub Developer Analysis</p>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-6xl mx-auto p-6">
          {loading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-600 mt-4">Analyzing profile...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border-2 border-red-300 rounded-lg p-8 text-center shadow-sm">
              <div className="text-5xl mb-4">⚠️</div>
              <h2 className="text-2xl font-bold text-red-900 mb-2">Invalid GitHub Username</h2>
              <p className="text-red-800 mb-6 text-lg">{error}</p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={() => router.push('/')}
                  className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold transition"
                >
                  ← Try Another Username
                </button>
                <button
                  onClick={() => router.back()}
                  className="px-6 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 font-semibold transition"
                >
                  Go Back
                </button>
              </div>
            </div>
          )}

          {data && (
            <div className="space-y-6">
              {/* Skill Score Card */}
              <div className="bg-white rounded-lg shadow p-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-900">Skill Score</h2>
                  <span className="text-5xl font-bold text-blue-600">
                    {(data.skill_score * 10).toFixed(1)}
                  </span>
                </div>
                <p className="text-gray-600">ML-powered rating from 0-100 based on GitHub activity</p>
              </div>

              {/* Language Breakdown */}
              {data.language_breakdown && Object.keys(data.language_breakdown).length > 0 && (
                <div className="bg-white rounded-lg shadow p-8">
                  <h3 className="text-xl font-bold text-gray-900 mb-6">Language Breakdown</h3>
                  <div className="grid md:grid-cols-2 gap-8">
                    <div>
                      <Doughnut
                        data={{
                          labels: Object.keys(data.language_breakdown),
                          datasets: [
                            {
                              data: Object.values(data.language_breakdown),
                              backgroundColor: [
                                '#3b82f6',
                                '#10b981',
                                '#f59e0b',
                                '#ef4444',
                                '#8b5cf6',
                              ],
                            },
                          ],
                        }}
                        options={{ responsive: true }}
                      />
                    </div>
                    <div className="flex flex-col justify-center space-y-3">
                      {Object.entries(data.language_breakdown).map(([lang, count]) => (
                        <div key={lang} className="flex justify-between">
                          <span className="font-medium text-gray-700">{lang}</span>
                          <span className="text-gray-600">{count} repos</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Strengths & Weaknesses */}
              {data.strengths_weaknesses && (
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="bg-green-50 rounded-lg shadow p-8 border-l-4 border-green-600">
                    <h3 className="text-xl font-bold text-green-900 mb-4">💪 Strengths</h3>
                    <ul className="space-y-2">
                      {data.strengths_weaknesses.strengths?.map((strength, i) => (
                        <li key={i} className="text-green-800">
                          • {strength}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="bg-yellow-50 rounded-lg shadow p-8 border-l-4 border-yellow-600">
                    <h3 className="text-xl font-bold text-yellow-900 mb-4">⚡ Areas to Grow</h3>
                    <ul className="space-y-2">
                      {data.strengths_weaknesses.weaknesses?.map((weakness, i) => (
                        <li key={i} className="text-yellow-800">
                          • {weakness}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Activity & Stats */}
              {data.code_metrics && (
                <div className="bg-white rounded-lg shadow p-8">
                  <h3 className="text-xl font-bold text-gray-900 mb-6">📊 Key Metrics</h3>
                  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded p-4">
                      <p className="text-gray-600 text-sm">Total Repos</p>
                      <p className="text-3xl font-bold text-blue-600">
                        {data.code_metrics.repo_count}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-green-50 to-green-100 rounded p-4">
                      <p className="text-gray-600 text-sm">Languages</p>
                      <p className="text-3xl font-bold text-green-600">
                        {Object.keys(data.language_breakdown || {}).length}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded p-4">
                      <p className="text-gray-600 text-sm">Activity Level</p>
                      <p className="text-lg font-bold text-purple-600 capitalize">
                        {data.code_metrics.activity_level}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded p-4">
                      <p className="text-gray-600 text-sm">Account Age</p>
                      <p className="text-xl font-bold text-orange-600">
                        {data.code_metrics.account_age_days || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Repositories List */}
              {data.repositories && data.repositories.length > 0 && (
                <div className="bg-white rounded-lg shadow p-8">
                  <h3 className="text-xl font-bold text-gray-900 mb-6">📚 Repositories ({data.repositories.length})</h3>
                  <div className="grid md:grid-cols-2 gap-4">
                    {data.repositories.map((repo, idx) => (
                      <a
                        key={idx}
                        href={repo.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 hover:shadow-lg transition-shadow border border-gray-200"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-semibold text-blue-600 hover:underline text-sm md:text-base">
                            {repo.name}
                          </h4>
                          {repo.language && (
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              {repo.language}
                            </span>
                          )}
                        </div>
                        {repo.description && (
                          <p className="text-gray-700 text-sm mb-3 line-clamp-2">
                            {repo.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span className="flex items-center gap-1">
                            ⭐ {repo.stars > 0 ? repo.stars.toLocaleString() : '0'}
                          </span>
                          <span className="flex items-center gap-1">
                            🔀 {repo.forks > 0 ? repo.forks.toLocaleString() : '0'}
                          </span>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
