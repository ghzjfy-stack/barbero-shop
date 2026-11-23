/**
 * Builds Google Merchant Center TSV + sitemap from src/data.js product fields.
 * Run: node scripts/generate-merchant-feed.mjs
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dataUrl = pathToFileURL(join(root, "src/data.js")).href;
const {
  SITE_ORIGIN,
  products,
  absoluteAssetUrl,
  productUrl,
  shippingPriceForProduct,
  resolveOffer,
} = await import(dataUrl);

function tsvEscape(value) {
  return String(value ?? "")
    .replace(/\t/g, " ")
    .replace(/\r?\n/g, " ")
    .trim();
}

function shippingField(price) {
  const ship = shippingPriceForProduct(price);
  return `IL:::${ship.toFixed(2)} ILS`;
}

const headers = [
  "id",
  "title",
  "description",
  "link",
  "image_link",
  "additional_image_link",
  "availability",
  "condition",
  "price",
  "brand",
  "gtin",
  "mpn",
  "identifier_exists",
  "google_product_category",
  "product_type",
  "shipping",
];

const rows = products.map((product) => {
  const offer = resolveOffer(product);
  const extras = (product.images || [])
    .filter((src) => src && src !== product.image)
    .map(absoluteAssetUrl)
    .join(",");

  return [
    product.id,
    product.name,
    product.blurb,
    productUrl(product.id),
    absoluteAssetUrl(product.image),
    extras,
    product.stock > 0 ? "in_stock" : "out_of_stock",
    "new",
    `${offer.price.toFixed(2)} ILS`,
    product.brand,
    product.gtin || "",
    product.mpn || product.sku,
    product.gtin || product.mpn ? "yes" : "no",
    product.googleProductCategory || "",
    product.category,
    shippingField(offer.price),
  ].map(tsvEscape);
});

const feedDir = join(root, "public", "feeds");
mkdirSync(feedDir, { recursive: true });
const feedBody = [headers.join("\t"), ...rows.map((row) => row.join("\t"))].join("\n") + "\n";
const feedPath = join(feedDir, "google-merchant.tsv");
writeFileSync(feedPath, feedBody, "utf8");

const sitemapUrls = [
  { loc: `${SITE_ORIGIN}/`, priority: "1.0" },
  { loc: `${SITE_ORIGIN}/about`, priority: "0.6" },
  ...products.map((product) => ({
    loc: productUrl(product.id),
    priority: product.id === "wahl-senior" ? "0.95" : "0.8",
  })),
];

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${sitemapUrls
  .map(
    ({ loc, priority }) => `  <url>
    <loc>${loc}</loc>
    <changefreq>weekly</changefreq>
    <priority>${priority}</priority>
  </url>`,
  )
  .join("\n")}
</urlset>
`;
writeFileSync(join(root, "public", "sitemap.xml"), sitemap, "utf8");

const robots = `User-agent: *
Allow: /

Sitemap: ${SITE_ORIGIN}/sitemap.xml
`;
writeFileSync(join(root, "public", "robots.txt"), robots, "utf8");

console.log(`Wrote ${feedPath} (${rows.length} products)`);
console.log(`Wrote public/sitemap.xml and public/robots.txt`);
