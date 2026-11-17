import { SectionPage, sectionMetadata } from "@/components/store/section-page";
import { RecordView } from "@/components/store/record-view";
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
      <RecordView event={{ type: "page_view", page: "on_order" }} />
      <SectionPage section="on_order" searchParams={await searchParams} />
    </>
  );
}
