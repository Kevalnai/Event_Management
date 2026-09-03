import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, SlidersHorizontal } from "lucide-react";
import { api } from "../lib/api";
import EventCard from "../components/ui/EventCard";
import Loader from "../components/ui/Loader";
import Section, { Eyebrow } from "../components/ui/Section";

const FILTERS = ["Upcoming", "This week", "Free", "Paid"];

export default function Events() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [activeFilter, setActiveFilter] = useState("Upcoming");

  useEffect(() => {
    api
      .get("/events/")
      .then(({ data }) => setEvents(data))
      .catch(() => setError("Couldn't load events right now. Try again in a moment."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setQuery(searchParams.get("q") || "");
  }, [searchParams]);

  const filtered = useMemo(() => {
    const now = new Date();
    const weekAhead = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

    return events
      .filter((e) => {
        if (!query) return true;
        const haystack = `${e.title} ${e.venue} ${e.description || ""}`.toLowerCase();
        return haystack.includes(query.toLowerCase());
      })
      .filter((e) => {
        const start = new Date(e.start_date);
        if (activeFilter === "This week") return start <= weekAhead;
        if (activeFilter === "Free") return Number(e.price) <= 0;
        if (activeFilter === "Paid") return Number(e.price) > 0;
        return true;
      })
      .sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
  }, [events, query, activeFilter]);

  function handleSubmit(e) {
    e.preventDefault();
    setSearchParams(query ? { q: query } : {});
  }

  return (
    <Section className="py-14 sm:py-20">
      <Eyebrow>Explore</Eyebrow>
      <h1 className="font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">
        Everything happening right now
      </h1>
      <p className="mt-3 max-w-xl text-ink-soft">
        Filter by vibe, price, or just see what's dropping soonest.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 flex items-center gap-2 rounded-full bg-white p-1.5 shadow-soft sm:max-w-md">
        <Search size={17} className="ml-3 shrink-0 text-ink-soft" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search events or venues…"
          className="w-full bg-transparent py-2 text-sm text-ink placeholder:text-ink-soft/60 outline-none"
        />
      </form>

      <div className="mt-5 flex flex-wrap items-center gap-2">
        <SlidersHorizontal size={15} className="mr-1 text-ink-soft" />
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={`rounded-full px-4 py-1.5 text-xs font-bold uppercase tracking-wide transition-colors ${
              activeFilter === f ? "bg-ink text-cream" : "bg-white text-ink-soft hover:text-ink"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="mt-10">
        {loading ? (
          <Loader full={false} />
        ) : error ? (
          <p className="rounded-2xl bg-coral-dim px-5 py-4 text-sm font-medium text-coral">{error}</p>
        ) : filtered.length ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((event, i) => (
              <EventCard key={event.event_id} event={event} index={i} />
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border-2 border-dashed border-ink/10 py-20 text-center">
            <p className="font-display text-xl font-bold text-ink">Nothing matches that search</p>
            <p className="mt-2 text-sm text-ink-soft">Try a different keyword or clear your filters.</p>
          </div>
        )}
      </div>
    </Section>
  );
}
