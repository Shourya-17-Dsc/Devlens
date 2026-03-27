import { useState } from 'react';
import dynamic from 'next/dynamic';
import Head from 'next/head';
import { motion } from 'framer-motion';
import { Github, ArrowRight, Loader2, Sparkles, BarChart2, Activity } from 'lucide-react';
import WavingOctocat from '../components/WavingOctocat';

const Plasma = dynamic(() => import('../components/Plasma'), { ssr: false });

export default function Home() {
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [validating, setValidating] = useState(false);

  const extractUsername = (input) => {
    let val = input.trim();
    if (!val) return '';
    try {
      if (val.includes('github.com')) {
        const urlString = val.startsWith('http') ? val : `https://${val}`;
        const url = new URL(urlString);
        return url.pathname.split('/').filter(Boolean)[0] || val;
      }
    } catch(e) {}
    if (val.includes('github.com/')) {
      return val.split('github.com/')[1].split('/')[0];
    }
    return val;
  };

  const validateUsername = (input) => {
    const trimmed = extractUsername(input);
    if (!trimmed) return 'Please enter a GitHub username or URL';
    if (trimmed.length > 39) return 'Username cannot exceed 39 characters';
    if (trimmed.startsWith('-') || trimmed.endsWith('-')) return 'Username cannot start or end with a hyphen';
    if (!/^[a-zA-Z0-9-]+$/.test(trimmed)) return 'Invalid username or URL format';
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const targetUser = extractUsername(username);
    const validationError = validateUsername(username);
    if (validationError) { setError(validationError); return; }
    setValidating(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/analyze/${targetUser}`);
      if (response.status === 404) { setValidating(false); setError('User not found on GitHub'); return; }
      if (!response.ok) { setValidating(false); setError('Error checking username. Please try again.'); return; }
      window.location.href = `/profile/${targetUser}`;
    } catch (err) {
      setValidating(false);
      setError('Error validating username. Please try again.');
    }
  };

  const containerVariants = {
    hidden: { opacity: 0, y: 40, scale: 0.95 },
    visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1], staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } }
  };

  return (
    <>
      <Head>
        <title>Devlens - GitHub Skill Intelligence</title>
        <meta name="description" content="Premium GitHub Developer Skill Intelligence" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <main className="relative min-h-screen overflow-hidden flex items-center justify-center p-4 bg-[#0A0D14]">

        {/* Plasma WebGL Background */}
        <div className="absolute inset-0 z-0" style={{ pointerEvents: 'none' }}>
          <Plasma color="#3b6cf4" speed={0.5} direction="forward" scale={1.0} opacity={0.35} mouseInteractive={true} />
        </div>

        {/* Grid overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none z-0" />

        {/* ✨ Crazy Octocat — fixed, always on top, never clipped */}
        <motion.div
          className="fixed z-50"
          style={{ top: 'calc(50vh - 220px)', right: 'calc(50vw - 330px)' }}
          initial={{ y: -400, rotate: -30, scale: 0.3, opacity: 0 }}
          animate={{ y: 0, rotate: 0, scale: 1, opacity: 1 }}
          transition={{ delay: 0.6, type: 'spring', stiffness: 150, damping: 9, mass: 1 }}
        >
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut', delay: 1.6 }}
            className="relative"
          >
            {/* Glow ring */}
            <div className="absolute inset-0 rounded-full border-2 border-indigo-400/60 animate-ping" style={{ animationDuration: '2.2s' }} />
            {/* Waving Octocat GIF */}
            <motion.img
              src="https://github.githubassets.com/images/mona-loading-default.gif"
              alt="Waving Octocat"
              width={88}
              height={88}
              className="rounded-full drop-shadow-[0_0_28px_rgba(99,102,241,1)]"
              whileHover={{ scale: 1.3, rotate: [0, -15, 15, -8, 0], transition: { duration: 0.5 } }}
            />
            {/* Ground shadow */}
            <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-12 h-2 bg-black/60 rounded-full blur-md" />
          </motion.div>

          {/* Speech bubble */}
          <motion.div
            initial={{ opacity: 0, scale: 0, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ delay: 1.8, type: 'spring', stiffness: 260 }}
            className="absolute -top-11 -left-20 bg-[#181d2e] border border-white/15 text-white text-xs font-bold px-3 py-1.5 rounded-full whitespace-nowrap shadow-2xl pointer-events-none"
          >
            👋 Scan me!
            <span className="absolute -bottom-1.5 right-6 block w-3 h-3 bg-[#181d2e] border-r border-b border-white/15 rotate-45" />
          </motion.div>
        </motion.div>

        <motion.div
          className="relative z-10 w-full max-w-xl"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* ── Octocat + Card wrapper ── */}
          <div className="relative">

            {/* ✨ Crazy Octocat Drops In */}
            <motion.div
              className="absolute -top-14 right-6 z-30"
              initial={{ y: -280, rotate: -25, scale: 0.4, opacity: 0 }}
              animate={{ y: 0, rotate: 0, scale: 1, opacity: 1 }}
              transition={{ delay: 0.5, type: 'spring', stiffness: 160, damping: 9, mass: 1 }}
            >
              <motion.div
                animate={{ y: [0, -9, 0] }}
                transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut', delay: 1.4 }}
                className="relative"
              >
                {/* Glow ring */}
                <div
                  className="absolute inset-0 rounded-full border-2 border-blue-400/50 animate-ping"
                  style={{ animationDuration: '2s' }}
                />
                {/* The animated Octocat GIF */}
                <motion.img
                  src="https://user-images.githubusercontent.com/74038190/212284158-e840e285-664b-44d7-b79b-e264b5e54825.gif"
                  alt="Waving Octocat"
                  width={80}
                  height={80}
                  className="rounded-full drop-shadow-[0_0_24px_rgba(99,102,241,0.9)]"
                  whileHover={{ scale: 1.25, rotate: [0, -12, 12, -6, 0], transition: { duration: 0.4 } }}
                />
                {/* Ground shadow */}
                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-10 h-1.5 bg-black/50 rounded-full blur-md" />
              </motion.div>

              {/* Speech bubble */}
              <motion.div
                initial={{ opacity: 0, scale: 0, y: 8 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ delay: 1.5, type: 'spring', stiffness: 280 }}
                className="absolute -top-10 -left-24 bg-[#1a1f2e] border border-white/10 text-white text-xs font-bold px-3 py-1.5 rounded-full whitespace-nowrap shadow-2xl"
              >
                👋 Scan me!
                {/* Arrow pointing to octocat */}
                <span
                  className="absolute -bottom-1.5 right-5 w-3 h-3 bg-[#1a1f2e] border-r border-b border-white/10 rotate-45"
                  style={{ display: 'block' }}
                />
              </motion.div>
            </motion.div>

            {/* Glassmorphic Card */}
            <div className="bg-[#11141D]/60 backdrop-blur-2xl border border-white/5 rounded-3xl p-8 md:p-12 shadow-[0_0_80px_rgba(0,0,0,0.8)] overflow-hidden relative">

              {/* Inner top glow line */}
              <div className="absolute top-0 left-1/4 right-1/4 h-px bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />

              {/* Waving Octocat logo */}
              <motion.div variants={itemVariants} className="flex justify-center mb-8">
                <motion.div
                  className="h-24 w-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl p-[1px] shadow-2xl relative group cursor-pointer"
                  whileHover={{ scale: 1.08 }}
                  transition={{ type: 'spring', stiffness: 280 }}
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl rounded-3xl" />
                  <div className="h-full w-full bg-[#0A0D14] rounded-3xl flex items-center justify-center relative z-10">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-3xl" />
                    <div className="relative z-10">
                      <WavingOctocat size={70} color="#ffffff" />
                    </div>
                  </div>
                </motion.div>
              </motion.div>

              {/* Heading */}
              <motion.div variants={itemVariants} className="text-center mb-10">
                <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-4">
                  Dev<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">lens</span>
                </h1>
                <p className="text-slate-400 text-lg font-medium leading-relaxed max-w-sm mx-auto">
                  Decode developer DNA with advanced ML-powered GitHub telemetry.
                </p>
              </motion.div>

              {/* Form */}
              <motion.form variants={itemVariants} onSubmit={handleSubmit} className="space-y-6">
                <div className="relative group">
                  <div className="absolute inset-x-0 -bottom-px h-px w-full bg-gradient-to-r from-transparent via-blue-500/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none">
                    <Github className="h-5 w-5 text-slate-500 group-focus-within:text-blue-400 transition-colors duration-300" />
                  </div>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => { setUsername(e.target.value); setError(''); }}
                    placeholder="GitHub username or URL..."
                    className="w-full pl-14 pr-4 py-5 bg-[#0A0D14]/80 border border-white/5 rounded-2xl outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all placeholder:text-slate-600 text-white font-medium text-lg shadow-inner"
                    disabled={validating}
                  />
                </div>

                {error && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-center backdrop-blur-sm"
                  >
                    <p className="text-red-400 text-sm font-medium">{error}</p>
                  </motion.div>
                )}

                <button
                  type="submit"
                  disabled={validating || !username.trim()}
                  className="group w-full relative h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl overflow-hidden transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] hover:shadow-[0_0_40px_rgba(59,130,246,0.4)]"
                >
                  <div className="absolute inset-0 bg-white/20 mix-blend-overlay opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="relative h-full flex items-center justify-center gap-3 text-white font-bold text-lg tracking-wide">
                    {validating ? (
                      <>
                        <Loader2 className="w-6 h-6 animate-spin text-white/80" />
                        <span className="text-white/90">Analyzing Repository...</span>
                      </>
                    ) : (
                      <>
                        <span>Initiate Scan</span>
                        <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                      </>
                    )}
                  </div>
                </button>
              </motion.form>

            </div>
            {/* end glassmorphic card */}

          </div>
          {/* end octocat + card wrapper */}

          {/* Feature pills */}
          <motion.div variants={itemVariants} className="mt-12 grid grid-cols-3 gap-4 border-t border-white/10 pt-8">
            <div className="flex flex-col items-center text-center gap-3">
              <div className="p-3 bg-blue-500/10 rounded-2xl text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
                <Sparkles className="w-6 h-6" />
              </div>
              <span className="text-xs font-semibold tracking-wide text-slate-400 uppercase">ML Scoring</span>
            </div>
            <div className="flex flex-col items-center text-center gap-3">
              <div className="p-3 bg-purple-500/10 rounded-2xl text-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.2)]">
                <BarChart2 className="w-6 h-6" />
              </div>
              <span className="text-xs font-semibold tracking-wide text-slate-400 uppercase">Deep Stats</span>
            </div>
            <div className="flex flex-col items-center text-center gap-3">
              <div className="p-3 bg-cyan-500/10 rounded-2xl text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.2)]">
                <Activity className="w-6 h-6" />
              </div>
              <span className="text-xs font-semibold tracking-wide text-slate-400 uppercase">Code Health</span>
            </div>
          </motion.div>

        </motion.div>
      </main>
    </>
  );
}
