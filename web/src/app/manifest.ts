import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "FantaOptimizer — Listone",
    short_name: "Fanta Listone",
    description: "Listone dell'asta Fantacalcio in stile Sphynx",
    start_url: "/",
    display: "standalone",
    background_color: "#171817",
    theme_color: "#171817",
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
