import { cn } from "@/lib/utils";

// Campo de texto del panel (shadcn/ui). 16 px de letra: en iOS, menos que eso hace zoom
// al tocar el campo.
export function Input({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "h-12 w-full border border-border bg-surface px-3 text-base text-text placeholder:text-muted focus-visible:border-accent focus-visible:outline-2 focus-visible:outline-primary aria-invalid:border-error",
        className,
      )}
      {...props}
    />
  );
}
