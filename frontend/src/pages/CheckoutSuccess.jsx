import { motion } from "framer-motion";
import { PartyPopper } from "lucide-react";
import Button from "../components/ui/Button";
import Section from "../components/ui/Section";

export default function CheckoutSuccess() {
  return (
    <Section className="flex min-h-[70vh] items-center justify-center py-16 text-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mx-auto max-w-md"
      >
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-coral text-white">
          <PartyPopper size={26} />
        </div>
        <h1 className="mt-6 font-display text-3xl font-bold text-ink">Payment received!</h1>
        <p className="mt-3 text-sm leading-relaxed text-ink-soft">
          You're confirmed. Your ticket QR will appear on your dashboard in just a moment
          once we hear back from Stripe.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Button to="/dashboard">View my tickets</Button>
          <Button to="/events" variant="outline">
            Keep exploring
          </Button>
        </div>
      </motion.div>
    </Section>
  );
}
