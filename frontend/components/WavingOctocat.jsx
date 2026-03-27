/**
 * WavingOctocat — Inline SVG GitHub Octocat with a CSS wave animation.
 * No external dependencies, works everywhere.
 */
export default function WavingOctocat({ size = 72, color = '#ffffff' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
      style={{ overflow: 'visible' }}
    >
      <defs>
        <style>{`
          @keyframes octo-wave {
            0%,  60%,  100% { transform: rotate(0deg); }
            10%             { transform: rotate(-15deg); }
            20%             { transform: rotate(12deg); }
            30%             { transform: rotate(-10deg); }
            40%             { transform: rotate(8deg); }
          }
          @keyframes octo-float {
            0%, 100% { transform: translateY(0px); }
            50%      { transform: translateY(-3px); }
          }
          .octo-body  { animation: octo-float 3s ease-in-out infinite; }
          .octo-arm   {
            animation: octo-wave 2.2s ease-in-out infinite;
            transform-origin: 72px 56px;
          }
        `}</style>
      </defs>

      <g className="octo-body">
        {/* ── Cat head ── */}
        <circle cx="50" cy="41" r="19" fill={color} opacity="0.95" />

        {/* ── Ears ── */}
        <polygon points="33,29 37,17 44,28" fill={color} opacity="0.95" />
        <polygon points="67,29 63,17 56,28" fill={color} opacity="0.95" />
        {/* Inner ear tint */}
        <polygon points="35,27 38,20 43,27" fill="#6366f1" opacity="0.4" />
        <polygon points="65,27 62,20 57,27" fill="#6366f1" opacity="0.4" />

        {/* ── Eyes ── */}
        <circle cx="43" cy="41" r="3" fill="#0a0d14" />
        <circle cx="57" cy="41" r="3" fill="#0a0d14" />
        {/* Shine */}
        <circle cx="44.5" cy="39.5" r="1" fill="white" opacity="0.8" />
        <circle cx="58.5" cy="39.5" r="1" fill="white" opacity="0.8" />

        {/* ── Nose & mouth ── */}
        <ellipse cx="50" cy="47" rx="2.5" ry="1.8" fill="#0a0d14" opacity="0.5" />
        <path d="M 47 49 Q 50 52 53 49" stroke="#0a0d14" strokeWidth="1.2" fill="none" opacity="0.4" strokeLinecap="round" />

        {/* ── Body ── */}
        <ellipse cx="50" cy="63" rx="20" ry="13" fill={color} opacity="0.92" />

        {/* ── Left arm (static) ── */}
        <path d="M 31 63 Q 21 68 18 76" stroke={color} strokeWidth="4.5" strokeLinecap="round" fill="none" opacity="0.9" />
        <circle cx="17" cy="77" r="3.5" fill={color} opacity="0.9" />

        {/* ── Tentacles ── */}
        <path d="M 40 74 Q 37 84 39 92" stroke={color} strokeWidth="3.5" strokeLinecap="round" fill="none" opacity="0.85" />
        <path d="M 47 76 Q 45 86 47 93" stroke={color} strokeWidth="3.5" strokeLinecap="round" fill="none" opacity="0.85" />
        <path d="M 54 76 Q 56 86 54 93" stroke={color} strokeWidth="3.5" strokeLinecap="round" fill="none" opacity="0.85" />
        <path d="M 61 74 Q 64 84 62 92" stroke={color} strokeWidth="3.5" strokeLinecap="round" fill="none" opacity="0.85" />
      </g>

      {/* ── Waving arm (animated separately) ── */}
      <g className="octo-arm">
        <path d="M 69 58 Q 80 46 84 38" stroke={color} strokeWidth="4.5" strokeLinecap="round" fill="none" opacity="0.9" />
        <circle cx="85" cy="36" r="4" fill={color} opacity="0.9" />
        {/* Little fingers */}
        <path d="M 85 32 Q 89 28 91 30" stroke={color} strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.75" />
        <path d="M 87 34 Q 92 32 93 35" stroke={color} strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.75" />
      </g>
    </svg>
  );
}
