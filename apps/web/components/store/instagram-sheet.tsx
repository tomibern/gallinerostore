"use client";

import { useEffect, useRef, useState } from "react";

import type { Inquiry } from "@/lib/api";

export type InstagramSheetLabels = {
  title: string;
  text: string;
  copy: string;
  copied: string;
  copyFailed: string;
  open: string;
  close: string;
};

type Props = {
  // La consulta a mostrar; null, la hoja cerrada.
  inquiry: Inquiry | null;
  labels: InstagramSheetLabels;
  onClose: () => void;
  // Al tocar «Abrir Instagram»: ahí cuenta la consulta, no al abrir la hoja.
  onOpenChat?: () => void;
};

type CopyState = "idle" | "copied" | "failed";

// Hoja de Instagram: Instagram no acepta texto en el link del chat, así que el mensaje
// se muestra para que la persona lo copie (si quiere) y lo pegue. Nunca se copia sin
// que lo pida: el portapapeles se toca solo en el clic de «Copiar mensaje», sin
// esperar nada antes (ADR 0005). Si no se puede copiar (sin HTTPS, permiso negado),
// el texto queda seleccionado para copiarlo a mano.
export function InstagramSheet({ inquiry, labels, onClose, onOpenChat }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const message = useRef<HTMLTextAreaElement>(null);
  const [copy, setCopy] = useState<CopyState>("idle");

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (inquiry && !element.open) element.showModal();
    if (!inquiry && element.open) element.close();
  }, [inquiry]);

  function copyFailed() {
    setCopy("failed");
    message.current?.focus();
    message.current?.select();
  }

  function copyMessage() {
    if (!inquiry) return;
    // navigator.clipboard no existe fuera de un contexto seguro (HTTPS o localhost).
    if (!navigator.clipboard) return copyFailed();
    navigator.clipboard.writeText(inquiry.message).then(() => setCopy("copied"), copyFailed);
  }

  function close() {
    setCopy("idle");
    onClose();
  }

  return (
    <dialog
      ref={dialog}
      aria-labelledby="instagram-sheet-title"
      onClose={close}
      className="m-0 mt-auto max-h-[90dvh] w-full max-w-none rounded-t-lg bg-surface p-5 text-text shadow-xl backdrop:bg-black/50 md:m-auto md:max-w-md md:rounded-lg"
    >
      {inquiry && (
        <div className="flex flex-col gap-4">
          <h2 id="instagram-sheet-title" className="font-display text-xl font-bold">
            {labels.title}
          </h2>
          <p className="text-sm text-muted">{labels.text}</p>
          <textarea
            ref={message}
            readOnly
            rows={4}
            value={inquiry.message}
            aria-label={labels.title}
            data-testid="inquiry-message"
            className="w-full resize-none rounded-md border border-border bg-bg p-3 text-sm"
          />
          <p aria-live="polite" data-copy={copy} className="min-h-5 text-sm">
            {copy === "copied" && <span className="text-ok">{labels.copied}</span>}
            {copy === "failed" && <span className="text-error">{labels.copyFailed}</span>}
          </p>
          <div className="flex flex-col gap-2 md:flex-row-reverse">
            <a
              href={inquiry.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={onOpenChat}
              className="font-display flex h-12 items-center justify-center rounded-md bg-primary md:flex-1 px-4 font-semibold text-primary-contrast"
            >
              {labels.open}
            </a>
            <button
              type="button"
              onClick={copyMessage}
              data-testid="copy-message"
              className="font-display flex h-12 cursor-pointer items-center justify-center rounded-md border md:flex-1 border-border px-4 font-semibold"
            >
              {labels.copy}
            </button>
          </div>
          <form method="dialog">
            <button
              type="submit"
              className="flex h-11 w-full cursor-pointer items-center justify-center text-sm text-muted underline"
            >
              {labels.close}
            </button>
          </form>
        </div>
      )}
    </dialog>
  );
}
