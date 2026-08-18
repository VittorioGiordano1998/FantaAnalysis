import Link from "next/link";

const SECTIONS = [
  { href: "/", label: "Mega Listone" },
  { href: "/formazioni", label: "Probabili formazioni" },
  { href: "/combinazioni-portieri", label: "Combinazioni portieri" },
];

const BASE_CLASSES =
  "inline-flex h-8 items-center gap-1.5 rounded-full border px-3 text-xs font-medium transition-colors";

/**
 * Navigazione tra le sezioni dell'app, in stile Sphynx. `current` evidenzia la
 * sezione attiva (href).
 */
export function SectionNav({ current }: { current?: string }) {
  return (
    <nav className="flex flex-wrap items-center gap-2">
      {SECTIONS.map((section) => {
        const active = section.href === current;
        return (
          <Link
            key={section.href}
            href={section.href}
            aria-current={active ? "page" : undefined}
            className={`${BASE_CLASSES} ${
              active
                ? "border-primary/50 bg-primary/15 text-primary"
                : "border-border/70 bg-muted/40 text-muted-foreground hover:bg-muted/70 hover:text-foreground"
            }`}
          >
            {section.label}
          </Link>
        );
      })}
    </nav>
  );
}
