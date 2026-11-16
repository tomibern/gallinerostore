import type { StoryItemOut } from "@/lib/api";

import { DiagonalBand } from "./diagonal-band";
import { StoryCard } from "./story-card";

type Props = {
  story: StoryItemOut[];
  labels: { title: string; hint: string; milestones: string; stats: string; funFact: string };
};

// Inclinación de cada tarjeta, para que no queden en fila perfecta.
const TILTS = ["-rotate-3", "rotate-2", "-rotate-1"];

// Historia del producto: hitos como tarjetas que se dan vuelta, cifras y datos
// curiosos. La API ya la manda ordenada por tipo, y vacía si el producto no tiene
// o si la función está apagada: entonces la sección no aparece.
export function ProductStory({ story, labels }: Props) {
  if (story.length === 0) return null;
  const milestones = story.filter((item) => item.kind === "milestone");
  const stats = story.filter((item) => item.kind === "stat");
  const funFacts = story.filter((item) => item.kind === "fun_fact");
  const aside = stats.length > 0 || funFacts.length > 0;

  return (
    <section
      data-testid="product-story"
      aria-labelledby="product-story-title"
      className="relative grid gap-8 overflow-hidden border border-border bg-surface px-4 pt-10 pb-8 md:col-span-2 md:grid-cols-[minmax(0,1fr)_minmax(0,22rem)] md:px-10"
    >
      <DiagonalBand className="absolute inset-x-0 top-0 h-2.5" />
      <div className={`flex min-w-0 flex-col gap-3 ${aside ? "" : "md:col-span-2"}`}>
        <h2
          id="product-story-title"
          className="font-display text-3xl leading-none font-bold text-primary uppercase md:text-4xl"
        >
          {labels.title}
        </h2>
        {milestones.length > 0 && (
          <>
            <p className="text-sm text-muted md:text-base">{labels.hint}</p>
            <ul
              aria-label={labels.milestones}
              className="-mx-4 flex gap-4 overflow-x-auto px-6 py-4 md:mx-0 md:flex-wrap md:gap-6 md:overflow-visible md:px-2"
            >
              {milestones.map((item, index) => (
                <StoryCard
                  key={`${index}-${item.title}`}
                  item={item}
                  tilt={TILTS[index % TILTS.length]}
                />
              ))}
            </ul>
          </>
        )}
      </div>

      {aside && (
        <div className="flex flex-col justify-center gap-4">
          {stats.length > 0 && (
            <ul aria-label={labels.stats} className="grid grid-cols-3 gap-2">
              {stats.map((item, index) => (
                <li
                  key={`${index}-${item.title}`}
                  className="flex flex-col gap-1 border-2 border-primary bg-surface p-3"
                >
                  <span className="font-display text-2xl leading-none font-bold text-primary">
                    {item.title}
                  </span>
                  {item.body && (
                    <span className="text-xs leading-tight text-muted">{item.body}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
          {funFacts.map((item, index) => (
            <aside
              key={`${index}-${item.title}`}
              className="flex -rotate-1 flex-col gap-1.5 bg-primary p-4 text-primary-contrast"
            >
              <h3 className="font-display text-xl font-bold uppercase">{labels.funFact}</h3>
              <p className="text-sm leading-relaxed">{item.title}</p>
              {item.body && <p className="text-sm leading-relaxed">{item.body}</p>}
            </aside>
          ))}
        </div>
      )}
    </section>
  );
}
