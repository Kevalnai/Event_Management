import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import Button from "../components/ui/Button";
import Field, { inputClass } from "../components/ui/Field";
import Alert from "../components/ui/Alert";
import Blob from "../components/ui/Blob";
import Logo from "../components/ui/Logo";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ identifier: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const from = location.state?.from?.pathname || "/dashboard";

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    const res = await login(form.identifier, form.password);
    setSubmitting(false);
    if (res.ok) navigate(from, { replace: true });
    else setError(res.message);
  }

  return (
    <div className="relative flex min-h-[85vh] items-center justify-center overflow-hidden px-5 py-16">
      <Blob tone="violet" className="-left-20 top-10 h-72 w-72" />
      <Blob tone="coral" className="-right-16 bottom-0 h-72 w-72" />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-sm rounded-3xl bg-white p-8 shadow-lift"
      >
        <Logo className="justify-center" />
        <h1 className="mt-6 text-center font-display text-2xl font-bold text-ink">Welcome back</h1>
        <p className="mt-1 text-center text-sm text-ink-soft">Log in to grab your next ticket.</p>

        <form onSubmit={handleSubmit} className="mt-7 space-y-4">
          <Alert>{error}</Alert>
          <Field label="Email or username">
            <input
              required
              autoFocus
              className={inputClass}
              value={form.identifier}
              onChange={(e) => setForm({ ...form, identifier: e.target.value })}
            />
          </Field>
          <Field label="Password">
            <input
              required
              type="password"
              className={inputClass}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </Field>
          <Button type="submit" disabled={submitting} className="w-full">
            {submitting ? "Logging in…" : "Log in"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-ink-soft">
          New here?{" "}
          <Link to="/register" className="font-semibold text-violet-600 hover:underline">
            Create an account
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
