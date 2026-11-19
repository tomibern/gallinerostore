"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { AdminPage } from "@/components/admin/admin-page";
import { ProductRankingCard } from "@/components/admin/product-ranking";
import { Button } from "@/components/ui/button";
import { getMetricsSummary, type MetricsPeriod, type MetricsSummary } from "@/lib/admin-api";
import { ADMIN_LOGIN } from "@/lib/admin-paths";
import {
  chartLabel,
  chartLongDate,
  formatChange,
  formatCount,
  formatShare,
  labelEvery,
} from "@/lib/metrics-format";
import { sourceLabel, t, type TextKey } from "@/lib/texts";
import { cn } from "@/lib/utils";

const PERIODS: MetricsPeriod[] = ["today", "7d", "30d"];
const DEFAULT_PERIOD: MetricsPeriod = "7d";

function periodLabel(period: MetricsPeriod): string {
  return t(`admin.metrics.period.${period}` as TextKey);
}

type State =
  { status: "loading" } | { status: "error" } | { status: "ok"; summary: MetricsSummary };

// La respuesta de un pedido (período e intento): mientras no llega la del pedido actual,
// se muestra «Cargando».
type Loaded = { request: string; state: State };

/** Pantalla de Métricas: el período elegido, sus números y de dónde llegan las visitas. */
export function MetricsSummaryView({ locale }: { locale: string }) {
  const router = useRouter();
  const [period, setPeriod] = useState<MetricsPeriod>(DEFAULT_PERIOD);
  // Cada «Probar de nuevo» suma uno y vuelve a pedir.
  const [attempt, setAttempt] = useState(0);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const request = `${period}:${attempt}`;
  const state: State = loaded?.request === request ? loaded.state : { status: "loading" };

  useEffect(() => {
    let active = true;
    getMetricsSummary(period)
      .then((summary) => {
        if (!active) return;
        if (summary) setLoaded({ request, state: { status: "ok", summary } });
        else router.replace(`${ADMIN_LOGIN}?next=${encodeURIComponent(window.location.pathname)}`);
      })
      .catch(() => {
        if (active) setLoaded({ request, state: { status: "error" } });
      });
    return () => {
      active = false;
    };
  }, [period, request, router]);

  return (
    <AdminPage
      title={t("admin.nav.metrics")}
      actions={<PeriodPicker value={period} onChange={setPeriod} />}
    >
      <div id="metrics-panel" role="tabpanel" aria-label={periodLabel(period)}>
        {state.status === "loading" && (
          <p className="text-muted" role="status">
            {t("admin.metrics.loading")}
          </p>
        )}
        {state.status === "error" && (
          <div className="flex flex-col items-start gap-3">
            <p role="alert">{t("admin.metrics.error")}</p>
            <Button onClick={() => setAttempt((n) => n + 1)}>{t("admin.retry")}</Button>
          </div>
        )}
        {state.status === "ok" && <Summary summary={state.summary} locale={locale} />}
      </div>
    </AdminPage>
  );
}

function PeriodPicker({
  value,
  onChange,
}: {
  value: MetricsPeriod;
  onChange: (period: MetricsPeriod) => void;
}) {
  const tabs = useRef<(HTMLButtonElement | null)[]>([]);

  // Pestañas: las flechas pasan a la de al lado (patrón de ARIA).
  function handleKeyDown(event: React.KeyboardEvent, index: number) {
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    event.preventDefault();
    const next = (index + step + PERIODS.length) % PERIODS.length;
    onChange(PERIODS[next]);
    tabs.current[next]?.focus();
  }

  return (
    <div
      role="tablist"
      aria-label={t("admin.metrics.period.label")}
      className="grid grid-cols-3 border-2 border-accent bg-surface md:flex"
    >
      {PERIODS.map((period, index) => {
        const selected = period === value;
        return (
          <button
            key={period}
            ref={(element) => {
              tabs.current[index] = element;
            }}
            type="button"
            role="tab"
            aria-selected={selected}
            aria-label={periodLabel(period)}
            aria-controls="metrics-panel"
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(period)}
            onKeyDown={(event) => handleKeyDown(event, index)}
            className={cn(
              "min-h-11 px-2 text-sm leading-tight font-semibold focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-primary md:px-5",
              selected ? "bg-accent font-bold text-on-accent" : "text-accent hover:bg-bg",
            )}
          >
            <span className="md:hidden">
              {t(`admin.metrics.period.${period}.short` as TextKey)}
            </span>
            <span className="hidden md:inline">{periodLabel(period)}</span>
          </button>
        );
      })}
    </div>
  );
}

function Card({ className, children, ...props }: React.ComponentProps<"div">) {
  return (
    <div className={cn("flex flex-col gap-3 bg-surface p-4 md:p-5", className)} {...props}>
      {children}
    </div>
  );
}

function Hint({ children }: { children: React.ReactNode }) {
  return <span className="text-xs leading-snug text-muted">{children}</span>;
}

function Summary({ summary, locale }: { summary: MetricsSummary; locale: string }) {
  const previous = t(
    summary.period === "today" ? "admin.metrics.previous.today" : "admin.metrics.previous.other",
  );

  function comparison({ change }: { change: number | null }) {
    return change == null
      ? t("admin.metrics.change.none", { previous })
      : t("admin.metrics.change", { change: formatChange(change, locale), previous });
  }

  const { rate } = summary;

  return (
    <div className="flex flex-col gap-3 md:gap-4">
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4 md:gap-4">
        <Kpi
          label={t("admin.metrics.visits")}
          value={formatCount(summary.visits.current, locale)}
          hint={comparison(summary.visits)}
        />
        <Kpi
          label={t("admin.metrics.inquiries")}
          value={formatCount(summary.inquiries.current, locale)}
          hint={comparison(summary.inquiries)}
          strong
        />
        <Kpi
          label={t("admin.metrics.rate")}
          value={
            rate.current == null ? t("admin.metrics.rate.none") : formatShare(rate.current, locale)
          }
          hint={
            rate.previous == null
              ? t("admin.metrics.rate.hint")
              : t("admin.metrics.rate.hintWithPrevious", {
                  rate: formatShare(rate.previous, locale),
                })
          }
        />
        <Channels channels={summary.channels} locale={locale} />
      </div>

      <div className="grid gap-3 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] md:gap-4">
        <Chart summary={summary} locale={locale} />
        <Sources sources={summary.sources} locale={locale} />
      </div>

      <ProductRankingCard period={summary.period} locale={locale} />

      <p className="border border-dashed border-primary/60 px-3 py-3 text-xs leading-normal md:px-4 md:text-sm">
        {t("admin.metrics.notice")}
      </p>
    </div>
  );
}

function Kpi({
  label,
  value,
  hint,
  strong = false,
}: {
  label: string;
  value: string;
  hint: string;
  strong?: boolean;
}) {
  return (
    <Card className="gap-1" role="group" aria-label={label}>
      <Hint>{label}</Hint>
      <span
        className={cn(
          "font-display text-3xl font-bold uppercase md:text-4xl",
          strong && "text-primary",
        )}
      >
        {value}
      </span>
      <Hint>{hint}</Hint>
    </Card>
  );
}

// Un color por canal, en el orden en que llegan.
const CHANNEL_COLORS = ["bg-primary", "bg-accent"];

function Channels({ channels, locale }: { channels: MetricsSummary["channels"]; locale: string }) {
  // Sin consultas, la API no manda partes.
  const withInquiries = channels.some((channel) => channel.share != null);
  return (
    <Card className="gap-2">
      <Hint>
        <span className="md:hidden">{t("admin.metrics.channels.short")}</span>
        <span className="hidden md:inline">{t("admin.metrics.channels")}</span>
      </Hint>
      {withInquiries ? (
        <>
          <div className="flex h-3.5 md:h-4.5" aria-hidden="true">
            {channels.map((channel, index) => (
              <span
                key={channel.channel}
                className={CHANNEL_COLORS[index % CHANNEL_COLORS.length]}
                style={{ flexGrow: channel.inquiries }}
              />
            ))}
          </div>
          <span className="text-xs font-semibold md:text-sm">
            {channels
              .map((channel) =>
                t("admin.metrics.channels.item", {
                  channel: t(`inquiry.channel.${channel.channel}`),
                  share: formatShare(channel.share ?? 0, locale),
                }),
              )
              .join(t("admin.metrics.channels.separator"))}
          </span>
        </>
      ) : (
        <span className="text-xs md:text-sm">{t("admin.metrics.channels.empty")}</span>
      )}
    </Card>
  );
}

type ChartPoint = MetricsSummary["chart"][number];

function Chart({ summary, locale }: { summary: MetricsSummary; locale: string }) {
  const points = summary.chart;
  const max = Math.max(1, ...points.map((point) => Math.max(point.visits, point.inquiries)));
  const mobileEvery = labelEvery(points.length, false);
  const desktopEvery = labelEvery(points.length, true);
  const height = (value: number) => `${(value / max) * 100}%`;
  const title = t("admin.metrics.chart.title", {
    period: periodLabel(summary.period).toLowerCase(),
  });
  const key = (point: ChartPoint) => `${point.date}-${point.hour}`;

  return (
    <Card>
      <h2 className="font-display text-lg font-bold uppercase md:text-xl">{title}</h2>
      <div aria-hidden="true" className="flex flex-col gap-1.5">
        <div className="flex h-38 items-end gap-0.5 border-b border-primary/35 md:h-55 md:gap-1.5">
          {points.map((point) => (
            <div key={key(point)} className="relative h-full flex-1">
              <span
                className="absolute inset-x-0 bottom-0 bg-primary/35"
                style={{ height: height(point.visits) }}
              />
              <span
                className="absolute inset-x-0 bottom-0 bg-primary"
                style={{ height: height(point.inquiries) }}
              />
            </div>
          ))}
        </div>
        <div className="flex gap-0.5 md:gap-1.5">
          {points.map((point, index) => (
            <span
              key={key(point)}
              className={cn(
                "flex-1 overflow-visible text-center text-[11px] whitespace-nowrap text-muted md:text-xs",
                index % mobileEvery !== 0 && "invisible",
                index % desktopEvery === 0 && "md:visible",
                index % desktopEvery !== 0 && "md:invisible",
              )}
            >
              {point.hour != null
                ? t("admin.metrics.chart.hour", { hour: point.hour })
                : chartLabel(point, points.length, locale)}
            </span>
          ))}
        </div>
      </div>
      <div className="flex gap-4 text-xs md:text-sm" aria-hidden="true">
        <span className="flex items-center gap-1.5">
          <span className="size-2.5 bg-primary/35 md:size-3" />
          {t("admin.metrics.visits")}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-2.5 bg-primary md:size-3" />
          {t("admin.metrics.inquiries")}
        </span>
      </div>
      {/* Los mismos datos, para lectores de pantalla. */}
      <table className="sr-only">
        <caption>{title}</caption>
        <thead>
          <tr>
            <th scope="col">{t("admin.metrics.chart.when")}</th>
            <th scope="col">{t("admin.metrics.visits")}</th>
            <th scope="col">{t("admin.metrics.inquiries")}</th>
          </tr>
        </thead>
        <tbody>
          {points.map((point) => (
            <tr key={key(point)}>
              <th scope="row">
                {point.hour != null
                  ? t("admin.metrics.chart.dayHour", {
                      date: chartLongDate(point, locale),
                      hour: point.hour,
                    })
                  : chartLongDate(point, locale)}
              </th>
              <td>{formatCount(point.visits, locale)}</td>
              <td>{formatCount(point.inquiries, locale)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function Sources({ sources, locale }: { sources: MetricsSummary["sources"]; locale: string }) {
  const top = Math.max(0, ...sources.map((source) => source.share));
  return (
    <Card>
      <h2 className="font-display text-lg font-bold uppercase md:text-xl">
        {t("admin.metrics.sources.title")}
      </h2>
      {sources.length === 0 ? (
        <p className="text-sm">{t("admin.metrics.sources.empty")}</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {sources.map((source) => (
            <li key={source.source ?? ""} className="flex flex-col gap-1">
              <span className="flex justify-between gap-2 text-sm">
                <span className="min-w-0 font-semibold break-words">
                  {sourceLabel(source.source ?? null)}
                </span>
                <span>{formatShare(source.share, locale)}</span>
              </span>
              <span className="h-2.5 bg-bg" aria-hidden="true">
                <span
                  className="block h-full bg-primary"
                  // La barra más larga ocupa todo el ancho: se comparan entre sí.
                  style={{ width: `${(source.share / top) * 100}%` }}
                />
              </span>
            </li>
          ))}
        </ul>
      )}
      <Hint>{t("admin.metrics.sources.hint")}</Hint>
    </Card>
  );
}
