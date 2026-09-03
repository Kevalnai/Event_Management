import { AtSign, Globe } from "lucide-react";
import Logo from "../ui/Logo";

export default function Footer() {
  return (
    <footer className="relative overflow-hidden border-t border-ink/5 bg-ink text-cream">
      <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8">
        <div className="grid gap-10 sm:grid-cols-2 md:grid-cols-4">
          <div className="md:col-span-2">
            <Logo className="[&_span:last-child]:text-cream" />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-cream/60">
              The place your next favorite memory starts. Find rooms worth walking into —
              or open the doors yourself.
            </p>
            <div className="mt-6 flex gap-3">
              <a
                href="#"
                className="flex h-10 w-10 items-center justify-center rounded-full bg-cream/10 transition-colors hover:bg-cream/20"
              >
                <AtSign size={16} />
              </a>
              <a
                href="#"
                className="flex h-10 w-10 items-center justify-center rounded-full bg-cream/10 transition-colors hover:bg-cream/20"
              >
                <Globe size={16} />
              </a>
            </div>
          </div>

          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-cream/40">Explore</p>
            <ul className="mt-4 space-y-3 text-sm text-cream/70">
              <li><a href="/events" className="hover:text-cream">Browse events</a></li>
              <li><a href="/create-event" className="hover:text-cream">Host an event</a></li>
              <li><a href="/dashboard" className="hover:text-cream">My tickets</a></li>
            </ul>
          </div>

          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-cream/40">Company</p>
            <ul className="mt-4 space-y-3 text-sm text-cream/70">
              <li><a href="#" className="hover:text-cream">About</a></li>
              <li><a href="#" className="hover:text-cream">Support</a></li>
              <li><a href="#" className="hover:text-cream">Privacy</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-cream/10 pt-6 text-xs text-cream/40 sm:flex-row">
          <p>© {new Date().getFullYear()} Ripple. Made for people who show up.</p>
          <p>Built with React + Tailwind</p>
        </div>
      </div>
    </footer>
  );
}
