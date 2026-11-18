import { MetricsSummaryView } from "@/components/admin/metrics-summary";
import { getStore } from "@/lib/api";

// Para formatear los números; sin la API, el idioma del diccionario.
const FALLBACK_LOCALE = "es-AR";

export default async function AdminMetricsPage() {
  const store = await getStore();
  return <MetricsSummaryView locale={store?.locale ?? FALLBACK_LOCALE} />;
}
