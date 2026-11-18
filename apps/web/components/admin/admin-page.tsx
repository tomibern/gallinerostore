// Encabezado y cuerpo de una página del panel. En el celular el título ya está en el
// encabezado del panel, así que acá solo se ve en escritorio; las acciones (por ejemplo,
// elegir el período) van al lado del título en escritorio y arriba de todo en el celular.
export function AdminPage({
  title,
  actions,
  children,
}: {
  title: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-center">
        <h1 className="sr-only font-display text-4xl font-bold uppercase md:not-sr-only md:flex-1">
          {title}
        </h1>
        {actions}
      </div>
      {children}
    </div>
  );
}
