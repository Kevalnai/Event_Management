import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Shield, Trash2, UserPlus, Users } from "lucide-react";
import { api, apiErrorMessage } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { formatDate, formatTime } from "../lib/format";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import Loader from "../components/ui/Loader";
import Alert from "../components/ui/Alert";
import Field, { inputClass } from "../components/ui/Field";
import Section from "../components/ui/Section";

const STATUS_TONE = { confirmed: "lime", pending: "coral", cancelled: "outline" };
const ROLE_TONE = { admin: "coral", staff: "violet", volunteer: "outline" };

// Mirrors the backend's allow-lists (RBACService.require_roles calls in
// events/services.py) so the UI only offers controls the API will accept -
// the server re-checks every one of these independently regardless.
const CAN_VIEW_REGISTRATIONS = ["admin", "staff"];
const CAN_VIEW_ORGANISERS = ["admin", "staff"];
const CAN_MANAGE_ORGANISERS = ["admin"];
const CAN_DELETE_EVENT = ["admin"];
const CAN_CHECK_IN = ["admin", "staff", "volunteer"];

export default function ManageEvent() {
  const { eventId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [event, setEvent] = useState(null);
  const [myRole, setMyRole] = useState(undefined); // undefined = still loading
  const [loading, setLoading] = useState(true);
  const [accessError, setAccessError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    Promise.all([api.get(`/events/${eventId}`), api.get(`/events/${eventId}/my-role`)])
      .then(([eventRes, roleRes]) => {
        if (cancelled) return;
        setEvent(eventRes.data);
        setMyRole(roleRes.data.role);
        if (!roleRes.data.role) {
          setAccessError("You're not an organiser of this event, so there's nothing to manage here.");
        }
      })
      .catch(() => {
        if (!cancelled) setAccessError("This event doesn't exist, or something went wrong loading it.");
      })
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [eventId]);

  if (loading) return <Loader />;

  if (accessError || !event || !myRole) {
    return (
      <Section className="py-24 text-center">
        <AlertTriangle className="mx-auto text-coral" size={32} />
        <p className="mt-4 font-display text-2xl font-bold text-ink">Can't manage this event</p>
        <p className="mt-2 text-sm text-ink-soft">{accessError || "No access."}</p>
        <Button to="/events" className="mt-6">
          Back to events
        </Button>
      </Section>
    );
  }

  return (
    <Section className="py-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to={`/events/${eventId}`} className="text-xs font-semibold text-ink-soft hover:text-ink">
            ← Back to event page
          </Link>
          <h1 className="mt-2 font-display text-3xl font-bold text-ink">{event.title}</h1>
        </div>
        <Badge tone={ROLE_TONE[myRole]}>
          <Shield size={12} /> You're {myRole} here
        </Badge>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {CAN_VIEW_REGISTRATIONS.includes(myRole) && (
            <RegistrationsPanel eventId={eventId} myRole={myRole} />
          )}
          {CAN_VIEW_ORGANISERS.includes(myRole) && (
            <OrganisersPanel eventId={eventId} myRole={myRole} currentUserId={user?.user_id} />
          )}
        </div>

        <div className="space-y-6">
          {CAN_CHECK_IN.includes(myRole) && <ManualCheckInPanel eventId={eventId} />}
          {CAN_DELETE_EVENT.includes(myRole) && (
            <DangerZonePanel eventId={eventId} eventTitle={event.title} onDeleted={() => navigate("/events")} />
          )}
        </div>
      </div>
    </Section>
  );
}

function Panel({ icon: Icon, title, children }) {
  return (
    <div className="rounded-3xl bg-white p-6 shadow-lift">
      <div className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
          <Icon size={16} />
        </div>
        <h2 className="font-display text-lg font-bold text-ink">{title}</h2>
      </div>
      <div className="mt-5">{children}</div>
    </div>
  );
}

function RegistrationsPanel({ eventId, myRole }) {
  const [registrations, setRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [checkingInId, setCheckingInId] = useState(null);

  useEffect(() => {
    api
      .get(`/events/${eventId}/registrations`, { params: { limit: 100 } })
      .then(({ data }) => setRegistrations(data))
      .catch((err) => setError(apiErrorMessage(err, "Couldn't load registrations.")))
      .finally(() => setLoading(false));
  }, [eventId]);

  async function checkIn(registration) {
    setCheckingInId(registration.registration_id);
    try {
      await api.post(`/events/events/${eventId}/checkins/${registration.registration_id}`, {
        gate: "Manage dashboard",
      });
      setRegistrations((rows) =>
        rows.map((r) => (r.registration_id === registration.registration_id ? { ...r, _checkedIn: true } : r))
      );
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't check that attendee in."));
    } finally {
      setCheckingInId(null);
    }
  }

  return (
    <Panel icon={Users} title={`Registrations (${registrations.length})`}>
      <Alert>{error}</Alert>
      {loading ? (
        <Loader full={false} />
      ) : registrations.length === 0 ? (
        <p className="text-sm text-ink-soft">No one has registered yet.</p>
      ) : (
        <div className="-mx-2 overflow-x-auto">
          <table className="w-full min-w-[520px] text-left text-sm">
            <thead>
              <tr className="text-xs font-semibold uppercase tracking-wide text-ink-soft/70">
                <th className="px-2 py-2">Name</th>
                <th className="px-2 py-2">Contact</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Registered</th>
                {CAN_CHECK_IN.includes(myRole) && <th className="px-2 py-2">Check-in</th>}
              </tr>
            </thead>
            <tbody>
              {registrations.map((r) => (
                <tr key={r.registration_id} className="border-t border-ink/5">
                  <td className="px-2 py-3 font-medium text-ink">{r.name}</td>
                  <td className="px-2 py-3 text-ink-soft">
                    <div>{r.email}</div>
                    <div className="text-xs">{r.phone}</div>
                  </td>
                  <td className="px-2 py-3">
                    <Badge tone={STATUS_TONE[r.status] || "outline"}>{r.status}</Badge>
                  </td>
                  <td className="px-2 py-3 text-xs text-ink-soft">{formatDate(r.registered_at)}</td>
                  {CAN_CHECK_IN.includes(myRole) && (
                    <td className="px-2 py-3">
                      {r._checkedIn ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-lime-700">
                          <CheckCircle2 size={14} /> Checked in
                        </span>
                      ) : r.status !== "confirmed" ? (
                        <span className="text-xs text-ink-soft">Not confirmed</span>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={checkingInId === r.registration_id}
                          onClick={() => checkIn(r)}
                        >
                          {checkingInId === r.registration_id ? "…" : "Check in"}
                        </Button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}

function OrganisersPanel({ eventId, myRole, currentUserId }) {
  const [organisers, setOrganisers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState({ email: "", role: "staff" });
  const [granting, setGranting] = useState(false);

  function loadOrganisers() {
    return api.get(`/events/${eventId}/organisers`).then(({ data }) => setOrganisers(data));
  }

  useEffect(() => {
    loadOrganisers()
      .catch((err) => setError(apiErrorMessage(err, "Couldn't load organisers.")))
      .finally(() => setLoading(false));
  }, [eventId]);

  async function handleGrant(e) {
    e.preventDefault();
    setGranting(true);
    setError("");
    setSuccess("");
    try {
      await api.post(`/events/${eventId}/organisers`, { email: form.email, role: form.role });
      setSuccess(`Granted ${form.role} to ${form.email}.`);
      setForm({ email: "", role: "staff" });
      await loadOrganisers();
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't grant that role."));
    } finally {
      setGranting(false);
    }
  }

  return (
    <Panel icon={Shield} title="Organisers">
      <Alert>{error}</Alert>
      {success && <Alert tone="success">{success}</Alert>}

      {loading ? (
        <Loader full={false} />
      ) : (
        <ul className="divide-y divide-ink/5">
          {organisers.map((o) => (
            <li key={o.id} className="flex items-center justify-between py-2.5 text-sm">
              <div>
                <p className="font-medium text-ink">
                  {o.user.username}
                  {o.user_id === currentUserId && <span className="text-ink-soft"> (you)</span>}
                </p>
                <p className="text-xs text-ink-soft">{o.user.email}</p>
              </div>
              <Badge tone={ROLE_TONE[o.role]}>{o.role}</Badge>
            </li>
          ))}
        </ul>
      )}

      {CAN_MANAGE_ORGANISERS.includes(myRole) && (
        <form onSubmit={handleGrant} className="mt-5 space-y-3 border-t border-ink/5 pt-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-ink-soft/70">
            Grant a role by email
          </p>
          <Field label="Email">
            <input
              required
              type="email"
              className={inputClass}
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="teammate@example.com"
            />
          </Field>
          <Field label="Role">
            <select
              className={inputClass}
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
            >
              <option value="staff">Staff</option>
              <option value="volunteer">Volunteer</option>
              <option value="admin">Admin</option>
            </select>
          </Field>
          <Button type="submit" variant="outline" size="sm" disabled={granting} className="w-full">
            <UserPlus size={14} /> {granting ? "Granting…" : "Grant role"}
          </Button>
        </form>
      )}
    </Panel>
  );
}

function ManualCheckInPanel({ eventId }) {
  const [registrationId, setRegistrationId] = useState("");
  const [status, setStatus] = useState(null); // { ok: bool, message: string }
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setStatus(null);
    try {
      await api.post(`/events/events/${eventId}/checkins/${registrationId.trim()}`, {
        gate: "Manual",
      });
      setStatus({ ok: true, message: "Checked in." });
      setRegistrationId("");
    } catch (err) {
      setStatus({ ok: false, message: apiErrorMessage(err, "Couldn't check that registration in.") });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Panel icon={CheckCircle2} title="Manual check-in">
      <p className="text-xs text-ink-soft">
        For when a QR code won't scan - paste the attendee's registration ID instead.
      </p>
      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <Field label="Registration ID">
          <input
            required
            className={inputClass}
            value={registrationId}
            onChange={(e) => setRegistrationId(e.target.value)}
            placeholder="e.g. 3f1c2b9a-…"
          />
        </Field>
        {status && <Alert tone={status.ok ? "success" : "error"}>{status.message}</Alert>}
        <Button type="submit" size="sm" disabled={submitting} className="w-full">
          {submitting ? "Checking in…" : "Check in"}
        </Button>
      </form>
    </Panel>
  );
}

function DangerZonePanel({ eventId, eventTitle, onDeleted }) {
  const [confirming, setConfirming] = useState(false);
  const [typed, setTyped] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  async function handleDelete() {
    setDeleting(true);
    setError("");
    try {
      await api.delete(`/events/events/${eventId}`);
      onDeleted();
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't delete this event."));
      setDeleting(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border-2 border-coral/20 bg-coral-dim/40 p-6"
    >
      <div className="flex items-center gap-2.5 text-coral">
        <Trash2 size={16} />
        <h2 className="font-display text-lg font-bold">Danger zone</h2>
      </div>
      <p className="mt-3 text-xs text-ink-soft">
        Deleting this event permanently removes it along with every registration, payment record,
        ticket, and check-in tied to it. This can't be undone.
      </p>

      <Alert>{error}</Alert>

      {!confirming ? (
        <Button variant="outline" size="sm" className="mt-4 w-full" onClick={() => setConfirming(true)}>
          Delete event
        </Button>
      ) : (
        <div className="mt-4 space-y-3">
          <Field label={`Type "${eventTitle}" to confirm`}>
            <input
              className={inputClass}
              value={typed}
              onChange={(e) => setTyped(e.target.value)}
              autoFocus
            />
          </Field>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => {
                setConfirming(false);
                setTyped("");
              }}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              className="flex-1 !bg-coral !bg-none text-white"
              disabled={typed !== eventTitle || deleting}
              onClick={handleDelete}
            >
              {deleting ? "Deleting…" : "Confirm delete"}
            </Button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
