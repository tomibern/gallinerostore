// Encabezado y cuerpo de una página del panel. En el celular el título ya está en el
// encabezado del panel, así que acá solo se ve en escritorio.
export function AdminPage({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-5">
      <h1 className="sr-only font-display text-4xl font-bold uppercase md:not-sr-only">{title}</h1>
      {children}
    </div>
  );
}
