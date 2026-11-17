import { SectionPage, sectionMetadata } from "@/components/store/section-page";
import { TrackView } from "@/components/store/track-view";
import type { SearchParams } from "@/lib/listing";

export function generateMetadata() {
  return sectionMetadata("on_order");
}

export default async function OnOrderPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  return (
    <>
      <TrackView event={{ type: "page_view", page: "on_order" }} />
      <SectionPage section="on_order" searchParams={await searchParams} />
    </>
  );
}
