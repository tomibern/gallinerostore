import { SectionPage, sectionMetadata } from "@/components/store/section-page";
import { TrackView } from "@/components/store/track-view";
import type { SearchParams } from "@/lib/listing";

export function generateMetadata() {
  return sectionMetadata("stock");
}

export default async function StockPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  return (
    <>
      <TrackView event={{ type: "page_view", page: "stock" }} />
      <SectionPage section="stock" searchParams={await searchParams} />
    </>
  );
}
