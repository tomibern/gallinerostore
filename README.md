# Gallinero Store

Catálogo online de camisetas de fútbol para [@gallinerostore14](https://instagram.com/gallinerostore14).
Los visitantes consultan prendas, talles y stock; un único administrador gestiona el catálogo.

> 🚧 En construcción.

## Stack

- **Next.js 15** (App Router, Server Components, Server Actions) + **TypeScript**
- **Tailwind CSS v4**
- **PostgreSQL** (Neon) + **Drizzle ORM** — _próximamente_
- **Cloudinary** para imágenes — _próximamente_
- **Auth.js** para el panel admin — _próximamente_
- **Vitest** + **Playwright**, CI con **GitHub Actions**, deploy en **Vercel**

## Desarrollo local

Requisitos: Node 22+.

```bash
cp .env.example .env.local   # completar variables
npm install
npm run dev                  # http://localhost:3000
```

| Script                       | Descripción               |
| ---------------------------- | ------------------------- |
| `npm run dev`                | Servidor de desarrollo    |
| `npm run build`              | Build de producción       |
| `npm run lint` / `typecheck` | ESLint / chequeo de tipos |
| `npm test`                   | Tests unitarios (Vitest)  |
| `npm run format`             | Formatea con Prettier     |

## Roadmap

- [x] Setup: TypeScript, lint, formato, tests, CI
- [ ] Base de datos y modelo (productos, imágenes, variantes por talle, movimientos de stock)
- [ ] Catálogo público con filtros por URL
- [ ] Panel admin: login, ABM de prendas, subida de imágenes, stock con historial
- [ ] Diseño visual
- [ ] Tests E2E, dominio y lanzamiento
