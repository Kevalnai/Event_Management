export default function Blob({ className = "", tone = "violet" }) {
  const gradients = {
    violet: "from-violet-400 to-fuchsia-pop",
    coral: "from-coral to-lime",
    mix: "from-violet-500 via-fuchsia-pop to-coral",
  };
  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none absolute rounded-full bg-gradient-to-br ${gradients[tone]} opacity-30 blur-3xl animate-blob ${className}`}
    />
  );
}
