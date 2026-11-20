"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  getProductRanking,
  type MetricsPeriod,
  type ProductRanking,
  type RankingSort,
} from "@/lib/admin-api";
import { ADMIN_LOGIN, adminProductPath } from "@/lib/admin-paths";
import { formatCount, formatShare } from "@/lib/metrics-format";
import { t } from "@/lib/texts";
import { cn } from "@/lib/utils";

// Por defecto, el ranking va por consultas (como la API).
const DEFAULT_SORT: RankingSort = "inquiries";

type RankedProduct = ProductRanking["items"][number];

type Column = { sort: RankingSort; label: string; value: (item: RankedProduct) => string };

function columns(ranking: ProductRanking, locale: string): Column[] {
  const count = (value: number) => formatCount(value, locale);
  const all: Column[] = [
    {
      sort: "visits",
      label: t("admin.metrics.ranking.visits"),
      value: (item) => count(item.visits),
    },
    {
      sort: "inquiries",
      label: t("admin.metrics.ranking.inquiries"),
      value: (item) => count(item.inquiries),
    },
    {
      sort: "rate",
      label: t("admin.metrics.ranking.rate"),
      value: (item) =>
        item.rate == null ? t("admin.metrics.rate.none") : formatShare(item.rate, locale),
    },
    {
      sort: "whatsapp",
      label: t("inquiry.channel.whatsapp"),
      value: (item) => count(item.whatsapp),
    },
    {
      sort: "instagram",
      label: t("inquiry.channel.instagram"),
      value: (item) => count(item.instagram),
    },
  ];
  // Los canales que no se muestran (Instagram apagado) no tienen columna.
  return all.filter(
    (column) =>
      (column.sort !== "whatsapp" && column.sort !== "instagram") ||
      ranking.channels.includes(column.sort),
  );
}

type State =
  { status: "loading" } | { status: "error" } | { status: "ok"; ranking: ProductRanking };

/** Ranking de productos del período, ordenable por columna (de mayor a menor). */
export function ProductRankingCard({ period, locale }: { period: MetricsPeriod; locale: string }) {
  const router = useRouter();
  const [sort, setSort] = useState<RankingSort>(DEFAULT_SORT);
  const [attempt, setAttempt] = useState(0);
  const request = `${period}:${sort}:${attempt}`;
  const [loaded, setLoaded] = useState<{ request: string; state: State } | null>(null);
  // Mientras llega el orden nuevo, se sigue viendo el anterior (no salta la tabla).
  const [shown, setShown] = useState<ProductRanking | null>(null);
  const state: State = loaded?.request === request ? loaded.state : { status: "loading" };

  useEffect(() => {
    let active = true;
    getProductRanking(period, sort)
      .then((ranking) => {
        if (!active) return;
        if (!ranking) {
          router.replace(`${ADMIN_LOGIN}?next=${encodeURIComponent(window.location.pathname)}`);
          return;
        }
        setLoaded({ request, state: { status: "ok", ranking } });
        setShown(ranking);
      })
      .catch(() => {
        if (active) setLoaded({ request, state: { status: "error" } });
      });
    return () => {
      active = false;
    };
  }, [period, sort, request, router]);

  // Lo del período anterior no sirve: solo se mantiene si es del mismo período.
  const ranking = state.status === "ok" ? state.ranking : shown?.period === period ? shown : null;

  return (
    <section
      aria-labelledby="product-ranking-title"
      className="flex flex-col gap-3 bg-surface p-4 md:p-5"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h2
          id="product-ranking-title"
          className="font-display text-lg font-bold uppercase md:text-xl"
        >
          {t("admin.metrics.ranking.title")}
        </h2>
        <span className="text-xs leading-snug text-muted">
          <span className="md:hidden">{t("admin.metrics.ranking.hint.short")}</span>
          <span className="hidden md:inline">{t("admin.metrics.ranking.hint")}</span>
        </span>
      </div>
      {state.status === "error" ? (
        <div role="alert" className="flex flex-col items-start gap-3">
          <p>{t("admin.metrics.ranking.error")}</p>
          <Button variant="outline" onClick={() => setAttempt((n) => n + 1)}>
            {t("admin.retry")}
          </Button>
        </div>
      ) : ranking === null ? (
        <p role="status" className="text-sm text-muted">
          {t("admin.metrics.ranking.loading")}
        </p>
      ) : ranking.items.length === 0 ? (
        <p className="text-sm">{t("admin.metrics.ranking.empty")}</p>
      ) : (
        <RankingTable
          ranking={ranking}
          sort={sort}
          onSort={setSort}
          locale={locale}
          busy={state.status === "loading"}
        />
      )}
    </section>
  );
}

function RankingTable({
  ranking,
  sort,
  onSort,
  locale,
  busy,
}: {
  ranking: ProductRanking;
  sort: RankingSort;
  onSort: (sort: RankingSort) => void;
  locale: string;
  busy: boolean;
}) {
  const th =
    "px-2 py-2 text-left text-xs font-bold tracking-wider whitespace-nowrap text-muted uppercase";
  const td = "border-b border-border px-2 py-2.5 text-sm";
  const shown = columns(ranking, locale);

  return (
    <div className="-mx-4 overflow-x-auto px-4 md:mx-0 md:px-0">
      <table className="w-full border-collapse" aria-busy={busy}>
        <thead>
          <tr className="border-b-2 border-accent">
            <th scope="col" className={th}>
              {t("admin.metrics.ranking.position")}
            </th>
            <th scope="col" className={th}>
              {t("admin.metrics.ranking.product")}
            </th>
            {shown.map((column) => {
              const active = column.sort === sort;
              return (
                <th
                  key={column.sort}
                  scope="col"
                  aria-sort={active ? "descending" : undefined}
                  className={cn(th, "p-0")}
                >
                  <button
                    type="button"
                    data-sort={column.sort}
                    aria-label={t("admin.metrics.ranking.sortBy", { column: column.label })}
                    onClick={() => onSort(column.sort)}
                    className={cn(
                      "flex min-h-11 w-full items-center gap-1 px-2 uppercase hover:text-accent focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary",
                      active && "text-accent",
                    )}
                  >
                    {column.label}
                    <span aria-hidden="true" className={active ? "" : "invisible"}>
                      ▼
                    </span>
                  </button>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {ranking.items.map((item, index) => (
            <tr key={item.code} data-code={item.code} className="relative hover:bg-bg">
              <td className={cn(td, "font-display text-lg font-bold text-primary")}>{index + 1}</td>
              <td className={cn(td, "min-w-48")}>
                <Link
                  href={adminProductPath(item.code)}
                  className="flex flex-col gap-0.5 after:absolute after:inset-0 hover:text-primary"
                >
                  <span className="font-semibold">{item.name}</span>
                  <span className="text-xs text-muted">
                    {item.status === "published"
                      ? item.code
                      : `${item.code} · ${t(`admin.products.status.${item.status}`)}`}
                  </span>
                </Link>
              </td>
              {shown.map((column) => (
                <td
                  key={column.sort}
                  data-column={column.sort}
                  className={cn(
                    td,
                    "whitespace-nowrap",
                    column.sort === "inquiries" && "font-bold text-primary",
                  )}
                >
                  {column.value(item)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
