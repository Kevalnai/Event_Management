export function formatDate(iso, opts = {}) {
  if (!iso) return "";
  const date = new Date(iso);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    ...opts,
  });
}

export function formatDateShort(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  return {
    month: date.toLocaleDateString("en-US", { month: "short" }).toUpperCase(),
    day: date.toLocaleDateString("en-US", { day: "numeric" }),
  };
}

export function formatTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
}

export function formatPrice(amount, currency = "USD") {
  const value = Number(amount ?? 0);
  if (value <= 0) return "Free";
  try {
    return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(value);
  } catch {
    return `${value.toFixed(2)} ${currency}`;
  }
}

export function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
}
