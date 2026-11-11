"use client";

import { useEffect, useState } from "react";

type State = "loading" | "ok" | "error";

// Se pide desde el navegador a /api/health: prueba el reenvío de Next a la API.
export function HealthStatus() {
  const [state, setState] = useState<State>("loading");

  useEffect(() => {
    fetch("/api/health", { cache: "no-store" })
      .then((response) => setState(response.ok ? "ok" : "error"))
      .catch(() => setState("error"));
  }, []);

  const label = { loading: "API…", ok: "API ok", error: "API con problemas" }[state];
  const color = { loading: "text-muted", ok: "text-ok", error: "text-error" }[state];

  return (
    <span data-testid="health" data-state={state} className={`font-medium ${color}`}>
      {label}
    </span>
  );
}
