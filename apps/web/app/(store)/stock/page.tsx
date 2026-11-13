import type { Metadata } from "next";

import { SectionPage, sectionTitle } from "@/components/store/section-page";

export const metadata: Metadata = { title: sectionTitle("stock") };

export default function StockPage() {
  return <SectionPage section="stock" />;
}
