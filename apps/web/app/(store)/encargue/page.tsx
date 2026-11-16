import { SectionPage, sectionMetadata } from "@/components/store/section-page";
import type { SearchParams } from "@/lib/listing";

export function generateMetadata() {
  return sectionMetadata("on_order");
}

export default async function OnOrderPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  return <SectionPage section="on_order" searchParams={await searchParams} />;
}
