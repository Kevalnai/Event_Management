import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import QRCode from "react-qr-code";
import { Calendar, MapPin, Ticket, X } from "lucide-react";
import { api, apiErrorMessage } from "../lib/api";
import { formatDate, formatPrice, formatTime } from "../lib/format";
import { coverFor } from "../lib/cover";
import { isImageUrl } from "../lib/isUrl";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Loader from "../components/ui/Loader";
import Alert from "../components/ui/Alert";
import Section, { Eyebrow } from "../components/ui/Section";
import { useAuth } from "../context/AuthContext";

const STATUS_TONE = { confirmed: "lime", pending: "coral", cancelled: "outline" };

export default function Dashboard() {
  const { user } = useAuth();
  const [registrations, setRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTicket, setActiveTicket] = useState(null);
  const [issuing, setIssuing] = useState(null);

  function load() {
    setLoading(true);
    api
      .get("/events/me/registrations")
      .then(({ data }) => setRegistrations(data))
      .catch(() => setError("Couldn't load your tickets right now."))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function getTicket(registrationId) {
    setIssuing(registrationId);
    try {
      await api.post(`/tickets/${registrationId}`);
      load();
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't issue your ticket."));
    } finally {
      setIssuing(null);
    }
  }

  return (
    <Section className="py-14 sm:py-20">
      <Eyebrow>Your account</Eyebrow>
      <h1 className="font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">
        Hey {user?.username} 👋
      </h1>
      <p className="mt-3 text-ink-soft">Everything you've RSVP'd or bought a ticket for.</p>

      <div className="mt-8">
        <Alert>{error}</Alert>
      </div>

      <div className="mt-6">
        {loading ? (
          <Loader full={false} />
        ) : registrations.length ? (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {registrations.map((r) => (
              <RegistrationCard
                key={r.registration_id}
                registration={r}
                onGetTicket={() => getTicket(r.registration_id)}
                issuing={issuing === r.registration_id}
                onShowQr={() => setActiveTicket(r)}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border-2 border-dashed border-ink/10 py-20 text-center">
            <p className="font-display text-xl font-bold text-ink">No tickets yet</p>
            <p className="mt-2 text-sm text-ink-soft">
              Once you RSVP to something, it'll show up right here.
            </p>
            <Button to="/events" className="mt-6">
              Browse events
            </Button>
          </div>
        )}
      </div>

      <AnimatePresence>
        {activeTicket && (
          <QrModal registration={activeTicket} onClose={() => setActiveTicket(null)} />
        )}
      </AnimatePresence>
    </Section>
  );
}

function RegistrationCard({ registration, onGetTicket, issuing, onShowQr }) {
  const { event, status, ticket } = registration;
  const cover = coverFor(event.event_id || event.title);
  const hasBanner = isImageUrl(event.banner_url);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="overflow-hidden rounded-3xl bg-white shadow-soft"
    >
      <div
        className={`relative flex h-28 items-center justify-center bg-gradient-to-br ${cover.gradient}`}
        style={
          hasBanner
            ? { backgroundImage: `url(${event.banner_url})`, backgroundSize: "cover", backgroundPosition: "center" }
            : undefined
        }
      >
        {!hasBanner && <span className="font-display text-4xl text-white/25">{cover.glyph}</span>}
        <div className="absolute right-3 top-3">
          <Badge tone={STATUS_TONE[status] || "outline"}>{status}</Badge>
        </div>
      </div>

      <div className="space-y-3 p-5">
        <h3 className="font-display text-base font-bold leading-snug text-ink line-clamp-2">
          {event.title}
        </h3>
        <div className="space-y-1.5 text-xs text-ink-soft">
          <p className="flex items-center gap-1.5">
            <Calendar size={13} className="text-violet-500" /> {formatDate(event.start_date)} ·{" "}
            {formatTime(event.start_date)}
          </p>
          <p className="flex items-center gap-1.5">
            <MapPin size={13} className="text-violet-500" /> {event.venue}
          </p>
        </div>

        {status === "pending" ? (
          <Button to={`/checkout/${registration.registration_id}`} size="sm" className="mt-2 w-full">
            Complete payment · {formatPrice(event.price, event.currency)}
          </Button>
        ) : ticket ? (
          <Button onClick={onShowQr} variant="dark" size="sm" className="mt-2 w-full">
            <Ticket size={14} /> View ticket
          </Button>
        ) : status === "confirmed" ? (
          <Button onClick={onGetTicket} disabled={issuing} size="sm" className="mt-2 w-full">
            {issuing ? "Issuing…" : "Get my ticket"}
          </Button>
        ) : null}
      </div>
    </motion.div>
  );
}

function QrModal({ registration, onClose }) {
  const { event, ticket } = registration;
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-ink/60 p-5 backdrop-blur-sm"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.92, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.92, y: 12 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm rounded-3xl bg-white p-7 text-center shadow-lift"
      >
        <button
          onClick={onClose}
          className="ml-auto flex h-8 w-8 items-center justify-center rounded-full text-ink-soft hover:bg-cream"
        >
          <X size={16} />
        </button>
        <p className="text-xs font-bold uppercase tracking-wide text-violet-600">Your ticket</p>
        <h3 className="mt-1 font-display text-xl font-bold text-ink">{event.title}</h3>
        <p className="mt-1 text-xs text-ink-soft">
          {formatDate(event.start_date)} · {event.venue}
        </p>

        <div className="mx-auto mt-6 w-fit rounded-2xl bg-white p-4 shadow-soft ring-1 ring-ink/5">
          <QRCode value={ticket?.qr_code || registration.qr_code} size={168} fgColor="#14121a" />
        </div>
        <p className="mt-4 text-xs text-ink-soft">Show this at the door to check in.</p>
      </motion.div>
    </motion.div>
  );
}
