"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getHowToBuy, saveHowToBuy, type HowToBuyContent } from "@/lib/admin-api";
import type { FieldErrors } from "@/lib/admin-settings";
import { t, type TextKey } from "@/lib/texts";
import { cn } from "@/lib/utils";

/** Un tema o una pregunta mientras se edita. `key` solo sirve para que React siga
 * a cada una cuando se ordenan o se borran. */
type Item = { key: number; heading: string; body: string };

type Form = { topics: Item[]; faq: Item[] };

type ListName = keyof Form;

let nextKey = 0;
const newItem = (heading = "", body = ""): Item => ({ key: nextKey++, heading, body });

function toForm(content: HowToBuyContent): Form {
  return {
    topics: content.topics.map((topic) => newItem(topic.title, topic.text)),
    faq: content.faq.map((entry) => newItem(entry.question, entry.answer)),
  };
}

function toBody(form: Form): HowToBuyContent {
  return {
    topics: form.topics.map((item) => ({ title: item.heading, text: item.body })),
    faq: form.faq.map((item) => ({ question: item.heading, answer: item.body })),
  };
}

// Los textos y los nombres de los campos de la API de cada lista.
const LISTS = {
  topics: {
    title: "admin.howToBuy.topics",
    item: "admin.howToBuy.topic",
    heading: "admin.howToBuy.topicTitle",
    body: "admin.howToBuy.topicText",
    add: "admin.howToBuy.addTopic",
    empty: "admin.howToBuy.noTopics",
    headingField: "title",
    bodyField: "text",
  },
  faq: {
    title: "admin.howToBuy.faq",
    item: "admin.howToBuy.faqItem",
    heading: "admin.howToBuy.question",
    body: "admin.howToBuy.answer",
    add: "admin.howToBuy.addQuestion",
    empty: "admin.howToBuy.noQuestions",
    headingField: "question",
    bodyField: "answer",
  },
} satisfies Record<
  ListName,
  Record<"title" | "item" | "heading" | "body" | "add" | "empty", TextKey> &
    Record<"headingField" | "bodyField", string>
>;

type Status = "idle" | "saving" | "saved" | "invalid" | "error";

const textareaClass =
  "w-full resize-y border border-border bg-surface px-3 py-2.5 text-base font-normal text-text focus-visible:border-accent focus-visible:outline-2 focus-visible:outline-primary aria-invalid:border-error";

function FieldError({ id, error }: { id: string; error?: string }) {
  if (!error) return null;
  return (
    <span id={id} className="text-sm font-semibold text-error">
      {error}
    </span>
  );
}

function ItemAction({
  id,
  label,
  item,
  disabled,
  onClick,
}: {
  id?: string;
  label: string;
  item: string;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      id={id}
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={t("admin.howToBuy.itemAction", { action: label, item })}
      className="min-h-9 border border-border bg-bg px-3 text-sm font-semibold hover:border-accent disabled:opacity-40 disabled:hover:border-border"
    >
      {label}
    </button>
  );
}

/** Una lista editable (temas o preguntas): agregar, ordenar con subir y bajar, y borrar. */
function ItemList({
  name,
  items,
  errors,
  onChange,
}: {
  name: ListName;
  items: Item[];
  errors: FieldErrors;
  onChange: (items: Item[]) => void;
}) {
  const texts = LISTS[name];
  // Al agregar, el foco va al título de la nueva; al mover, sigue al botón que se tocó.
  const focusNext = useRef<string | null>(null);

  useEffect(() => {
    if (!focusNext.current) return;
    document.getElementById(focusNext.current)?.focus();
    focusNext.current = null;
  });

  const update = (index: number, changes: Partial<Item>) =>
    onChange(items.map((item, i) => (i === index ? { ...item, ...changes } : item)));

  function move(index: number, offset: -1 | 1, action: "up" | "down") {
    const next = [...items];
    const [item] = next.splice(index, 1);
    next.splice(index + offset, 0, item!);
    const target = index + offset;
    // En el borde, el botón queda apagado: el foco pasa al otro.
    const edge = target === 0 || target === items.length - 1;
    focusNext.current = `${name}-${item!.key}-${edge ? (action === "up" ? "down" : "up") : action}`;
    onChange(next);
  }

  function add() {
    const item = newItem();
    focusNext.current = `${name}-${item.key}-heading`;
    onChange([...items, item]);
  }

  function remove(index: number) {
    const rest = items.filter((_, i) => i !== index);
    // El foco va al título de la que quedó en su lugar, o a «Agregar».
    const neighbor = rest[Math.min(index, rest.length - 1)];
    focusNext.current = neighbor ? `${name}-${neighbor.key}-heading` : `${name}-add`;
    onChange(rest);
  }

  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-display text-xl font-bold uppercase">{t(texts.title)}</h3>
      {items.length === 0 && <p className="text-sm text-muted">{t(texts.empty)}</p>}
      <ol className="flex flex-col gap-4">
        {items.map((item, index) => {
          const legend = t(texts.item, { n: String(index + 1) });
          const id = `${name}-${item.key}`;
          const headingError = errors[`${name}.${index}.${texts.headingField}`];
          const bodyError = errors[`${name}.${index}.${texts.bodyField}`];
          return (
            <li key={item.key}>
              <fieldset className="flex flex-col gap-3 border border-border p-4">
                <legend className="px-1 text-sm font-semibold text-muted">{legend}</legend>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`${id}-heading`}>{t(texts.heading)}</Label>
                  <Input
                    id={`${id}-heading`}
                    value={item.heading}
                    onChange={(event) => update(index, { heading: event.target.value })}
                    aria-invalid={headingError ? true : undefined}
                    aria-describedby={headingError ? `${id}-heading-error` : undefined}
                  />
                  <FieldError id={`${id}-heading-error`} error={headingError} />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`${id}-body`}>{t(texts.body)}</Label>
                  <textarea
                    id={`${id}-body`}
                    rows={3}
                    value={item.body}
                    onChange={(event) => update(index, { body: event.target.value })}
                    aria-invalid={bodyError ? true : undefined}
                    aria-describedby={bodyError ? `${id}-body-error` : undefined}
                    className={textareaClass}
                  />
                  <FieldError id={`${id}-body-error`} error={bodyError} />
                </div>
                <div className="flex flex-wrap gap-2">
                  <ItemAction
                    id={`${id}-up`}
                    label={t("admin.howToBuy.moveUp")}
                    item={legend}
                    disabled={index === 0}
                    onClick={() => move(index, -1, "up")}
                  />
                  <ItemAction
                    id={`${id}-down`}
                    label={t("admin.howToBuy.moveDown")}
                    item={legend}
                    disabled={index === items.length - 1}
                    onClick={() => move(index, 1, "down")}
                  />
                  <ItemAction
                    label={t("admin.howToBuy.remove")}
                    item={legend}
                    onClick={() => remove(index)}
                  />
                </div>
              </fieldset>
            </li>
          );
        })}
      </ol>
      <button
        id={`${name}-add`}
        type="button"
        onClick={add}
        className="min-h-11 border-2 border-dashed border-accent bg-surface px-4 text-sm font-semibold hover:bg-bg"
      >
        + {t(texts.add)}
      </button>
    </div>
  );
}

/**
 * «Cómo comprar» y las preguntas frecuentes, editadas como listas (título y texto;
 * pregunta y respuesta), con su propio «Guardar». El admin no ve la estructura en
 * Markdown: la arma la API.
 */
export function HowToBuySection() {
  const [form, setForm] = useState<Form | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<Status>("idle");

  useEffect(() => {
    let active = true;
    getHowToBuy()
      .then((loaded) => {
        if (!active || !loaded) return;
        setForm(toForm(loaded));
        setLoadFailed(false);
      })
      .catch(() => {
        if (active) setLoadFailed(true);
      });
    return () => {
      active = false;
    };
  }, [attempt]);

  if (loadFailed) {
    return (
      <section className="flex flex-col items-start gap-3 bg-surface p-6">
        <p>{t("admin.howToBuy.loadError")}</p>
        <Button onClick={() => setAttempt((n) => n + 1)}>{t("admin.retry")}</Button>
      </section>
    );
  }
  if (!form) return null;

  // Un cambio en la lista deja viejos los errores (van por posición) y el «Guardado».
  const change = (name: ListName) => (items: Item[]) => {
    setForm({ ...form, [name]: items });
    setErrors({});
    setStatus("idle");
  };

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form) return;
    setStatus("saving");
    const result = await saveHowToBuy(toBody(form));
    if (result.status === "ok") {
      setForm(toForm(result.data));
      setErrors({});
      setStatus("saved");
    } else if (result.status === "invalid") {
      setErrors(result.errors);
      setStatus("invalid");
    } else {
      setStatus("error");
    }
  }

  const message =
    status === "saved"
      ? t("admin.settings.saved")
      : status === "invalid"
        ? t("admin.settings.invalid")
        : status === "error"
          ? t("admin.settings.error")
          : null;

  return (
    <form
      onSubmit={(event) => void handleSubmit(event)}
      noValidate
      aria-labelledby="how-to-buy-title"
      className="flex flex-col gap-5 bg-surface p-6"
    >
      <div className="flex flex-col gap-1">
        <h2 id="how-to-buy-title" className="font-display text-2xl font-bold uppercase">
          {t("admin.howToBuy.title")}
        </h2>
        <span className="text-xs leading-snug text-muted">{t("admin.howToBuy.hint")}</span>
        <span className="text-xs leading-snug text-muted">{t("admin.howToBuy.textHint")}</span>
      </div>
      <div className="grid items-start gap-8 lg:grid-cols-2">
        <ItemList name="topics" items={form.topics} errors={errors} onChange={change("topics")} />
        <ItemList name="faq" items={form.faq} errors={errors} onChange={change("faq")} />
      </div>
      <div className="flex flex-col items-end gap-2">
        <Button
          type="submit"
          disabled={status === "saving"}
          aria-label={status === "saving" ? undefined : t("admin.howToBuy.save")}
        >
          {status === "saving" ? t("admin.settings.saving") : t("admin.settings.save")}
        </Button>
        {message && (
          <p
            role={status === "saved" ? "status" : "alert"}
            className={cn("text-sm font-semibold", status === "saved" ? "text-ok" : "text-error")}
          >
            {message}
          </p>
        )}
      </div>
    </form>
  );
}
