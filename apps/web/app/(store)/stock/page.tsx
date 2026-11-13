import type { Metadata } from "next";

import { SectionPage, sectionTitle } from "@/components/store/section-page";
import type { SearchParams } from "@/lib/listing";

export const metadata: Metadata = { title: sectionTitle("stock") };

export default async function StockPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  return <SectionPage section="stock" searchParams={await searchParams} />;
}
