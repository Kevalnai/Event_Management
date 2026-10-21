import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { api, apiErrorMessage } from "../lib/api";
import Button from "../components/ui/Button";
import Field, { inputClass } from "../components/ui/Field";
import Alert from "../components/ui/Alert";
import Blob from "../components/ui/Blob";
import Logo from "../components/ui/Logo";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [form, setForm] = useState({
    token: searchParams.get("token") || "",
    password: "",
    confirm: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) {
      setError("Passwords don't match.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/auth/password-reset/confirm", {
        reset_token: form.token,
        new_password: form.password,
      });
      setDone(true);
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't reset your password - the link may have expired."));
    } finally {
      setSubmitting(false);
    }
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
        <h1 className="mt-6 text-center font-display text-2xl font-bold text-ink">Set a new password</h1>

        {done ? (
          <div className="mt-7 space-y-4 text-center">
            <Alert tone="success">Your password has been updated.</Alert>
            <Button onClick={() => navigate("/login")} className="w-full">
              Log in
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-7 space-y-4">
            <Alert>{error}</Alert>
            <Field label="Reset token" hint="Paste the token from your reset email or the dev-mode screen">
              <input
                required
                className={inputClass}
                value={form.token}
                onChange={(e) => setForm({ ...form, token: e.target.value })}
              />
            </Field>
            <Field label="New password">
              <input
                required
                type="password"
                minLength={8}
                className={inputClass}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </Field>
            <Field label="Confirm new password">
              <input
                required
                type="password"
                minLength={8}
                className={inputClass}
                value={form.confirm}
                onChange={(e) => setForm({ ...form, confirm: e.target.value })}
              />
            </Field>
            <Button type="submit" disabled={submitting} className="w-full">
              {submitting ? "Updating…" : "Update password"}
            </Button>
          </form>
        )}

        <p className="mt-6 text-center text-sm text-ink-soft">
          <Link to="/login" className="font-semibold text-violet-600 hover:underline">
            Back to login
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
