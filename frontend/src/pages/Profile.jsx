import { useState } from "react";
import { KeyRound, Shield, UserCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import Alert from "../components/ui/Alert";
import Field, { inputClass } from "../components/ui/Field";
import Section, { Eyebrow } from "../components/ui/Section";

export default function Profile() {
  const { user, updateProfile } = useAuth();
  const [form, setForm] = useState({ username: user?.username || "", email: user?.email || "" });
  const [status, setStatus] = useState(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setStatus(null);
    const res = await updateProfile(form);
    setStatus(res.ok ? { ok: true, message: "Profile updated." } : { ok: false, message: res.message });
    setSaving(false);
  }

  if (!user) return null;

  return (
    <Section className="py-14 sm:py-20">
      <Eyebrow>Your account</Eyebrow>
      <h1 className="font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">Profile</h1>
      <p className="mt-3 text-ink-soft">Manage your name, email, and account security.</p>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="rounded-3xl bg-white p-6 shadow-lift sm:p-8">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
                <UserCircle size={16} />
              </div>
              <h2 className="font-display text-lg font-bold text-ink">Account details</h2>
            </div>

            <form onSubmit={handleSubmit} className="mt-5 space-y-4">
              {status && <Alert tone={status.ok ? "success" : "error"}>{status.message}</Alert>}
              <Field label="Username">
                <input
                  required
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
              <Button type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save changes"}
              </Button>
            </form>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-3xl bg-white p-6 shadow-lift">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
                <Shield size={16} />
              </div>
              <h2 className="font-display text-lg font-bold text-ink">Account type</h2>
            </div>
            <div className="mt-4">
              <Badge tone={user.role === "admin" ? "coral" : "outline"}>{user.role}</Badge>
            </div>
            <p className="mt-3 text-xs text-ink-soft">
              {user.role === "admin"
                ? "You have platform-wide admin access."
                : "Event-level permissions (admin/staff/volunteer) are separate from this and granted per event - see any event you organise."}
            </p>
          </div>

          <div className="rounded-3xl bg-white p-6 shadow-lift">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
                <KeyRound size={16} />
              </div>
              <h2 className="font-display text-lg font-bold text-ink">Password</h2>
            </div>
            <p className="mt-3 text-xs text-ink-soft">
              Reset your password by email, the same way as if you were signed out.
            </p>
            <Button to="/forgot-password" variant="outline" size="sm" className="mt-4 w-full">
              Change password
            </Button>
          </div>
        </div>
      </div>
    </Section>
  );
}
