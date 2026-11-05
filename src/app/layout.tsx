import type { Metadata } from "next";
import { Anton, Archivo } from "next/font/google";
import "./globals.css";

const display = Anton({ variable: "--font-display", weight: "400", subsets: ["latin"] });
const body = Archivo({ variable: "--font-body", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Gallinero Store — Camisetas de fútbol",
  description: "Catálogo y stock de camisetas de fútbol. Consultá talles y disponibilidad.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-AR">
      <body className={`${display.variable} ${body.variable} antialiased`}>{children}</body>
    </html>
  );
}
