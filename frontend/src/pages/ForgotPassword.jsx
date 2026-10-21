import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { api, apiErrorMessage } from "../lib/api";
import Button from "../components/ui/Button";
import Field, { inputClass } from "../components/ui/Field";
import Alert from "../components/ui/Alert";
import Blob from "../components/ui/Blob";
import Logo from "../components/ui/Logo";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(null); // { devToken?: string }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const { data } = await api.post("/auth/password-reset/request", { email });
      setSent({ devToken: data.reset_token || null });
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't send a reset link."));
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
        <h1 className="mt-6 text-center font-display text-2xl font-bold text-ink">Reset your password</h1>
        <p className="mt-1 text-center text-sm text-ink-soft">
          Enter your email and we'll send you a link to reset it.
        </p>

        {sent ? (
          <div className="mt-7 space-y-4">
            <Alert tone="success">
              If an account exists for that email, a reset link has been sent.
            </Alert>
            {sent.devToken && (
              <div className="rounded-2xl border-2 border-dashed border-violet-200 bg-violet-50 p-4 text-xs text-ink">
                <p className="font-bold uppercase tracking-wide text-violet-600">Dev mode only</p>
                <p className="mt-1 text-ink-soft">
                  No email provider is wired up yet, so here's your reset token directly:
                </p>
                <code className="mt-2 block break-all rounded-lg bg-white px-2 py-1.5 text-[11px]">
                  {sent.devToken}
                </code>
                <Button
                  size="sm"
                  className="mt-3 w-full"
                  onClick={() => navigate(`/reset-password?token=${encodeURIComponent(sent.devToken)}`)}
                >
                  Continue to reset
                </Button>
              </div>
            )}
            <Link to="/login" className="block text-center text-sm font-semibold text-violet-600 hover:underline">
              Back to login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-7 space-y-4">
            <Alert>{error}</Alert>
            <Field label="Email">
              <input
                required
                autoFocus
                type="email"
                className={inputClass}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Field>
            <Button type="submit" disabled={submitting} className="w-full">
              {submitting ? "Sending…" : "Send reset link"}
            </Button>
            <Link to="/login" className="block text-center text-sm font-semibold text-ink-soft hover:text-ink">
              Back to login
            </Link>
          </form>
        )}
      </motion.div>
    </div>
  );
}
