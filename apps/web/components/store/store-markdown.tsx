import Markdown, { type Components } from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

// Lo que se dibuja del Markdown que edita el admin. Sin imágenes ni tablas (las
// fotos van por /media), y sin h1: el título es de la página. Lo que no está en la
// lista se reemplaza por su texto.
const ALLOWED = ["h2", "h3", "p", "ul", "ol", "li", "strong", "em", "a", "br"];

// Solo estilos: ningún componente cambia links ni atributos.
const COMPONENTS: Components = {
  h2: ({ children }) => (
    <h2 className="font-display mt-8 text-2xl font-bold uppercase first:mt-0 md:text-3xl">
      {children}
    </h2>
  ),
  h3: ({ children }) => <h3 className="font-display mt-6 text-xl font-bold">{children}</h3>,
  p: ({ children }) => <p className="mt-3 leading-relaxed first:mt-0">{children}</p>,
  ul: ({ children }) => <ul className="mt-3 list-disc space-y-1 pl-6">{children}</ul>,
  ol: ({ children }) => <ol className="mt-3 list-decimal space-y-2 pl-6">{children}</ol>,
  a: ({ href, children }) => (
    <a href={href} className="font-semibold text-primary underline underline-offset-4">
      {children}
    </a>
  ),
};

// Markdown de la tienda («Cómo comprar», preguntas frecuentes). Se dibuja en el
// servidor: no manda JavaScript. El HTML crudo se descarta y rehype-sanitize va al
// final de la cadena, así nada que agregue un plugin o un componente se cuela.
export function StoreMarkdown({ children }: { children: string }) {
  return (
    <Markdown
      skipHtml
      allowedElements={ALLOWED}
      unwrapDisallowed
      rehypePlugins={[rehypeSanitize]}
      components={COMPONENTS}
    >
      {children}
    </Markdown>
  );
}
