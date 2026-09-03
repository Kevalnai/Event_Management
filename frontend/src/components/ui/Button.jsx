import { forwardRef } from "react";
import { Link } from "react-router-dom";

const VARIANTS = {
  primary:
    "text-white bg-gradient-to-r from-violet-600 via-fuchsia-pop to-coral shadow-lift hover:brightness-110 hover:-translate-y-0.5",
  dark: "text-cream bg-ink hover:bg-ink/90 hover:-translate-y-0.5",
  outline: "text-ink bg-transparent border-2 border-ink/15 hover:border-ink/40",
  ghost: "text-ink bg-transparent hover:bg-ink/5",
  lime: "text-ink bg-lime hover:brightness-95 hover:-translate-y-0.5",
};

const SIZES = {
  sm: "px-4 py-2 text-sm",
  md: "px-6 py-3 text-sm",
  lg: "px-8 py-4 text-base",
};

const base =
  "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none whitespace-nowrap";

const Button = forwardRef(function Button(
  { as, to, href, variant = "primary", size = "md", className = "", children, ...props },
  ref
) {
  const classes = `${base} ${VARIANTS[variant]} ${SIZES[size]} ${className}`;

  if (to) {
    return (
      <Link to={to} className={classes} {...props}>
        {children}
      </Link>
    );
  }
  if (href) {
    return (
      <a href={href} className={classes} {...props}>
        {children}
      </a>
    );
  }
  return (
    <button ref={ref} className={classes} {...props}>
      {children}
    </button>
  );
});

export default Button;
