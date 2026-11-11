"use client";

import { useEffect, useState } from "react";

type State = "loading" | "ok" | "error";

const VIEW: Record<State, { label: string; className: string }> = {
  loading: { label: "API…", className: "text-muted" },
  ok: { label: "API ok", className: "text-ok" },
  error: { label: "API con problemas", className: "text-error" },
};

// Se pide desde el navegador a /api/health: prueba el reenvío de Next a la API.
export function HealthStatus() {
  const [state, setState] = useState<State>("loading");

  useEffect(() => {
    fetch("/api/health", { cache: "no-store" })
      .then((response) => setState(response.ok ? "ok" : "error"))
      .catch(() => setState("error"));
  }, []);

  const { label, className } = VIEW[state];

  return (
    <span data-testid="health" data-state={state} className={`font-medium ${className}`}>
      {label}
    </span>
  );
}
