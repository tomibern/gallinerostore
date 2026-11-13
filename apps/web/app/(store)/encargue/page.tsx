import type { Metadata } from "next";

import { SectionPage, sectionTitle } from "@/components/store/section-page";
import type { SearchParams } from "@/lib/listing";

export const metadata: Metadata = { title: sectionTitle("on_order") };

export default async function OnOrderPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  return <SectionPage section="on_order" searchParams={await searchParams} />;
}
