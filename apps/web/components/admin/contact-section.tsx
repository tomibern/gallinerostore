"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  getAdminSettings,
  previewMessage,
  saveAdminSettings,
  type AdminSettings,
  type MessageCase,
  type MessagePreview,
} from "@/lib/admin-api";
import { insertAt, type FieldErrors } from "@/lib/admin-settings";
import { t, type TextKey } from "@/lib/texts";
import { cn } from "@/lib/utils";

// Las plantillas de encargue no se muestran si la tienda no toma encargues.
const ON_ORDER_CASES: MessageCase[] = ["on_order", "sold_out_on_order"];

type Form = {
  whatsapp: string;
  instagram: string;
  templates: Record<MessageCase, string>;
  onOrderNotice: string;
};

function toForm(settings: AdminSettings): Form {
  return {
    whatsapp: settings.contact_channels.whatsapp?.number ?? "",
    instagram: settings.contact_channels.instagram?.username ?? "",
    templates: { ...settings.message_templates },
    onOrderNotice: settings.on_order_notice,
  };
}

type Status =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "saved" }
  | { kind: "invalid" }
  | { kind: "error" };

function FieldError({ id, error }: { id: string; error?: string }) {
  if (!error) return null;
  return (
    <span id={id} className="text-sm font-semibold text-error">
      {error}
    </span>
  );
}

function Hint({ id, children }: { id?: string; children: React.ReactNode }) {
  return (
    <span id={id} className="text-xs leading-snug font-normal text-muted">
      {children}
    </span>
  );
}

/** Un canal de contacto: etiqueta, campo, error y ayuda (que el lector de pantalla lee). */
function ChannelField({
  id,
  label,
  hint,
  value,
  error,
  onChange,
  ...inputProps
}: {
  id: string;
  label: string;
  hint: string;
  value: string;
  error?: string;
  onChange: (value: string) => void;
} & Pick<React.ComponentProps<"input">, "type" | "inputMode" | "autoCapitalize">) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error ${id}-hint` : `${id}-hint`}
        {...inputProps}
      />
      <FieldError id={`${id}-error`} error={error} />
      <Hint id={`${id}-hint`}>{hint}</Hint>
    </div>
  );
}

const textareaClass =
  "w-full resize-y border border-border bg-surface px-3 py-2.5 text-base font-normal text-text focus-visible:border-accent focus-visible:outline-2 focus-visible:outline-primary aria-invalid:border-error";

function TemplateField({
  messageCase,
  value,
  variables,
  error,
  onChange,
}: {
  messageCase: MessageCase;
  value: string;
  variables: string[];
  error?: string;
  onChange: (value: string) => void;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const [preview, setPreview] = useState<MessagePreview | "error" | null>(null);
  const [previewError, setPreviewError] = useState<string | undefined>();
  const name = t(`admin.messages.case.${messageCase}` as TextKey);
  const id = `template-${messageCase}`;
  const shownError = error ?? previewError;

  function insert(variable: string) {
    const textarea = ref.current;
    const start = textarea?.selectionStart ?? value.length;
    const end = textarea?.selectionEnd ?? value.length;
    const next = insertAt(value, `{${variable}}`, start, end);
    onChange(next.value);
    setPreview(null);
    requestAnimationFrame(() => {
      textarea?.focus();
      textarea?.setSelectionRange(next.cursor, next.cursor);
    });
  }

  async function showPreview() {
    const result = await previewMessage(messageCase, value);
    if (result.status === "ok") {
      setPreview(result.data);
      setPreviewError(undefined);
    } else if (result.status === "invalid") {
      setPreview(null);
      setPreviewError(result.errors.template);
    } else {
      setPreview("error");
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{name}</Label>
      <textarea
        ref={ref}
        id={id}
        rows={2}
        value={value}
        onChange={(event) => {
          // Una vista previa vieja ya no corresponde al texto nuevo.
          setPreview(null);
          setPreviewError(undefined);
          onChange(event.target.value);
        }}
        aria-invalid={shownError ? true : undefined}
        aria-describedby={shownError ? `${id}-error` : undefined}
        className={textareaClass}
      />
      <FieldError id={`${id}-error`} error={shownError} />
      <div className="flex flex-wrap gap-2">
        {variables.map((variable) => {
          const label = t(`admin.messages.variable.${variable}` as TextKey);
          return (
            <button
              key={variable}
              type="button"
              onClick={() => insert(variable)}
              aria-label={t("admin.messages.insert", { variable: label, template: name })}
              className="min-h-9 border border-border bg-bg px-3 text-sm font-semibold hover:border-accent"
            >
              + {label}
            </button>
          );
        })}
        <Button type="button" variant="link" className="min-h-9" onClick={() => void showPreview()}>
          {t("admin.messages.preview")}
          <span className="sr-only"> · {name}</span>
        </Button>
      </div>
      {preview && (
        <div role="status" className="bg-bg p-3 text-sm">
          {preview === "error" ? (
            t("admin.messages.previewError")
          ) : (
            <>
              <span className="block text-xs text-muted">
                {preview.product
                  ? t("admin.messages.previewWith", {
                      product: preview.product.name,
                      code: preview.product.code,
                      size: preview.product.size,
                    })
                  : t("admin.messages.previewGeneral")}
              </span>
              <span className="break-words whitespace-pre-wrap">{preview.message}</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Contacto, mensajes prearmados y aviso de encargue, con un solo «Guardar». Los canales y
 * plantillas que la tienda tiene apagados no se muestran, pero se guardan como estaban.
 */
export function ContactSection({ instagram, onOrder }: { instagram: boolean; onOrder: boolean }) {
  const [settings, setSettings] = useState<AdminSettings | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [form, setForm] = useState<Form | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  useEffect(() => {
    let active = true;
    getAdminSettings()
      .then((loaded) => {
        if (!active || !loaded) return;
        setSettings(loaded);
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
        <p>{t("admin.settings.loadError")}</p>
        <Button onClick={() => setAttempt((n) => n + 1)}>{t("admin.retry")}</Button>
      </section>
    );
  }
  if (!settings || !form) return null;

  const update = (changes: Partial<Form>) => setForm({ ...form, ...changes });
  // Los casos y su orden son los de la API.
  const cases = (Object.keys(settings.message_variables) as MessageCase[]).filter(
    (c) => onOrder || !ON_ORDER_CASES.includes(c),
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form) return;
    setStatus({ kind: "saving" });
    const result = await saveAdminSettings({
      contact_channels: {
        whatsapp: form.whatsapp.trim() ? { number: form.whatsapp } : null,
        instagram: form.instagram.trim() ? { username: form.instagram } : null,
      },
      message_templates: form.templates,
      on_order_notice: form.onOrderNotice,
    });
    if (result.status === "ok") {
      setSettings(result.data);
      setForm(toForm(result.data));
      setErrors({});
      setStatus({ kind: "saved" });
    } else if (result.status === "invalid") {
      setErrors(result.errors);
      setStatus({ kind: "invalid" });
    } else {
      setStatus({ kind: "error" });
    }
  }

  const message =
    status.kind === "saved"
      ? t("admin.settings.saved")
      : status.kind === "invalid"
        ? t("admin.settings.invalid")
        : status.kind === "error"
          ? t("admin.settings.error")
          : null;

  return (
    <form
      onSubmit={(event) => void handleSubmit(event)}
      noValidate
      className="grid items-start gap-5 lg:grid-cols-2"
    >
      <section className="flex flex-col gap-4 bg-surface p-6">
        <h2 className="font-display text-2xl font-bold uppercase">{t("admin.contact.title")}</h2>
        <div className={cn("grid gap-4", instagram && "sm:grid-cols-2")}>
          <ChannelField
            id="whatsapp"
            label={t("admin.contact.whatsapp")}
            hint={t("admin.contact.whatsappHint")}
            value={form.whatsapp}
            error={errors.whatsapp}
            onChange={(whatsapp) => update({ whatsapp })}
            type="tel"
            inputMode="tel"
          />
          {instagram && (
            <ChannelField
              id="instagram"
              label={t("admin.contact.instagram")}
              hint={t("admin.contact.instagramHint")}
              value={form.instagram}
              error={errors.instagram}
              onChange={(username) => update({ instagram: username })}
              autoCapitalize="none"
            />
          )}
        </div>

        <h3 className="pt-2 font-display text-xl font-bold uppercase">
          {t("admin.messages.title")}
        </h3>
        <Hint>{t("admin.messages.hint")}</Hint>
        {cases.map((messageCase) => (
          <TemplateField
            key={messageCase}
            messageCase={messageCase}
            value={form.templates[messageCase]}
            variables={settings.message_variables[messageCase] ?? []}
            error={errors[`message_templates.${messageCase}`]}
            onChange={(value) => update({ templates: { ...form.templates, [messageCase]: value } })}
          />
        ))}
      </section>

      <div className="flex flex-col gap-5">
        {onOrder && (
          <section className="flex flex-col gap-4 bg-surface p-6">
            <h2 className="font-display text-2xl font-bold uppercase">{t("admin.notice.title")}</h2>
            <Label htmlFor="on-order-notice">{t("admin.notice.label")}</Label>
            <textarea
              id="on-order-notice"
              rows={3}
              value={form.onOrderNotice}
              onChange={(event) => update({ onOrderNotice: event.target.value })}
              aria-invalid={errors.on_order_notice ? true : undefined}
              aria-describedby={
                errors.on_order_notice
                  ? "on-order-notice-error on-order-notice-hint"
                  : "on-order-notice-hint"
              }
              className={textareaClass}
            />
            <FieldError id="on-order-notice-error" error={errors.on_order_notice} />
            <Hint id="on-order-notice-hint">{t("admin.notice.hint")}</Hint>
          </section>
        )}
        <div className="flex flex-col items-end gap-2">
          <Button type="submit" disabled={status.kind === "saving"}>
            {status.kind === "saving" ? t("admin.settings.saving") : t("admin.settings.save")}
          </Button>
          {message && (
            <p
              role={status.kind === "saved" ? "status" : "alert"}
              className={cn(
                "text-sm font-semibold",
                status.kind === "saved" ? "text-ok" : "text-error",
              )}
            >
              {message}
            </p>
          )}
        </div>
      </div>
    </form>
  );
}
