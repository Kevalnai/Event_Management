import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { MapPin } from "lucide-react";
import { formatDateShort, formatPrice, formatTime } from "../../lib/format";
import { coverFor } from "../../lib/cover";
import { isImageUrl } from "../../lib/isUrl";

export default function EventCard({ event, index = 0 }) {
  const { month, day } = formatDateShort(event.start_date);
  const cover = coverFor(event.event_id || event.title);
  const price = formatPrice(event.price, event.currency);
  const hasBanner = isImageUrl(event.banner_url);

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay: (index % 6) * 0.05 }}
    >
      <Link
        to={`/events/${event.event_id}`}
        className="group block overflow-hidden rounded-3xl bg-white shadow-soft transition-all duration-300 hover:-translate-y-1.5 hover:shadow-lift"
      >
        <div
          className={`relative flex h-44 items-center justify-center overflow-hidden bg-gradient-to-br ${cover.gradient}`}
          style={hasBanner ? { backgroundImage: `url(${event.banner_url})`, backgroundSize: "cover", backgroundPosition: "center" } : undefined}
        >
          {!hasBanner && (
            <span className="font-display text-6xl text-white/25 transition-transform duration-500 group-hover:scale-110">
              {cover.glyph}
            </span>
          )}

          <div className="absolute left-3 top-3 flex flex-col items-center justify-center rounded-xl bg-white/95 px-2.5 py-1.5 text-center leading-none shadow-soft backdrop-blur">
            <span className="text-[10px] font-bold tracking-wide text-coral">{month}</span>
            <span className="font-display text-lg font-bold text-ink">{day}</span>
          </div>

          <div className="absolute right-3 top-3 rounded-full bg-ink/85 px-3 py-1 text-xs font-bold text-cream backdrop-blur">
            {price}
          </div>
        </div>

        <div className="space-y-2 p-5">
          <h3 className="font-display text-lg font-bold leading-snug text-ink line-clamp-2">
            {event.title}
          </h3>
          <div className="flex items-center gap-1.5 text-sm text-ink-soft">
            <MapPin size={14} className="shrink-0 text-violet-500" />
            <span className="truncate">{event.venue}</span>
          </div>
          <p className="text-xs font-medium uppercase tracking-wide text-ink-soft/70">
            {formatTime(event.start_date)}
          </p>
        </div>
      </Link>
    </motion.div>
  );
}
