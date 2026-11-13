import type { Metadata } from "next";

import { SectionPage, sectionTitle } from "@/components/store/section-page";

export const metadata: Metadata = { title: sectionTitle("on_order") };

export default function OnOrderPage() {
  return <SectionPage section="on_order" />;
}
