export default function Field({ label, error, children, hint }) {
  return (
    <label className="block">
      {label && <span className="mb-1.5 block text-sm font-semibold text-ink">{label}</span>}
      {children}
      {hint && !error && <span className="mt-1.5 block text-xs text-ink-soft">{hint}</span>}
      {error && <span className="mt-1.5 block text-xs font-medium text-coral">{error}</span>}
    </label>
  );
}

export const inputClass =
  "w-full rounded-2xl border border-ink/10 bg-white px-4 py-3 text-sm text-ink placeholder:text-ink-soft/50 outline-none transition-all focus:border-violet-400 focus:ring-4 focus:ring-violet-100";
