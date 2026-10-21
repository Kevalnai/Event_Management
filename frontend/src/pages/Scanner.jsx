import { useEffect, useRef, useState } from "react";
import QrScanner from "qr-scanner";
import { CheckCircle2, Keyboard, ScanLine, XCircle } from "lucide-react";
import { api, apiErrorMessage } from "../lib/api";
import Button from "../components/ui/Button";
import Field, { inputClass } from "../components/ui/Field";
import Loader from "../components/ui/Loader";
import Section, { Eyebrow } from "../components/ui/Section";

// Cooldown after a scan so the same code isn't re-submitted on every frame
// while it's still in view.
const RESCAN_COOLDOWN_MS = 2500;

export default function Scanner() {
  const videoRef = useRef(null);
  const scannerRef = useRef(null);
  const busyRef = useRef(false);

  const [cameraState, setCameraState] = useState("starting"); // starting | ready | denied | unsupported
  const [result, setResult] = useState(null); // { ok, message }
  const [manualCode, setManualCode] = useState("");
  const [manualMode, setManualMode] = useState(false);

  async function submitCode(qrCode) {
    if (busyRef.current) return;
    busyRef.current = true;
    try {
      const { data } = await api.post("/scanner/scan", { qr_code: qrCode, gate: "Scanner" });
      setResult({ ok: true, message: `Checked in - gate ${data.gate || "–"}` });
    } catch (err) {
      setResult({ ok: false, message: apiErrorMessage(err, "Couldn't check this ticket in.") });
    } finally {
      setTimeout(() => {
        busyRef.current = false;
      }, RESCAN_COOLDOWN_MS);
    }
  }

  useEffect(() => {
    if (manualMode) return;
    let cancelled = false;

    QrScanner.hasCamera().then((hasCamera) => {
      if (cancelled) return;
      if (!hasCamera) {
        setCameraState("unsupported");
        return;
      }
      const scanner = new QrScanner(
        videoRef.current,
        (result) => submitCode(result.data),
        { highlightScanRegion: true, highlightCodeOutline: true, maxScansPerSecond: 5 }
      );
      scannerRef.current = scanner;
      scanner
        .start()
        .then(() => !cancelled && setCameraState("ready"))
        .catch(() => !cancelled && setCameraState("denied"));
    });

    return () => {
      cancelled = true;
      scannerRef.current?.stop();
      scannerRef.current?.destroy();
      scannerRef.current = null;
    };
  }, [manualMode]);

  function handleManualSubmit(e) {
    e.preventDefault();
    if (!manualCode.trim()) return;
    submitCode(manualCode.trim());
    setManualCode("");
  }

  return (
    <Section className="py-10">
      <Eyebrow>Door check-in</Eyebrow>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-3xl font-bold text-ink">Scan tickets</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setManualMode((v) => !v);
            setResult(null);
          }}
        >
          <Keyboard size={14} /> {manualMode ? "Use camera instead" : "Enter code manually"}
        </Button>
      </div>
      <p className="mt-2 text-sm text-ink-soft">
        Point the camera at an attendee's ticket QR. You only need to be an organiser of whatever
        event the ticket belongs to - this works across every event you have a role on.
      </p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="overflow-hidden rounded-3xl bg-ink shadow-lift">
          {manualMode ? (
            <form onSubmit={handleManualSubmit} className="flex aspect-video flex-col items-center justify-center gap-4 p-8">
              <ScanLine size={32} className="text-cream/40" />
              <div className="w-full max-w-xs">
                <Field label={<span className="text-cream">Ticket QR code</span>}>
                  <input
                    autoFocus
                    className={inputClass}
                    value={manualCode}
                    onChange={(e) => setManualCode(e.target.value)}
                    placeholder="Paste or type the QR code value"
                  />
                </Field>
              </div>
              <Button type="submit" className="w-full max-w-xs">
                Check in
              </Button>
            </form>
          ) : (
            <div className="relative aspect-video">
              <video ref={videoRef} className="h-full w-full object-cover" muted playsInline />
              {cameraState === "starting" && (
                <div className="absolute inset-0 flex items-center justify-center bg-ink">
                  <Loader full={false} />
                </div>
              )}
              {cameraState === "denied" && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-ink p-6 text-center text-cream">
                  <XCircle size={28} className="text-coral" />
                  <p className="text-sm font-semibold">Camera access was denied</p>
                  <p className="text-xs text-cream/60">
                    Allow camera access in your browser, or use manual entry instead.
                  </p>
                </div>
              )}
              {cameraState === "unsupported" && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-ink p-6 text-center text-cream">
                  <XCircle size={28} className="text-coral" />
                  <p className="text-sm font-semibold">No camera found on this device</p>
                  <p className="text-xs text-cream/60">Use manual entry instead.</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-lift">
          <p className="text-xs font-semibold uppercase tracking-wide text-ink-soft/70">Last scan</p>
          {result ? (
            <div
              className={`mt-3 flex items-start gap-2.5 rounded-2xl px-4 py-3 text-sm font-medium ${
                result.ok ? "bg-violet-50 text-violet-600" : "bg-coral-dim text-coral"
              }`}
            >
              {result.ok ? (
                <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
              ) : (
                <XCircle size={18} className="mt-0.5 shrink-0" />
              )}
              <span>{result.message}</span>
            </div>
          ) : (
            <p className="mt-3 text-sm text-ink-soft">Scan a ticket to see the result here.</p>
          )}
        </div>
      </div>
    </Section>
  );
}
