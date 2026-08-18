# Deploy su Vercel

Impostazioni necessarie sul progetto Vercel (non modificabili da `vercel.json`):

- **Root Directory:** `web` (Settings → General → Root Directory) — l'app Next.js
  sta in `web/`; senza questa Vercel non trova il `package.json`.
- **Production Branch:** `main` (Settings → Git → Deployment) — così ogni push
  su `main` fa un deploy automatico in produzione.
- `vercel.json`: solo `{"framework": "nextjs"}` (rootDirectory NON è valido nel
  file: va impostato dalla dashboard).
