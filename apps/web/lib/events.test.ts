import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createVisit,
  deviceFor,
  DIRECT_SOURCE,
  pageFromPath,
  postEvent,
  sourceFrom,
} from "./events";

// Un sessionStorage de mentira.
function memoryStorage() {
  const items = new Map<string, string>();
  return {
    getItem: (key: string) => items.get(key) ?? null,
    setItem: (key: string, value: string) => void items.set(key, value),
  };
}

// Un sessionStorage que no se puede usar (bloqueado, modo privado, sin cuota).
const brokenStorage = {
  getItem: () => {
    throw new DOMException("bloqueado", "SecurityError");
  },
  setItem: () => {
    throw new DOMException("sin cuota", "QuotaExceededError");
  },
};

describe("sourceFrom", () => {
  it("toma el utm_source de la URL", () => {
    expect(sourceFrom("?utm_source=historia")).toBe("historia");
  });

  it("lo recorta y lo pasa a minúsculas", () => {
    expect(sourceFrom("?utm_source=%20Bio%20&x=1")).toBe("bio");
  });

  it("corta los textos largos", () => {
    expect(sourceFrom(`?utm_source=${"a".repeat(80)}`)).toHaveLength(60);
  });

  it.each(["", "?x=1", "?utm_source=", "?utm_source=%20%20"])(
    "sin utm_source en «%s» es directo",
    (search) => {
      expect(sourceFrom(search)).toBe(DIRECT_SOURCE);
    },
  );
});

describe("createVisit", () => {
  it("arma un session_id al azar de 32 caracteres hexadecimales", () => {
    const visit = createVisit(memoryStorage)("");
    expect(visit.session_id).toMatch(/^[0-9a-f]{32}$/);
  });

  it("guarda el session_id y el origen para toda la visita", () => {
    const storage = memoryStorage();
    const first = createVisit(() => storage)("?utm_source=historia");
    // Otra página de la misma pestaña (o una recarga): sin utm, sigue siendo historia.
    const next = createVisit(() => storage)("");
    expect(next).toEqual(first);
    expect(next.source).toBe("historia");
  });

  it("el origen de la entrada no se pisa con otro utm", () => {
    const storage = memoryStorage();
    createVisit(() => storage)("");
    expect(createVisit(() => storage)("?utm_source=bio").source).toBe(DIRECT_SOURCE);
  });

  it("sin sessionStorage sigue andando y recuerda la visita mientras dure la página", () => {
    const visit = createVisit(() => brokenStorage);
    const first = visit("?utm_source=bio");
    expect(first.session_id).toMatch(/^[0-9a-f]{32}$/);
    expect(visit("")).toEqual(first);
  });

  it("sin window (por ejemplo, si no hay sessionStorage) también", () => {
    const visit = createVisit(() => {
      throw new ReferenceError("sessionStorage is not defined");
    });
    expect(visit("").source).toBe(DIRECT_SOURCE);
  });
});

describe("deviceFor", () => {
  it("es escritorio con pantalla ancha y celular si no", () => {
    expect(deviceFor(true)).toBe("desktop");
    expect(deviceFor(false)).toBe("mobile");
  });
});

describe("pageFromPath", () => {
  it.each([
    ["/", "home"],
    ["/stock", "stock"],
    ["/encargue", "on_order"],
    ["/como-comprar", "how_to_buy"],
    ["/p/tp-001", "product"],
    ["/no-existe", "not_found"],
  ] as const)("%s → %s", (path, page) => {
    expect(pageFromPath(path)).toBe(page);
  });
});

describe("postEvent", () => {
  const event = {
    type: "page_view",
    page: "home",
    session_id: "0".repeat(32),
    source: "directo",
    device: "mobile",
  } as const;

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lo manda con sendBeacon como JSON a /api/events", async () => {
    const sendBeacon = vi.fn<(url: string, body: Blob) => boolean>(() => true);
    vi.stubGlobal("navigator", { sendBeacon });

    postEvent(event);

    const [url, body] = sendBeacon.mock.calls[0];
    expect(url).toBe("/api/events");
    expect(body.type).toBe("application/json");
    expect(JSON.parse(await body.text())).toEqual(event);
  });

  it("si el beacon no sale, usa fetch con keepalive", () => {
    const fetch = vi.fn(() => Promise.resolve(new Response(null, { status: 204 })));
    vi.stubGlobal("navigator", { sendBeacon: () => false });
    vi.stubGlobal("fetch", fetch);

    postEvent(event);

    expect(fetch).toHaveBeenCalledWith("/api/events", {
      method: "POST",
      keepalive: true,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(event),
    });
  });

  it("nunca rompe la página", () => {
    vi.stubGlobal("navigator", {
      sendBeacon: () => {
        throw new TypeError("no");
      },
    });
    vi.stubGlobal("fetch", () => Promise.reject(new Error("sin red")));

    expect(() => postEvent(event)).not.toThrow();
  });
});
