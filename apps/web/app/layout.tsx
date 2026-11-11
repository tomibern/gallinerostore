import type { Metadata } from "next";

import { getStore } from "@/lib/api";

import "./globals.css";
import "./brand.generated.css";

export async function generateMetadata(): Promise<Metadata> {
  try {
    const store = await getStore();
    return { title: store.name };
  } catch {
    return {};
  }
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-dvh antialiased">{children}</body>
    </html>
  );
}
