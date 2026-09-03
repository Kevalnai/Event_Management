import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Elements,
  PaymentElement,
  useElements,
  useStripe,
} from "@stripe/react-stripe-js";
import { ShieldCheck } from "lucide-react";
import { api, apiErrorMessage } from "../lib/api";
import { getStripe } from "../lib/stripe";
import { formatPrice } from "../lib/format";
import Button from "../components/ui/Button";
import Alert from "../components/ui/Alert";
import Loader from "../components/ui/Loader";
import Section from "../components/ui/Section";

export default function Checkout() {
  const { registrationId } = useParams();
  const [clientSecret, setClientSecret] = useState(null);
  const [payment, setPayment] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .post("/payments/", { registration_id: registrationId })
      .then(({ data }) => {
        setClientSecret(data.client_secret);
        setPayment(data.payment);
      })
      .catch((err) => setError(apiErrorMessage(err, "Couldn't start checkout for this registration.")))
      .finally(() => setLoading(false));
  }, [registrationId]);

  const appearance = useMemo(
    () => ({
      theme: "stripe",
      variables: {
        colorPrimary: "#7c4dff",
        colorBackground: "#ffffff",
        colorText: "#14121a",
        colorDanger: "#ff6b4a",
        fontFamily: "Manrope, sans-serif",
        borderRadius: "14px",
        spacingUnit: "4px",
      },
    }),
    []
  );

  if (loading) return <Loader />;

  return (
    <Section className="py-16 sm:py-20">
      <div className="mx-auto max-w-lg">
        <p className="text-center text-xs font-bold uppercase tracking-wide text-violet-600">
          Secure checkout
        </p>
        <h1 className="mt-2 text-center font-display text-3xl font-bold text-ink">
          Almost there
        </h1>

        <div className="mt-8 rounded-3xl bg-white p-6 shadow-lift sm:p-8">
          {error ? (
            <>
              <Alert>{error}</Alert>
              <Button to="/events" className="mt-6 w-full">
                Back to events
              </Button>
            </>
          ) : (
            <>
              {payment && (
                <div className="mb-6 flex items-center justify-between rounded-2xl bg-cream px-4 py-3">
                  <span className="text-sm font-medium text-ink-soft">Total due</span>
                  <span className="font-display text-xl font-bold text-ink">
                    {formatPrice(payment.amount, payment.currency)}
                  </span>
                </div>
              )}

              {clientSecret && (
                <Elements stripe={getStripe()} options={{ clientSecret, appearance }}>
                  <PaymentForm registrationId={registrationId} />
                </Elements>
              )}

              <p className="mt-5 flex items-center justify-center gap-1.5 text-xs text-ink-soft">
                <ShieldCheck size={14} /> Payments secured by Stripe
              </p>
            </>
          )}
        </div>
      </div>
    </Section>
  );
}

function PaymentForm({ registrationId }) {
  const stripe = useStripe();
  const elements = useElements();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!stripe || !elements) return;
    setSubmitting(true);
    setError("");

    const { error: confirmError, paymentIntent } = await stripe.confirmPayment({
      elements,
      redirect: "if_required",
    });

    if (confirmError) {
      setError(confirmError.message || "Payment failed. Please try a different method.");
      setSubmitting(false);
      return;
    }

    if (paymentIntent?.status === "succeeded" || paymentIntent?.status === "processing") {
      navigate(`/checkout/${registrationId}/success`);
    } else {
      setError("Payment wasn't completed. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <Alert>{error}</Alert>
      <PaymentElement />
      <Button type="submit" disabled={!stripe || submitting} className="w-full">
        {submitting ? "Processing…" : "Pay now"}
      </Button>
    </form>
  );
}
