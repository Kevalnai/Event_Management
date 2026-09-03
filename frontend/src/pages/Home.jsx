import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Compass,
  Heart,
  MapPin,
  QrCode,
  Search,
  Sparkles,
  Ticket,
} from "lucide-react";
import { api } from "../lib/api";
import Button from "../components/ui/Button";
import Blob from "../components/ui/Blob";
import EventCard from "../components/ui/EventCard";
import Section, { Eyebrow } from "../components/ui/Section";
import Loader from "../components/ui/Loader";

const FALLBACK_CATEGORIES = [
  { name: "Music", glyph: "🎧" },
  { name: "Nightlife", glyph: "🌙" },
  { name: "Workshops", glyph: "🛠️" },
  { name: "Sports", glyph: "🏀" },
  { name: "Food & Drink", glyph: "🍜" },
  { name: "Networking", glyph: "🤝" },
];

const STEPS = [
  {
    icon: Compass,
    title: "Discover",
    copy: "Scroll through rooms actually worth your Saturday — filtered by vibe, not noise.",
  },
  {
    icon: Ticket,
    title: "Reserve",
    copy: "Lock your spot in one tap. Secure checkout, instant confirmation, zero spreadsheets.",
  },
  {
    icon: QrCode,
    title: "Show up",
    copy: "Flash your QR at the door. That's it — you're in.",
  },
];

const TESTIMONIALS = [
  {
    quote: "Found my favorite rooftop series through here. Now it's the only place I check on Fridays.",
    name: "Amara O.",
    role: "Regular attendee",
  },
  {
    quote: "Set up ticketing for our first meetup in ten minutes. Check-in on the day was effortless.",
    name: "Jules P.",
    role: "Event host",
  },
  {
    quote: "The kind of app that makes 'going out' feel curated instead of chaotic.",
    name: "Rhea K.",
    role: "Community organizer",
  },
];

export default function Home() {
  const [events, setEvents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    let alive = true;
    Promise.allSettled([api.get("/events/"), api.get("/events/categories")]).then(
      ([eventsRes, catsRes]) => {
        if (!alive) return;
        if (eventsRes.status === "fulfilled") setEvents(eventsRes.value.data);
        if (catsRes.status === "fulfilled") setCategories(catsRes.value.data);
        setLoading(false);
      }
    );
    return () => {
      alive = false;
    };
  }, []);

  const upcoming = [...events]
    .sort((a, b) => new Date(a.start_date) - new Date(b.start_date))
    .slice(0, 6);

  function handleSearch(e) {
    e.preventDefault();
    navigate(query ? `/events?q=${encodeURIComponent(query)}` : "/events");
  }

  return (
    <div>
      {/* HERO */}
      <div className="relative overflow-hidden">
        <Blob tone="violet" className="-left-24 -top-24 h-96 w-96" />
        <Blob tone="coral" className="-right-32 top-20 h-96 w-96" />
        <div className="absolute inset-0 bg-grain opacity-40" />

        <Section className="relative pb-20 pt-16 sm:pt-24 lg:pb-28">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mx-auto max-w-3xl text-center"
          >
            <span className="inline-flex items-center gap-1.5 rounded-full border border-ink/10 bg-white/70 px-4 py-1.5 text-xs font-bold uppercase tracking-wide text-ink-soft backdrop-blur">
              <Sparkles size={13} className="text-coral" /> Where plans become memories
            </span>

            <h1 className="mt-6 font-display text-5xl font-bold leading-[1.05] tracking-tight text-ink sm:text-6xl lg:text-7xl">
              Find your next
              <span className="block text-gradient">favorite night out.</span>
            </h1>

            <p className="mx-auto mt-6 max-w-xl text-base text-ink-soft sm:text-lg">
              Ripple is where the good ones get discovered — gigs, pop-ups, workshops and
              meetups worth clearing your calendar for. Tap in, secure your spot, show up.
            </p>

            <form
              onSubmit={handleSearch}
              className="mx-auto mt-9 flex max-w-xl items-center gap-2 rounded-full bg-white p-2 shadow-lift"
            >
              <Search size={18} className="ml-3 shrink-0 text-ink-soft" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search events, venues, vibes…"
                className="w-full bg-transparent py-2 text-sm text-ink placeholder:text-ink-soft/60 outline-none"
              />
              <Button type="submit" size="sm" className="shrink-0">
                Search
              </Button>
            </form>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <Button to="/events" variant="dark" size="md">
                Browse events <ArrowRight size={16} />
              </Button>
              <Button to="/create-event" variant="outline" size="md">
                Host your own
              </Button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="mx-auto mt-16 grid max-w-3xl grid-cols-3 gap-4 sm:gap-8"
          >
            {[
              ["4.2k+", "events hosted"],
              ["96%", "would rebook"],
              ["150+", "cities live"],
            ].map(([stat, label]) => (
              <div key={label} className="text-center">
                <p className="font-display text-3xl font-bold text-ink sm:text-4xl">{stat}</p>
                <p className="mt-1 text-xs font-medium uppercase tracking-wide text-ink-soft">
                  {label}
                </p>
              </div>
            ))}
          </motion.div>
        </Section>
      </div>

      {/* CATEGORIES */}
      <Section className="pb-4">
        <div className="scrollbar-thin flex gap-3 overflow-x-auto pb-2">
          {(categories.length ? categories.map((c) => ({ name: c.name, glyph: "✦" })) : FALLBACK_CATEGORIES).map(
            (cat) => (
              <button
                key={cat.name}
                onClick={() => navigate(`/events?q=${encodeURIComponent(cat.name)}`)}
                className="flex shrink-0 items-center gap-2 rounded-full border border-ink/10 bg-white px-5 py-2.5 text-sm font-semibold text-ink transition-all hover:-translate-y-0.5 hover:border-violet-300 hover:shadow-soft"
              >
                <span>{cat.glyph}</span>
                {cat.name}
              </button>
            )
          )}
        </div>
      </Section>

      {/* UPCOMING EVENTS */}
      <Section className="py-16 sm:py-24">
        <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
          <div>
            <Eyebrow>Happening soon</Eyebrow>
            <h2 className="font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
              Fresh drops on Ripple
            </h2>
          </div>
          <Button to="/events" variant="ghost" size="sm">
            View all <ArrowRight size={15} />
          </Button>
        </div>

        {loading ? (
          <Loader full={false} />
        ) : upcoming.length ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {upcoming.map((event, i) => (
              <EventCard key={event.event_id} event={event} index={i} />
            ))}
          </div>
        ) : (
          <EmptyState />
        )}
      </Section>

      {/* HOW IT WORKS */}
      <div className="bg-white py-20 sm:py-28">
        <Section>
          <div className="mb-14 text-center">
            <Eyebrow tone="coral">
              <span className="mx-auto">Ridiculously simple</span>
            </Eyebrow>
            <h2 className="font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
              Three taps between you and the door
            </h2>
          </div>

          <div className="grid gap-8 sm:grid-cols-3">
            {STEPS.map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="relative rounded-3xl bg-cream p-8"
              >
                <span className="font-display text-5xl font-bold text-ink/10">0{i + 1}</span>
                <div className="mt-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-coral text-white">
                  <step.icon size={22} />
                </div>
                <h3 className="mt-5 font-display text-xl font-bold text-ink">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-soft">{step.copy}</p>
              </motion.div>
            ))}
          </div>
        </Section>
      </div>

      {/* TESTIMONIALS */}
      <Section className="py-20 sm:py-28">
        <div className="mb-14 text-center">
          <Eyebrow>Loved by the crowd</Eyebrow>
          <h2 className="font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            People keep coming back
          </h2>
        </div>

        <div className="grid gap-6 sm:grid-cols-3">
          {TESTIMONIALS.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="rounded-3xl bg-white p-7 shadow-soft"
            >
              <Heart className="text-coral" size={20} fill="currentColor" />
              <p className="mt-4 text-sm leading-relaxed text-ink">“{t.quote}”</p>
              <div className="mt-5 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-violet-400 to-coral font-display text-xs font-bold text-white">
                  {t.name[0]}
                </div>
                <div>
                  <p className="text-sm font-bold text-ink">{t.name}</p>
                  <p className="text-xs text-ink-soft">{t.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* HOST CTA */}
      <Section className="pb-20 sm:pb-28">
        <div className="relative overflow-hidden rounded-[2.5rem] bg-ink px-8 py-16 text-center sm:px-16">
          <Blob tone="mix" className="left-1/2 top-0 h-72 w-72 -translate-x-1/2 -translate-y-1/2 opacity-40" />
          <div className="relative">
            <p className="inline-flex items-center gap-1.5 rounded-full bg-cream/10 px-4 py-1.5 text-xs font-bold uppercase tracking-wide text-cream/80">
              <MapPin size={13} /> For hosts
            </p>
            <h2 className="mx-auto mt-5 max-w-2xl font-display text-3xl font-bold text-cream sm:text-4xl">
              Got an idea worth gathering for?
            </h2>
            <p className="mx-auto mt-4 max-w-md text-sm text-cream/60">
              Set up ticketing, manage the guest list, and check people in at the door — all
              from one dashboard.
            </p>
            <Button to="/create-event" variant="lime" size="lg" className="mt-8">
              Start hosting <ArrowRight size={16} />
            </Button>
          </div>
        </div>
      </Section>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-3xl border-2 border-dashed border-ink/10 py-20 text-center">
      <p className="font-display text-xl font-bold text-ink">No events yet — be the first</p>
      <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
        Nothing's live on Ripple right now. Why not host the one you wish existed?
      </p>
      <Button to="/create-event" size="md" className="mt-6">
        Host an event
      </Button>
    </div>
  );
}
