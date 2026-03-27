import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Github,
  Star,
  GitFork,
  BookOpen,
  Activity,
  Calendar,
  Code2,
  BrainCircuit,
  LayoutDashboard,
  FolderDot,
  CheckCircle2,
  AlertTriangle,
  Flame,
  XCircle,
  Loader2
} from 'lucide-react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
} from 'chart.js';
import { Doughnut, Radar } from 'react-chartjs-2';

ChartJS.register(
  ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale,
  RadialLinearScale, PointElement, LineElement, Filler
);

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

export default function Profile() {
  const router = useRouter();
  const { username } = router.query;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (!username) return;

    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`http://localhost:8000/api/v1/analyze/${username}`);
        
        if (response.status === 404) {
          setError(`User '${username}' does not exist on GitHub.`);
          setLoading(false);
          return;
        }
        
        if (!response.ok) {
          setError(response.status === 429 
            ? 'GitHub rate limit exceeded. Please try later.' 
            : `Failed to analyze profile (${response.status})`);
          setLoading(false);
          return;
        }
        
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(`Error: ${err.message || 'Failed to fetch profile'}`);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [username]);

  // utility to convert byte counts into human-readable string
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatAge = (days) => {
    if (!days) return 'N/A';
    if (days < 30) return `${Math.floor(days)}d`;
    if (days < 365) return `${Math.floor(days / 30)}mo`;
    const years = Math.floor(days / 365);
    const remainingMonths = Math.floor((days % 365) / 30);
    return remainingMonths > 0 ? `${years}y ${remainingMonths}m` : `${years}y`;
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'insights', label: 'Insights', icon: BrainCircuit },
    { id: 'repositories', label: 'Repositories', icon: FolderDot },
  ];

  if (!username) return null;

  return (
    <>
      <Head>
        <title>{username} | Devlens</title>
        <meta name="description" content={`Devlens analysis for ${username}`} />
      </Head>

      <main className="min-h-screen bg-[#0A0D14] text-white pb-20 relative overflow-hidden">
        {/* Animated Background */}
        <div className="fixed top-[-20%] left-[-10%] w-[60%] h-[60%] bg-blue-600/20 rounded-full blur-[150px] mix-blend-screen pointer-events-none animate-float" />
        <div className="fixed bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-purple-600/20 rounded-full blur-[150px] mix-blend-screen pointer-events-none animate-float" style={{animationDelay: "4s"}} />
        <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay"></div>

        {/* Header Section */}
        <div className="relative pt-10 pb-24 z-10 border-b border-white/10 bg-[#11141D]/40 backdrop-blur-xl">
          <div className="max-w-6xl mx-auto px-6 relative">
            <Link href="/" className="inline-flex items-center text-slate-400 hover:text-white transition-colors mb-8 group font-medium bg-white/5 py-2 px-4 rounded-full border border-white/5 hover:bg-white/10">
              <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
              Analyze Another User
            </Link>
            
            <div className="flex items-center gap-6">
              <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl p-[1px] shadow-2xl">
                <div className="w-full h-full bg-[#0A0D14] rounded-2xl flex items-center justify-center relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10"></div>
                  {data?.avatar_url ? (
                    <img src={data.avatar_url} alt={username} className="w-full h-full object-cover opacity-90" />
                  ) : (
                    <Github className="w-12 h-12 text-blue-400" />
                  )}
                </div>
              </div>
              <div>
                <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-2">
                  {data?.name || username}
                </h1>
                <div className="flex items-center gap-3 text-slate-400 font-medium tracking-wide">
                  <span className="flex items-center gap-1"><Github className="w-4 h-4 text-slate-500"/> Developer Profile</span>
                  {data?.code_metrics && (
                    <>
                      <span className="text-slate-600">•</span>
                      <span className="capitalize px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-sm">
                        {data.code_metrics.activity_level} Activity
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="max-w-6xl mx-auto px-6 -mt-10 relative z-20">
          
          {loading && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              className="bg-[#11141D]/80 backdrop-blur-2xl border border-white/10 rounded-3xl p-12 flex flex-col items-center justify-center space-y-6 shadow-2xl"
            >
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
              <div className="text-center">
                <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300 mb-2">Decoding Telemetry...</h3>
                <p className="text-slate-400">Running Devlens ML models against {username}</p>
              </div>
            </motion.div>
          )}

          {error && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-[#11141D]/90 backdrop-blur-3xl border border-red-500/20 rounded-3xl p-8 md:p-12 text-center shadow-2xl">
              <div className="w-20 h-20 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-red-500/20 shadow-[0_0_30px_rgba(239,68,68,0.2)]">
                <XCircle className="w-10 h-10 text-red-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-3">Analysis Failed</h2>
              <p className="text-slate-400 mb-8 max-w-lg mx-auto leading-relaxed">{error}</p>
              <div className="flex justify-center gap-4">
                <Link href="/" className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:shadow-[0_0_30px_rgba(59,130,246,0.5)] border border-white/10">
                  Try Another Profile
                </Link>
              </div>
            </motion.div>
          )}

          {data && !loading && !error && (
            <>
              {/* Tab Navigation */}
              <div className="bg-[#11141D]/60 backdrop-blur-xl border border-white/5 rounded-2xl mb-8 p-1.5 flex overflow-x-auto shadow-2xl max-w-fit mx-auto md:mx-0">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-medium transition-all whitespace-nowrap outline-none relative ${
                        activeTab === tab.id
                          ? 'text-white shadow-lg bg-white/10'
                          : 'text-slate-400 hover:text-white hover:bg-white/5'
                      }`}
                  >
                    {activeTab === tab.id && (
                      <motion.div layoutId="activeTab" className="absolute inset-0 bg-blue-500/20 border border-blue-500/30 rounded-xl" />
                    )}
                    <tab.icon className="w-4 h-4 relative z-10" />
                    <span className="relative z-10">{tab.label}</span>
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  variants={containerVariants}
                  initial="hidden"
                  animate="visible"
                  exit={{ opacity: 0, y: -20, transition: { duration: 0.2 } }}
                  className="space-y-6"
                >
                  
                  {/* OVERVIEW TAB */}
                  {activeTab === 'overview' && (
                    <>
                      <div className="grid md:grid-cols-3 gap-6">
                        {/* Score Card */}
                        <motion.div variants={itemVariants} className="md:col-span-1 bg-[#11141D]/80 backdrop-blur-2xl border border-white/10 rounded-3xl p-8 flex flex-col items-center text-center justify-center relative overflow-hidden group shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
                          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                          <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/20 rounded-full blur-[50px] group-hover:bg-blue-400/30 transition-colors duration-500" />
                          <h2 className="text-sm font-bold tracking-widest text-slate-400 uppercase mb-4 z-10 flex items-center gap-2">
                            <Flame className="w-4 h-4 text-orange-400" />
                            Dev Score
                          </h2>
                          <div className="text-8xl font-black text-transparent bg-clip-text bg-gradient-to-br from-blue-400 to-cyan-300 mb-2 z-10 drop-shadow-[0_0_15px_rgba(59,130,246,0.3)]">
                            {(data.skill_score * 10).toFixed(1)}
                          </div>
                          <div className="h-1 w-16 bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full mb-2 z-10 opacity-50"></div>
                          <p className="text-xs text-slate-500 font-bold z-10 tracking-[0.2em] uppercase">Percentile</p>
                        </motion.div>

                        {/* Metrics Grid */}
                        <motion.div variants={itemVariants} className="md:col-span-2 bg-[#11141D]/80 backdrop-blur-2xl border border-white/10 rounded-3xl p-8 grid grid-cols-2 lg:grid-cols-4 gap-8 shadow-[0_8px_32px_rgba(0,0,0,0.5)] relative overflow-hidden">
                          <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent"></div>
                          
                          <div className="space-y-3 relative z-10 group">
                            <div className="flex items-center gap-2 text-slate-400">
                              <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400 group-hover:bg-blue-500/20 transition-colors">
                                <BookOpen className="w-4 h-4" />
                              </div>
                              <span className="text-sm font-semibold tracking-wide">Repositories</span>
                            </div>
                            <div className="text-3xl font-extrabold text-white pl-1">{data.code_metrics.repo_count}</div>
                          </div>
                          
                          <div className="space-y-3 relative z-10 group">
                            <div className="flex items-center gap-2 text-slate-400">
                              <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400 group-hover:bg-purple-500/20 transition-colors">
                                <Code2 className="w-4 h-4" />
                              </div>
                              <span className="text-sm font-semibold tracking-wide">Languages</span>
                            </div>
                            <div className="text-3xl font-extrabold text-white pl-1">
                              {Object.keys(data.language_breakdown || {}).length}
                            </div>
                          </div>
                          
                          <div className="space-y-3 relative z-10 group">
                            <div className="flex items-center gap-2 text-slate-400">
                              <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400 group-hover:bg-emerald-500/20 transition-colors">
                                <Activity className="w-4 h-4" />
                              </div>
                              <span className="text-sm font-semibold tracking-wide">Velocity</span>
                            </div>
                            <div className="text-xl font-extrabold text-white capitalize mt-2 pl-1">
                              {data.code_metrics.activity_level}
                            </div>
                          </div>
                          
                          <div className="space-y-3 relative z-10 group">
                            <div className="flex items-center gap-2 text-slate-400">
                              <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400 group-hover:bg-amber-500/20 transition-colors">
                                <Calendar className="w-4 h-4" />
                              </div>
                              <span className="text-sm font-semibold tracking-wide">Account Age</span>
                            </div>
                            <div className="text-xl font-extrabold text-white mt-2 pl-1 whitespace-nowrap">
                              {formatAge(data.code_metrics.account_age_days)}
                            </div>
                          </div>
                        </motion.div>
                      </div>

                      {/* Languages Doughnut */}
                      {data.language_breakdown && Object.keys(data.language_breakdown).length > 0 && (
                        <motion.div variants={itemVariants} className="bg-[#11141D]/80 backdrop-blur-2xl border border-white/10 rounded-3xl p-8 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
                          <h3 className="text-xl font-bold text-white mb-8 flex items-center gap-3">
                            <Code2 className="w-6 h-6 text-blue-400" />
                            Language Ecosystem
                          </h3>
                          <div className="grid md:grid-cols-2 gap-12 items-center">
                            <div className="aspect-square max-h-72 mx-auto relative flex justify-center">
                              <Doughnut
                                data={{
                                  labels: Object.keys(data.language_breakdown),
                                  datasets: [{
                                    data: Object.values(data.language_breakdown),
                                    backgroundColor: [
                                      '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4'
                                    ],
                                    borderWidth: 0,
                                    hoverOffset: 15,
                                  }],
                                }}
                                options={{
                                  responsive: true,
                                  cutout: '75%',
                                  plugins: {
                                    legend: { display: false }
                                  }
                                }}
                              />
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
                              {Object.entries(data.language_breakdown)
                                .sort((a, b) => b[1] - a[1])
                                .map(([lang, count], i) => (
                                <div key={lang} className="flex justify-between items-center p-3 rounded-2xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                                  <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full shadow-lg" style={{backgroundColor: ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4'][i % 6]}}></div>
                                    <span className="font-semibold text-slate-300">{lang}</span>
                                  </div>
                                  <span className="text-slate-400 font-medium px-2.5 py-1 bg-black/30 rounded-lg text-sm border border-white/5">
                                    {formatBytes(count)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </>
                  )}

                  {/* INSIGHTS TAB */}
                  {activeTab === 'insights' && (
                    <motion.div variants={containerVariants} className="space-y-6">

                      {/* Skill Radar Chart */}
                      {data.radar_scores && (
                        <motion.div variants={itemVariants} className="bg-[#11141D]/80 backdrop-blur-2xl border border-white/10 rounded-3xl p-8 shadow-[0_8px_32px_rgba(0,0,0,0.5)] relative overflow-hidden">
                          <div className="absolute -top-10 -right-10 w-48 h-48 bg-blue-500/10 rounded-full blur-[60px]" />
                          <div className="absolute -bottom-10 -left-10 w-48 h-48 bg-purple-500/10 rounded-full blur-[60px]" />
                          <h3 className="text-xl font-bold text-white mb-8 flex items-center gap-3 relative z-10">
                            <BrainCircuit className="w-6 h-6 text-purple-400" />
                            Skill Radar
                            <span className="ml-2 text-xs font-semibold text-slate-500 bg-white/5 border border-white/10 px-3 py-1 rounded-full tracking-wide">ML-powered analysis</span>
                          </h3>
                          <div className="grid md:grid-cols-2 gap-10 items-center relative z-10">
                            {/* Radar chart */}
                            <div className="max-w-xs mx-auto w-full">
                              <Radar
                                data={{
                                  labels: ['Backend', 'Frontend', 'ML / DS', 'DevOps', 'Testing'],
                                  datasets: [{
                                    label: 'Skill Score',
                                    data: [
                                      data.radar_scores.backend,
                                      data.radar_scores.frontend,
                                      data.radar_scores.machine_learning,
                                      data.radar_scores.devops,
                                      data.radar_scores.testing,
                                    ],
                                    backgroundColor: 'rgba(99, 102, 241, 0.15)',
                                    borderColor: 'rgba(139, 92, 246, 0.8)',
                                    borderWidth: 2,
                                    pointBackgroundColor: 'rgba(167, 139, 250, 1)',
                                    pointBorderColor: '#fff',
                                    pointBorderWidth: 1,
                                    pointRadius: 4,
                                    pointHoverRadius: 6,
                                    fill: true,
                                  }],
                                }}
                                options={{
                                  responsive: true,
                                  scales: {
                                    r: {
                                      min: 0,
                                      max: 100,
                                      ticks: {
                                        stepSize: 25,
                                        color: 'rgba(148,163,184,0.5)',
                                        backdropColor: 'transparent',
                                        font: { size: 10 },
                                      },
                                      grid: { color: 'rgba(255,255,255,0.05)' },
                                      angleLines: { color: 'rgba(255,255,255,0.05)' },
                                      pointLabels: {
                                        color: 'rgba(148,163,184,0.9)',
                                        font: { size: 12, weight: 'bold' },
                                      },
                                    },
                                  },
                                  plugins: { legend: { display: false } },
                                }}
                              />
                            </div>
                            {/* Skill bars */}
                            <div className="space-y-5">
                              {[
                                { key: 'backend',          label: 'Backend Dev',      color: '#3b82f6', glow: 'rgba(59,130,246,0.3)'  },
                                { key: 'frontend',         label: 'Frontend Dev',     color: '#ec4899', glow: 'rgba(236,72,153,0.3)'  },
                                { key: 'machine_learning', label: 'ML / Data Science',color: '#8b5cf6', glow: 'rgba(139,92,246,0.3)'  },
                                { key: 'devops',           label: 'DevOps / Infra',   color: '#10b981', glow: 'rgba(16,185,129,0.3)'  },
                                { key: 'testing',          label: 'Testing / Quality',color: '#f59e0b', glow: 'rgba(245,158,11,0.3)'  },
                              ].map(({ key, label, color, glow }) => {
                                const score = data.radar_scores[key] ?? 0;
                                return (
                                  <div key={key}>
                                    <div className="flex justify-between items-center mb-2">
                                      <span className="text-sm font-semibold text-slate-300">{label}</span>
                                      <span className="text-sm font-bold" style={{ color }}>{score}</span>
                                    </div>
                                    <div className="h-2 bg-white/5 rounded-full overflow-hidden border border-white/5">
                                      <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${score}%` }}
                                        transition={{ duration: 0.8, ease: 'easeOut', delay: 0.1 }}
                                        className="h-full rounded-full"
                                        style={{
                                          background: `linear-gradient(90deg, ${color}99, ${color})`,
                                          boxShadow: `0 0 8px ${glow}`,
                                        }}
                                      />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </motion.div>
                      )}

                      {/* Strengths & Weaknesses */}
                      {data.strengths_weaknesses && (
                        <div className="grid md:grid-cols-2 gap-6">
                          <motion.div variants={itemVariants} className="bg-[#11141D]/80 backdrop-blur-2xl border border-emerald-500/20 rounded-3xl p-8 shadow-[0_0_30px_rgba(16,185,129,0.1)] relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-[40px] group-hover:bg-emerald-500/20 transition-colors duration-500" />
                            <div className="w-14 h-14 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-center mb-6 relative z-10 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
                              <CheckCircle2 className="w-7 h-7 text-emerald-400" />
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-6 relative z-10">Core Strengths</h3>
                            <ul className="space-y-4 relative z-10">
                              {data.strengths_weaknesses.strengths?.map((strength, i) => (
                                <li key={i} className="flex items-start gap-4 p-4 bg-white/5 rounded-2xl border border-white/5 hover:bg-white/10 transition-colors">
                                  <div className="mt-1.5 w-2 h-2 rounded-full bg-emerald-400 shrink-0 shadow-[0_0_10px_rgba(52,211,153,0.8)]" />
                                  <span className="text-slate-300 leading-relaxed font-medium">{strength}</span>
                                </li>
                              ))}
                            </ul>
                          </motion.div>

                          <motion.div variants={itemVariants} className="bg-[#11141D]/80 backdrop-blur-2xl border border-amber-500/20 rounded-3xl p-8 shadow-[0_0_30px_rgba(245,158,11,0.1)] relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/10 rounded-full blur-[40px] group-hover:bg-amber-500/20 transition-colors duration-500" />
                            <div className="w-14 h-14 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex items-center justify-center mb-6 relative z-10 shadow-[0_0_15px_rgba(245,158,11,0.2)]">
                              <AlertTriangle className="w-7 h-7 text-amber-400" />
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-6 relative z-10">Actionable Growth</h3>
                            <ul className="space-y-4 relative z-10">
                              {data.strengths_weaknesses.weaknesses?.map((weakness, i) => (
                                <li key={i} className="flex items-start gap-4 p-4 bg-white/5 rounded-2xl border border-white/5 hover:bg-white/10 transition-colors">
                                  <div className="mt-1.5 w-2 h-2 rounded-full bg-amber-400 shrink-0 shadow-[0_0_10px_rgba(251,191,36,0.8)]" />
                                  <span className="text-slate-300 leading-relaxed font-medium">{weakness}</span>
                                </li>
                              ))}
                            </ul>
                          </motion.div>
                        </div>
                      )}

                    </motion.div>
                  )}

                  {/* REPOSITORIES TAB */}
                  {activeTab === 'repositories' && data.repositories && (
                    <motion.div variants={itemVariants} className="bg-[#11141D]/80 backdrop-blur-2xl border border-white/10 rounded-3xl p-8 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
                      <h3 className="text-xl font-bold text-white mb-8 flex items-center gap-3">
                        <FolderDot className="w-6 h-6 text-blue-400" />
                        Top Repositories <span className="text-slate-500 text-lg font-medium">({data.repositories.length})</span>
                      </h3>
                      <div className="grid md:grid-cols-2 gap-6">
                        {data.repositories.map((repo, idx) => (
                          <a
                            key={idx}
                            href={repo.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-6 rounded-3xl bg-white/5 border border-white/10 hover:border-blue-500/50 hover:bg-white/10 transition-all group relative overflow-hidden"
                          >
                            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-blue-400 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                            <div className="flex justify-between items-start mb-4">
                              <h4 className="font-bold text-lg text-white group-hover:text-blue-400 transition-colors flex items-center gap-2 truncate pr-4">
                                {repo.name}
                              </h4>
                              {repo.language && (
                                <span className="text-xs font-bold tracking-wide bg-blue-500/10 border border-blue-500/20 text-blue-400 px-3 py-1 rounded-full whitespace-nowrap">
                                  {repo.language}
                                </span>
                              )}
                            </div>
                            <p className="text-slate-400 text-sm mb-6 line-clamp-2 leading-relaxed h-10">
                              {repo.description || 'No description provided.'}
                            </p>
                            <div className="flex items-center gap-5 pt-5 border-t border-white/10">
                              <span className="flex items-center gap-1.5 text-sm font-semibold text-amber-400 bg-amber-400/10 border border-amber-400/20 px-3 py-1.5 rounded-lg">
                                <Star className="w-4 h-4" /> {repo.stars.toLocaleString()}
                              </span>
                              <span className="flex items-center gap-1.5 text-sm font-semibold text-slate-300 bg-white/10 border border-white/10 px-3 py-1.5 rounded-lg">
                                <GitFork className="w-4 h-4" /> {repo.forks.toLocaleString()}
                              </span>
                            </div>
                          </a>
                        ))}
                      </div>
                    </motion.div>
                  )}

                </motion.div>
              </AnimatePresence>
            </>
          )}
        </div>
      </main>
    </>
  );
}
