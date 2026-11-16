import type { Metadata } from "next";

import { getStore } from "@/lib/api";
import { siteUrl } from "@/lib/env";
import { rootMetadata } from "@/lib/seo";

import "./globals.css";
import "./brand.generated.css";

export async function generateMetadata(): Promise<Metadata> {
  return rootMetadata(await getStore(), siteUrl());
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const store = await getStore();

  return (
    <html lang={store?.locale ?? "es"}>
      <body className="min-h-dvh antialiased">{children}</body>
    </html>
  );
}
