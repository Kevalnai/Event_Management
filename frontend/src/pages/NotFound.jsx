import { Compass } from "lucide-react";
import Button from "../components/ui/Button";
import Blob from "../components/ui/Blob";
import Section from "../components/ui/Section";

export default function NotFound() {
  return (
    <div className="relative flex min-h-[75vh] items-center justify-center overflow-hidden">
      <Blob tone="violet" className="left-1/4 top-1/4 h-72 w-72" />
      <Section className="relative text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-ink text-cream">
          <Compass size={24} />
        </div>
        <p className="mt-6 font-display text-7xl font-bold text-ink/10">404</p>
        <h1 className="-mt-6 font-display text-3xl font-bold text-ink">Nothing to see here</h1>
        <p className="mx-auto mt-3 max-w-sm text-sm text-ink-soft">
          This page wandered off. Let's get you back to something worth attending.
        </p>
        <Button to="/" className="mt-8">
          Take me home
        </Button>
      </Section>
    </div>
  );
}
