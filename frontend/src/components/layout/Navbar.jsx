import { useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Menu, Plus, X } from "lucide-react";
import Logo from "../ui/Logo";
import Button from "../ui/Button";
import { useAuth } from "../../context/AuthContext";
import { initials } from "../../lib/format";

const LINKS = [
  { to: "/events", label: "Explore" },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        scrolled ? "bg-cream/85 shadow-soft backdrop-blur-lg" : "bg-transparent"
      }`}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
        <Logo />

        <div className="hidden items-center gap-8 md:flex">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `text-sm font-semibold transition-colors ${
                  isActive ? "text-ink" : "text-ink-soft hover:text-ink"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
          {user && (
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `text-sm font-semibold transition-colors ${
                  isActive ? "text-ink" : "text-ink-soft hover:text-ink"
                }`
              }
            >
              My tickets
            </NavLink>
          )}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <Button to="/create-event" variant="outline" size="sm">
            <Plus size={16} /> Host an event
          </Button>

          {user ? (
            <div className="relative">
              <button
                onClick={() => setMenuOpen((v) => !v)}
                onBlur={() => setTimeout(() => setMenuOpen(false), 150)}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-ink font-display text-sm font-bold text-cream"
              >
                {initials(user.username) || "U"}
              </button>
              <AnimatePresence>
                {menuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className="absolute right-0 mt-2 w-48 overflow-hidden rounded-2xl bg-white p-1.5 shadow-lift"
                  >
                    <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-ink-soft/70">
                      {user.username}
                    </div>
                    <Link
                      to="/dashboard"
                      className="block rounded-xl px-3 py-2 text-sm font-medium text-ink hover:bg-cream"
                    >
                      Dashboard
                    </Link>
                    <button
                      onClick={() => {
                        logout();
                        navigate("/");
                      }}
                      className="block w-full rounded-xl px-3 py-2 text-left text-sm font-medium text-coral hover:bg-coral-dim"
                    >
                      Log out
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <>
              <Button to="/login" variant="ghost" size="sm">
                Log in
              </Button>
              <Button to="/register" variant="primary" size="sm">
                Sign up free
              </Button>
            </>
          )}
        </div>

        <button
          onClick={() => setOpen((v) => !v)}
          className="flex h-10 w-10 items-center justify-center rounded-full text-ink md:hidden"
          aria-label="Toggle menu"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-ink/5 bg-cream md:hidden"
          >
            <div className="flex flex-col gap-1 px-5 py-4">
              {LINKS.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setOpen(false)}
                  className="rounded-xl px-3 py-2.5 text-sm font-semibold text-ink hover:bg-white"
                >
                  {link.label}
                </Link>
              ))}
              <Link
                to="/create-event"
                onClick={() => setOpen(false)}
                className="rounded-xl px-3 py-2.5 text-sm font-semibold text-ink hover:bg-white"
              >
                Host an event
              </Link>
              {user ? (
                <>
                  <Link
                    to="/dashboard"
                    onClick={() => setOpen(false)}
                    className="rounded-xl px-3 py-2.5 text-sm font-semibold text-ink hover:bg-white"
                  >
                    My tickets
                  </Link>
                  <button
                    onClick={() => {
                      logout();
                      setOpen(false);
                      navigate("/");
                    }}
                    className="rounded-xl px-3 py-2.5 text-left text-sm font-semibold text-coral hover:bg-white"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <div className="mt-2 flex gap-2 px-1">
                  <Button to="/login" variant="outline" size="sm" className="flex-1" onClick={() => setOpen(false)}>
                    Log in
                  </Button>
                  <Button to="/register" variant="primary" size="sm" className="flex-1" onClick={() => setOpen(false)}>
                    Sign up
                  </Button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
