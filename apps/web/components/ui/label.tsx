import { cn } from "@/lib/utils";

// Etiqueta de un campo del panel (shadcn/ui).
export function Label({ className, ...props }: React.ComponentProps<"label">) {
  return (
    <label className={cn("flex flex-col gap-1.5 text-sm font-semibold", className)} {...props} />
  );
}
