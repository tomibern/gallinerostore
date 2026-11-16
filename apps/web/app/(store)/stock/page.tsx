import { SectionPage, sectionMetadata } from "@/components/store/section-page";
import type { SearchParams } from "@/lib/listing";

export function generateMetadata() {
  return sectionMetadata("stock");
}

export default async function StockPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  return <SectionPage section="stock" searchParams={await searchParams} />;
}
