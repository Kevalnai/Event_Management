import { AlertCircle, CheckCircle2 } from "lucide-react";

export default function Alert({ tone = "error", children }) {
  if (!children) return null;
  const isError = tone === "error";
  return (
    <div
      className={`flex items-start gap-2.5 rounded-2xl px-4 py-3 text-sm font-medium ${
        isError ? "bg-coral-dim text-coral" : "bg-violet-50 text-violet-600"
      }`}
    >
      {isError ? <AlertCircle size={18} className="mt-0.5 shrink-0" /> : <CheckCircle2 size={18} className="mt-0.5 shrink-0" />}
      <span>{children}</span>
    </div>
  );
}
