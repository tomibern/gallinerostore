import type { Metadata } from "next";

import { getStore } from "@/lib/api";

import "./globals.css";
import "./brand.generated.css";

export async function generateMetadata(): Promise<Metadata> {
  const store = await getStore();
  return store ? { title: store.name } : {};
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const store = await getStore();

  return (
    <html lang={store?.locale ?? "es"}>
      <body className="min-h-dvh antialiased">{children}</body>
    </html>
  );
}
