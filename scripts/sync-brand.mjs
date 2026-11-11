// Copia los tokens de la marca configurada en config/store.toml a la web.
// El núcleo trae un tema neutro; la marca del cliente lo pisa.
import { copyFileSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const target = join(root, "apps/web/app/brand.generated.css");

const toml = readFileSync(join(root, "config/store.toml"), "utf8");
const brand = toml.match(/^\s*brand\s*=\s*"([^"]+)"/m)?.[1];
const tokens = brand && join(root, "brand", brand, "tokens.css");

if (tokens && existsSync(tokens)) {
  copyFileSync(tokens, target);
  console.log(`marca: ${brand}`);
} else {
  writeFileSync(target, "/* Sin marca configurada: se usa el tema neutro. */\n");
  console.log("marca: tema neutro");
}
