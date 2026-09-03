import { Link } from "react-router-dom";

export default function Logo({ className = "" }) {
  return (
    <Link to="/" className={`group inline-flex items-center gap-2 ${className}`}>
      <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-ink">
        <span className="absolute h-6 w-6 rounded-full border-2 border-violet-400/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-gradient-to-br from-violet-400 via-fuchsia-pop to-coral transition-transform duration-300 group-hover:scale-125" />
      </span>
      <span className="font-display text-xl font-bold tracking-tight text-ink">Ripple</span>
    </Link>
  );
}
