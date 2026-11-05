import { buildInstagramLink } from "@/lib/contact";

const instagramUser = process.env.NEXT_PUBLIC_INSTAGRAM_USER ?? "gallinerostore14";

export default function Home() {
  return (
    <main className="relative grid min-h-dvh place-items-center overflow-hidden px-6">
      {/* Banda diagonal: elemento gráfico provisorio hasta la etapa de diseño */}
      <div
        aria-hidden
        className="bg-banda absolute top-1/2 left-1/2 h-40 w-[200vmax] -translate-x-1/2 -translate-y-1/2 -rotate-[28deg]"
      />
      <div className="relative text-center">
        <h1 className="font-display text-7xl leading-none tracking-tight uppercase sm:text-9xl">
          Gallinero
          <br />
          Store
        </h1>
        <p className="mt-6 text-lg">Catálogo online · Próximamente</p>
        <a
          href={buildInstagramLink(instagramUser)}
          className="border-ink hover:bg-ink hover:text-paper mt-4 inline-block border-2 px-5 py-2 font-semibold transition-colors"
        >
          @{instagramUser}
        </a>
      </div>
    </main>
  );
}
