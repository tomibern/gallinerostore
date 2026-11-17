import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

// Botón del panel (shadcn/ui, con los tokens de la marca). Mínimo 44 px de alto: se usa
// con el dedo en el celular.
export const buttonVariants = cva(
  "inline-flex min-h-11 items-center justify-center gap-2 px-4 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:pointer-events-none disabled:opacity-60",
  {
    variants: {
      variant: {
        primary: "bg-primary text-primary-contrast hover:bg-primary-strong",
        outline: "border-2 border-accent bg-surface text-accent hover:bg-bg",
        link: "min-h-11 px-0 text-accent underline underline-offset-4 hover:text-primary",
      },
      size: { default: "", lg: "min-h-13 text-base" },
    },
    defaultVariants: { variant: "primary", size: "default" },
  },
);

export function Button({
  className,
  variant,
  size,
  ...props
}: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants>) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
