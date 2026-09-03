export default function Loader({ full = true }) {
  return (
    <div className={`flex items-center justify-center ${full ? "min-h-[60vh]" : "py-16"}`}>
      <div className="flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2.5 w-2.5 animate-bounce rounded-full bg-gradient-to-br from-violet-500 to-coral"
            style={{ animationDelay: `${i * 0.12}s` }}
          />
        ))}
      </div>
    </div>
  );
}
