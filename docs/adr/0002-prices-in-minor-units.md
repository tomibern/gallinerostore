# Precios como entero en la unidad menor de la moneda

El discovery pide precios en pesos y sin decimales. Igual los guardamos como entero en la unidad menor de la moneda (centavos), con la moneda y la cantidad de decimales a mostrar definidas en `config/store.toml`. Así el núcleo sirve a clientes con monedas que usan decimales (USD) y a un ecommerce futuro cuyos medios de pago trabajan en centavos. Gallinero carga «45000», se guarda 4500000 y se muestra «$ 45.000».

## Considered Options

- **Entero en pesos**: más simple hoy, pero cambiarlo después obliga a migrar todos los precios y tocar todo lo que los muestra.
