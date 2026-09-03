const TONES = {
  violet: "bg-violet-100 text-violet-600",
  coral: "bg-coral-dim text-coral",
  ink: "bg-ink text-cream",
  lime: "bg-lime text-ink",
  outline: "bg-white text-ink border border-ink/10",
};

export default function Badge({ tone = "violet", className = "", children }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${TONES[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
