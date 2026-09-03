export default function Section({ id, className = "", children }) {
  return (
    <section id={id} className={`mx-auto max-w-7xl px-5 sm:px-8 ${className}`}>
      {children}
    </section>
  );
}

export function Eyebrow({ children, tone = "violet" }) {
  const tones = {
    violet: "text-violet-600",
    coral: "text-coral",
  };
  return (
    <p className={`mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] ${tones[tone]}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {children}
    </p>
  );
}
