import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import Button from "../components/ui/Button";
import Field, { inputClass } from "../components/ui/Field";
import Alert from "../components/ui/Alert";
import Blob from "../components/ui/Blob";
import Logo from "../components/ui/Logo";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    const res = await register(form.username, form.email, form.password);
    setSubmitting(false);
    if (res.ok) navigate("/dashboard", { replace: true });
    else setError(res.message);
  }

  return (
    <div className="relative flex min-h-[85vh] items-center justify-center overflow-hidden px-5 py-16">
      <Blob tone="mix" className="-left-16 -top-10 h-80 w-80" />
      <Blob tone="coral" className="-right-20 bottom-0 h-72 w-72" />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-sm rounded-3xl bg-white p-8 shadow-lift"
      >
        <Logo className="justify-center" />
        <h1 className="mt-6 text-center font-display text-2xl font-bold text-ink">
          Join the ripple
        </h1>
        <p className="mt-1 text-center text-sm text-ink-soft">
          One account, every event worth showing up for.
        </p>

        <form onSubmit={handleSubmit} className="mt-7 space-y-4">
          <Alert>{error}</Alert>
          <Field label="Username">
            <input
              required
              autoFocus
              className={inputClass}
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
            />
          </Field>
          <Field label="Email">
            <input
              required
              type="email"
              className={inputClass}
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </Field>
          <Field label="Password" hint="At least 8 characters">
            <input
              required
              minLength={8}
              type="password"
              className={inputClass}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </Field>
          <Button type="submit" disabled={submitting} className="w-full">
            {submitting ? "Creating account…" : "Create account"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-ink-soft">
          Already have one?{" "}
          <Link to="/login" className="font-semibold text-violet-600 hover:underline">
            Log in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
