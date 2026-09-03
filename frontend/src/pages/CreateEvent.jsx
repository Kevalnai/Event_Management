import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { CalendarPlus, Plus } from "lucide-react";
import { api, apiErrorMessage } from "../lib/api";
import Button from "../components/ui/Button";
import Field, { inputClass } from "../components/ui/Field";
import Alert from "../components/ui/Alert";
import Section, { Eyebrow } from "../components/ui/Section";

const EMPTY = {
  title: "",
  description: "",
  category_id: "",
  venue: "",
  address: "",
  start_date: "",
  end_date: "",
  price: "0",
  currency: "USD",
  banner_url: "",
};

export default function CreateEvent() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [newCategory, setNewCategory] = useState("");
  const [addingCategory, setAddingCategory] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function loadCategories() {
    api.get("/events/categories").then(({ data }) => setCategories(data));
  }

  useEffect(loadCategories, []);

  async function handleAddCategory() {
    if (!newCategory.trim()) return;
    setAddingCategory(true);
    try {
      const { data } = await api.post("/events/categories", { name: newCategory.trim() });
      setCategories((prev) => [...prev, data]);
      setForm((f) => ({ ...f, category_id: data.category_id }));
      setNewCategory("");
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't create that category."));
    } finally {
      setAddingCategory(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const { data } = await api.post("/events/events", {
        ...form,
        price: Number(form.price) || 0,
        start_date: new Date(form.start_date).toISOString(),
        end_date: new Date(form.end_date).toISOString(),
        banner_url: form.banner_url || null,
      });
      navigate(`/events/${data.event_id}`);
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't create your event. Check the fields and try again."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Section className="py-14 sm:py-20">
      <div className="mx-auto max-w-2xl">
        <Eyebrow>For hosts</Eyebrow>
        <h1 className="font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">
          Host something people will remember
        </h1>
        <p className="mt-3 text-ink-soft">
          Fill in the essentials — you're automatically made the event's admin, so you can
          add sessions, organisers and check people in afterward.
        </p>

        <motion.form
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleSubmit}
          className="mt-8 space-y-5 rounded-3xl bg-white p-6 shadow-lift sm:p-8"
        >
          <Alert>{error}</Alert>

          <Field label="Event title">
            <input
              required
              className={inputClass}
              placeholder="Rooftop Sunset Sessions"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </Field>

          <Field label="Description" hint="What makes this worth showing up for?">
            <textarea
              rows={4}
              className={inputClass}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </Field>

          <Field label="Category">
            <div className="flex flex-wrap gap-2">
              {categories.map((c) => (
                <button
                  type="button"
                  key={c.category_id}
                  onClick={() => setForm({ ...form, category_id: c.category_id })}
                  className={`rounded-full px-4 py-2 text-xs font-bold transition-colors ${
                    form.category_id === c.category_id
                      ? "bg-ink text-cream"
                      : "bg-cream text-ink-soft hover:text-ink"
                  }`}
                >
                  {c.name}
                </button>
              ))}
            </div>
            <div className="mt-2.5 flex gap-2">
              <input
                className={inputClass}
                placeholder="New category…"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
              />
              <Button type="button" variant="outline" size="sm" onClick={handleAddCategory} disabled={addingCategory}>
                <Plus size={15} />
              </Button>
            </div>
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Starts">
              <input
                required
                type="datetime-local"
                className={inputClass}
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
              />
            </Field>
            <Field label="Ends">
              <input
                required
                type="datetime-local"
                className={inputClass}
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
              />
            </Field>
          </div>

          <Field label="Venue name">
            <input
              required
              className={inputClass}
              placeholder="The Attic"
              value={form.venue}
              onChange={(e) => setForm({ ...form, venue: e.target.value })}
            />
          </Field>

          <Field label="Address">
            <input
              required
              className={inputClass}
              placeholder="123 Main St, City"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
            />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Price" hint="0 for a free event">
              <input
                required
                type="number"
                min="0"
                step="0.01"
                className={inputClass}
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
              />
            </Field>
            <Field label="Currency">
              <select
                className={inputClass}
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value })}
              >
                {["USD", "EUR", "GBP", "INR", "CAD"].map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <Field label="Banner image URL" hint="Optional — leave blank for an auto-generated cover">
            <input
              className={inputClass}
              placeholder="https://…"
              value={form.banner_url}
              onChange={(e) => setForm({ ...form, banner_url: e.target.value })}
            />
          </Field>

          <Button type="submit" disabled={submitting || !form.category_id} className="w-full">
            <CalendarPlus size={16} /> {submitting ? "Publishing…" : "Publish event"}
          </Button>
          {!form.category_id && (
            <p className="text-center text-xs text-ink-soft">Pick or add a category to continue.</p>
          )}
        </motion.form>
      </div>
    </Section>
  );
}
