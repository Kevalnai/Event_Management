const GRADIENTS = [
  "from-violet-500 via-fuchsia-pop to-coral",
  "from-ink via-violet-600 to-fuchsia-pop",
  "from-coral via-fuchsia-pop to-violet-500",
  "from-violet-600 to-lime",
  "from-fuchsia-pop via-coral to-lime",
];

const EMOJI = ["✦", "◈", "✺", "⬡", "◎", "✷"];

function hash(str = "") {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (h << 5) - h + str.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

export function coverFor(seed = "") {
  const h = hash(seed);
  return {
    gradient: GRADIENTS[h % GRADIENTS.length],
    glyph: EMOJI[h % EMOJI.length],
  };
}
