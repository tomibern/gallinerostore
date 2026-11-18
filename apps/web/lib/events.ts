// Registro anónimo de eventos (visitas y consultas) desde el navegador. Sin cookies ni
// datos personales: un id de sesión al azar, el origen de la visita y el tipo de
// pantalla. Nunca rompe la página: si algo falla, el evento se pierde y listo.

import type { Device, EventIn, Page } from "@catalog/api-client";

// Sin utm_source en la URL de entrada. Tiene que coincidir con DIRECT_SOURCE de la API
// (app/modules/events/models.py): las métricas lo cuentan como «directo / otros».
export const DIRECT_SOURCE = "directo";
const MAX_SOURCE_LENGTH = 60;
// Por Next, que lo reenvía a la API (ADR 0003).
const EVENTS_URL = "/api/events";
const SESSION_KEY = "events.session";
const SOURCE_KEY = "events.source";
// El mismo `md` de Tailwind que separa el diseño de celular del de escritorio.
const WIDE_SCREEN = "(min-width: 48rem)";

type KeyValueStore = Pick<Storage, "getItem" | "setItem">;

// Los campos que pone cada evento; los de la visita los agrega `recordEvent`.
type VisitFields = "session_id" | "source" | "device";
export type EventFields = EventIn extends infer E
  ? E extends EventIn
    ? Omit<E, VisitFields>
    : never
  : never;

export type Visit = { session_id: string; source: string };

/** El utm_source de la URL, normalizado; sin él, «directo». */
export function sourceFrom(search: string): string {
  const raw = new URLSearchParams(search).get("utm_source") ?? "";
  const source = raw.trim().toLowerCase().slice(0, MAX_SOURCE_LENGTH);
  return source || DIRECT_SOURCE;
}

function randomId(): string {
  // getRandomValues anda también por http (el celular en la wifi local); randomUUID no.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

/**
 * La visita de esta pestaña: el session_id y el origen se guardan en sessionStorage la
 * primera vez y después no cambian. Sin sessionStorage (bloqueado o sin cuota), se
 * recuerdan en memoria mientras dure la página.
 */
export function createVisit(storage: () => KeyValueStore) {
  const memory = new Map<string, string>();
  const read = (key: string) => {
    if (memory.has(key)) return memory.get(key)!;
    try {
      return storage().getItem(key);
    } catch {
      return null;
    }
  };
  const remember = (key: string, value: string) => {
    memory.set(key, value);
    try {
      storage().setItem(key, value);
    } catch {
      // Queda en memoria.
    }
    return value;
  };

  return (search: string): Visit => ({
    session_id: read(SESSION_KEY) ?? remember(SESSION_KEY, randomId()),
    source: read(SOURCE_KEY) ?? remember(SOURCE_KEY, sourceFrom(search)),
  });
}

export function deviceFor(wideScreen: boolean): Device {
  return wideScreen ? "desktop" : "mobile";
}

// Rutas fijas del núcleo (las mismas de la navegación y de SECTION_PATHS).
const PAGES: Record<string, Page> = {
  "/": "home",
  "/stock": "stock",
  "/encargue": "on_order",
  "/como-comprar": "how_to_buy",
};

/** La página de una consulta general según la ruta en la que está. */
export function pageFromPath(pathname: string): Page {
  if (pathname.startsWith("/p/")) return "product";
  return PAGES[pathname] ?? "not_found";
}

/** Manda el evento a la API (por Next, ADR 0003) sin esperar la respuesta. */
export function postEvent(event: EventIn): void {
  const body = JSON.stringify(event);
  try {
    // Un Blob JSON: un string viajaría como text/plain y la API no lo leería.
    if (navigator.sendBeacon?.(EVENTS_URL, new Blob([body], { type: "application/json" }))) {
      return;
    }
  } catch {
    // Probamos con fetch.
  }
  try {
    fetch(EVENTS_URL, {
      method: "POST",
      keepalive: true,
      headers: { "Content-Type": "application/json" },
      body,
    }).catch(() => {});
  } catch {
    // Sin red ni beacon: el evento se pierde.
  }
}

const visit = createVisit(() => window.sessionStorage);

/** Fija el origen con la URL de entrada, aunque esa página no registre una visita (404). */
export function startVisit(): void {
  try {
    visit(window.location.search);
  } catch {
    // Nunca rompe la página.
  }
}

/** Registra un evento de esta visita. Solo en el navegador (efectos y clics). */
export function recordEvent(fields: EventFields): void {
  try {
    const device = deviceFor(window.matchMedia(WIDE_SCREEN).matches);
    postEvent({ ...fields, ...visit(window.location.search), device } as EventIn);
  } catch {
    // Nunca rompe la página.
  }
}
