import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Calendar, Clock, MapPin, Settings, Share2, Ticket, Users } from "lucide-react";
import { api, apiErrorMessage } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { formatDate, formatPrice, formatTime } from "../lib/format";
import { coverFor } from "../lib/cover";
import { isImageUrl } from "../lib/isUrl";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import Loader from "../components/ui/Loader";
import Alert from "../components/ui/Alert";
import Field, { inputClass } from "../components/ui/Field";
import Section from "../components/ui/Section";

export default function EventDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [myRole, setMyRole] = useState(null);

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", phone: "" });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    setLoading(true);
    api
      .get(`/events/${id}`)
      .then(({ data }) => setEvent(data))
      .catch(() => setError("This event doesn't exist or was removed."))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (user) {
      setForm({ name: user.username, email: user.email, phone: "" });
    }
  }, [user]);

  useEffect(() => {
    if (!user) {
      setMyRole(null);
      return;
    }
    // Drives whether the "Manage event" link shows - the backend re-checks
    // RBAC on every actual management endpoint regardless of this value.
    api
      .get(`/events/${id}/my-role`)
      .then(({ data }) => setMyRole(data.role))
      .catch(() => setMyRole(null));
  }, [id, user]);

  function openForm() {
    if (!user) {
      navigate("/login", { state: { from: { pathname: `/events/${id}` } } });
      return;
    }
    setShowForm(true);
  }

  async function handleRegister(e) {
    e.preventDefault();
    setSubmitting(true);
    setFormError("");
    try {
      const { data: registration } = await api.post(`/events/${id}/register`, form);

      if (registration.status === "confirmed") {
        // Free event - no payment step needed.
        setSuccess(registration);
        setShowForm(false);
      } else {
        navigate(`/checkout/${registration.registration_id}`);
      }
    } catch (err) {
      setFormError(apiErrorMessage(err, "Couldn't complete your registration."));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <Loader />;
  if (error || !event) {
    return (
      <Section className="py-24 text-center">
        <p className="font-display text-2xl font-bold text-ink">{error}</p>
        <Button to="/events" className="mt-6">
          Back to events
        </Button>
      </Section>
    );
  }

  const cover = coverFor(event.event_id || event.title);
  const price = formatPrice(event.price, event.currency);
  const isFree = Number(event.price) <= 0;
  const hasBanner = isImageUrl(event.banner_url);

  return (
    <div>
      <div
        className={`relative flex h-72 items-center justify-center overflow-hidden bg-gradient-to-br sm:h-96 ${cover.gradient}`}
        style={
          hasBanner
            ? { backgroundImage: `url(${event.banner_url})`, backgroundSize: "cover", backgroundPosition: "center" }
            : undefined
        }
      >
        {!hasBanner && (
          <span className="font-display text-9xl text-white/20">{cover.glyph}</span>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-ink/60 via-transparent to-transparent" />
      </div>

      <Section className="-mt-16 pb-24">
        <div className="grid gap-8 lg:grid-cols-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="lg:col-span-2"
          >
            <div className="rounded-3xl bg-white p-6 shadow-lift sm:p-9">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  {event.category?.name && <Badge tone="violet">{event.category.name}</Badge>}
                  <Badge tone={isFree ? "lime" : "coral"}>{price}</Badge>
                </div>
                {myRole && (
                  <Button to={`/events/${id}/manage`} variant="outline" size="sm">
                    <Settings size={14} /> Manage event
                  </Button>
                )}
              </div>

              <h1 className="mt-4 font-display text-3xl font-bold leading-tight text-ink sm:text-4xl">
                {event.title}
              </h1>

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <InfoRow icon={Calendar} label="Date" value={formatDate(event.start_date)} />
                <InfoRow
                  icon={Clock}
                  label="Time"
                  value={`${formatTime(event.start_date)} – ${formatTime(event.end_date)}`}
                />
                <InfoRow icon={MapPin} label="Venue" value={event.venue} />
                <InfoRow icon={Users} label="Address" value={event.address} />
              </div>

              {event.description && (
                <div className="mt-8 border-t border-ink/5 pt-8">
                  <h2 className="font-display text-lg font-bold text-ink">About this event</h2>
                  <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-ink-soft">
                    {event.description}
                  </p>
                </div>
              )}

              {event.sessions?.length > 0 && (
                <div className="mt-8 border-t border-ink/5 pt-8">
                  <h2 className="font-display text-lg font-bold text-ink">Schedule</h2>
                  <div className="mt-4 space-y-3">
                    {event.sessions.map((s) => (
                      <div
                        key={s.session_id}
                        className="flex items-start gap-4 rounded-2xl bg-cream p-4"
                      >
                        <div className="w-16 shrink-0 text-xs font-bold uppercase text-violet-600">
                          {formatTime(s.start_time)}
                        </div>
                        <div>
                          <p className="text-sm font-bold text-ink">{s.title}</p>
                          <p className="text-xs text-ink-soft">{s.speaker}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="sticky top-24 rounded-3xl bg-white p-6 shadow-lift">
              {success ? (
                <div className="text-center">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-lime">
                    <Ticket size={24} className="text-ink" />
                  </div>
                  <h3 className="mt-4 font-display text-lg font-bold text-ink">You're in! 🎉</h3>
                  <p className="mt-1 text-sm text-ink-soft">
                    Your spot is confirmed. Grab your ticket from your dashboard.
                  </p>
                  <Button to="/dashboard" className="mt-5 w-full">
                    Go to my tickets
                  </Button>
                </div>
              ) : showForm ? (
                <form onSubmit={handleRegister} className="space-y-4">
                  <h3 className="font-display text-lg font-bold text-ink">Confirm your details</h3>
                  <Alert>{formError}</Alert>
                  <Field label="Full name">
                    <input
                      required
                      className={inputClass}
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
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
                  <Field label="Phone">
                    <input
                      required
                      className={inputClass}
                      value={form.phone}
                      onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    />
                  </Field>
                  <Button type="submit" disabled={submitting} className="w-full">
                    {submitting ? "Please wait…" : isFree ? "Confirm free RSVP" : `Continue to pay ${price}`}
                  </Button>
                </form>
              ) : (
                <>
                  <p className="text-xs font-bold uppercase tracking-wide text-ink-soft">
                    Starting at
                  </p>
                  <p className="mt-1 font-display text-4xl font-bold text-ink">{price}</p>
                  <Button onClick={openForm} className="mt-6 w-full">
                    <Ticket size={16} /> {isFree ? "RSVP now" : "Get tickets"}
                  </Button>
                  <button
                    onClick={() => navigator.clipboard?.writeText(window.location.href)}
                    className="mt-3 flex w-full items-center justify-center gap-1.5 text-xs font-semibold text-ink-soft hover:text-ink"
                  >
                    <Share2 size={13} /> Copy link to share
                  </button>
                </>
              )}
            </div>
          </motion.div>
        </div>
      </Section>
    </div>
  );
}

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
        <Icon size={16} />
      </div>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-soft/70">{label}</p>
        <p className="text-sm font-medium text-ink">{value}</p>
      </div>
    </div>
  );
}
