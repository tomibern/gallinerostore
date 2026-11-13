// Copia a la web lo que pone el cliente: la marca configurada en
// config/store.toml (tokens, logo, tipografías) y los reemplazos de textos de
// config/texts.json. El núcleo trae un tema neutro y textos neutros; lo del
// cliente los pisa. Todo lo que escribe está en .gitignore.
import {
  copyFileSync,
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const web = join(root, "apps/web");

const toml = readFileSync(join(root, "config/store.toml"), "utf8");
const brand = toml.match(/^\s*brand\s*=\s*"([^"]+)"/m)?.[1];
const brandDir = brand ? join(root, "brand", brand) : null;

// Tokens de color y tipografías.
const tokensTarget = join(web, "app/brand.generated.css");
const tokens = brandDir && join(brandDir, "tokens.css");
if (tokens && existsSync(tokens)) {
  copyFileSync(tokens, tokensTarget);
  console.log(`marca: ${brand}`);
} else {
  writeFileSync(tokensTarget, "/* Sin marca configurada: se usa el tema neutro. */\n");
  console.log("marca: tema neutro");
}

// Recursos públicos (logo, fuentes): brand/<marca>/public → /brand/*.
const publicTarget = join(web, "public/brand");
rmSync(publicTarget, { recursive: true, force: true });
const publicSource = brandDir && join(brandDir, "public");
if (publicSource && existsSync(publicSource)) {
  cpSync(publicSource, publicTarget, { recursive: true });
}

// Logo: el primero que exista, servido desde /brand/.
const logo = ["logo.svg", "logo.webp", "logo.png"].find((name) =>
  existsSync(join(publicTarget, name)),
);
writeFileSync(
  join(web, "lib/brand.generated.json"),
  `${JSON.stringify({ logo: logo ? `/brand/${logo}` : null }, null, 2)}\n`,
);

// Reemplazos de textos del cliente (opcional).
const textsSource = join(root, "config/texts.json");
const textsTarget = join(web, "lib/texts/overrides.generated.json");
mkdirSync(dirname(textsTarget), { recursive: true });
if (existsSync(textsSource)) {
  // Se parsea para fallar acá, con un mensaje claro, si el JSON está roto.
  const texts = JSON.parse(readFileSync(textsSource, "utf8"));
  writeFileSync(textsTarget, `${JSON.stringify(texts, null, 2)}\n`);
  console.log("textos: con reemplazos del cliente");
} else {
  writeFileSync(textsTarget, "{}\n");
  console.log("textos: los del núcleo");
}
