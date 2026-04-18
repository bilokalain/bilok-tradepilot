#!/usr/bin/env node
/**
 * Bilok-TradePilot — Générateur PDF Livre Professionnel
 * Usage: node docs/build-pdf.js
 *
 * Construit un HTML complet avec page de garde bleu marine,
 * photo auteur, typographie Georgia, puis génère le PDF via Puppeteer.
 */
const fs = require("fs");
const path = require("path");
const markdownIt = require("markdown-it");
const texmath = require("markdown-it-texmath");
const katex = require("katex");

const DOCS = path.resolve(__dirname);
const INPUT = path.join(DOCS, "LIVRE_COMPLET.md");
const OUTPUT = path.join(DOCS, "Bilok-TradePilot_Livre.pdf");
const PHOTO = path.join(__dirname, "..", "frontend", "public", "author.jpg");
const KATEX_CSS = path.join(__dirname, "..", "node_modules", "katex", "dist", "katex.min.css");

// Encode photo en base64 pour l'embarquer dans le HTML
const photoBase64 = fs.existsSync(PHOTO)
  ? `data:image/jpeg;base64,${fs.readFileSync(PHOTO).toString("base64")}`
  : null;

// Lire le CSS KaTeX et embarquer les fonts en base64
let katexCss = fs.readFileSync(KATEX_CSS, "utf-8");
// Résoudre les chemins relatifs des fonts KaTeX
const katexFontsDir = path.join(__dirname, "..", "node_modules", "katex", "dist", "fonts");
katexCss = katexCss.replace(/url\(fonts\//g, `url(${katexFontsDir}/`);

const md = markdownIt({ html: true, typographer: true });
md.use(texmath, {
  engine: katex,
  delimiters: "dollars",
  katexOptions: { throwOnError: false, displayMode: false },
});

// ─── Lire et parser le markdown ───
const raw = fs.readFileSync(INPUT, "utf-8");

// Séparer : tout avant "# AVANT-PROPOS" = front matter (couverture, à propos, dédicaces)
// Le reste = corps du livre
const avantProposIdx = raw.indexOf("# AVANT-PROPOS");
const frontMatter = raw.substring(0, avantProposIdx);
const bodyRaw = raw.substring(avantProposIdx);

// ─── Construire les sections front-matter ───
function extractSection(text, startMarker, endMarkers) {
  const startIdx = text.indexOf(startMarker);
  if (startIdx === -1) return "";
  let endIdx = text.length;
  for (const em of endMarkers) {
    const idx = text.indexOf(em, startIdx + startMarker.length);
    if (idx !== -1 && idx < endIdx) endIdx = idx;
  }
  return text.substring(startIdx, endIdx).trim();
}

const aboutSection = extractSection(frontMatter, "## À PROPOS DE L'AUTEUR", ["## DÉDICACES"]);
const dedicaceSection = extractSection(frontMatter, "## DÉDICACES", ["# AVANT-PROPOS", "# PARTIE"]);

// ─── Corps : découper par # PARTIE (H1) pour forcer les sauts de page ───
function splitByParties(text) {
  const parts = [];
  const lines = text.split("\n");
  let current = [];

  for (const line of lines) {
    if (/^# (?:PARTIE |CONCLUSION|ANNEXES|AVANT-PROPOS|INTRODUCTION|REVUE DE LA LITTÉRATURE)/.test(line) && current.length > 0) {
      parts.push(current.join("\n"));
      current = [line];
    } else {
      current.push(line);
    }
  }
  if (current.length > 0) parts.push(current.join("\n"));
  return parts;
}

const bodyParts = splitByParties(bodyRaw);

// ─── Générer le HTML ───
function renderMd(text) {
  return md.render(text);
}

const CSS = `
/* ===== RESET ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ===== PAGE ===== */
@page {
  size: A4;
  margin: 25mm 20mm 28mm 28mm; /* top right bottom left(reliure) */
}

@page :first {
  margin: 0;
}

/* ===== TYPOGRAPHIE ===== */
body {
  font-family: "Georgia", "Times New Roman", serif;
  font-size: 11pt;
  line-height: 1.65;
  color: #1a1a1a;
  text-align: justify;
  hyphens: auto;
  -webkit-hyphens: auto;
  orphans: 3;
  widows: 3;
}

/* ===== PAGE DE GARDE ===== */
.cover {
  width: 210mm;
  height: 297mm;
  background: #0d1b2a;
  color: #c9a84c;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  page-break-after: always;
  padding: 30mm 20mm;
  position: relative;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

.cover .cover-dots {
  font-size: 10pt;
  letter-spacing: 12px;
  margin-bottom: 30px;
  color: #c9a84c;
}

.cover .cover-title {
  font-family: "Georgia", "Times New Roman", serif;
  font-size: 38pt;
  font-weight: 700;
  letter-spacing: 2px;
  margin-bottom: 20px;
  color: #c9a84c;
}

.cover .cover-line {
  width: 60px;
  height: 1.5px;
  background: #c9a84c;
  margin: 0 auto 20px;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

.cover .cover-name {
  font-family: "Georgia", serif;
  font-size: 22pt;
  font-weight: 400;
  letter-spacing: 4px;
  color: #c9a84c;
  margin-bottom: 20px;
}

.cover .cover-subtitle {
  font-family: "Georgia", serif;
  font-size: 12pt;
  font-weight: 400;
  font-style: italic;
  color: #c9a84c;
  opacity: 0.85;
  margin-bottom: 35px;
  max-width: 80%;
  line-height: 1.6;
}

.cover .pipeline {
  font-family: "SF Mono", "Fira Code", "Consolas", monospace;
  font-size: 7.5pt;
  color: #c9a84c;
  line-height: 1.6;
  white-space: pre;
  text-align: center;
  margin-bottom: 40px;
  opacity: 0.9;
}

.cover .cover-diamond {
  font-size: 8pt;
  color: #c9a84c;
  margin-bottom: 30px;
}

.cover .cover-author {
  font-family: "Georgia", serif;
  font-size: 14pt;
  font-weight: 400;
  color: #c9a84c;
  letter-spacing: 2px;
  margin-bottom: 8px;
}

.cover .cover-edition {
  font-family: "Georgia", serif;
  font-size: 10pt;
  color: #c9a84c;
  opacity: 0.7;
  font-style: italic;
}

/* ===== À PROPOS ===== */
.about-page {
  page-break-before: always;
  page-break-after: always;
  padding: 0;
}

.about-page h2 {
  text-align: center;
  border-bottom: none;
  margin-bottom: 20px;
}

.about-photo {
  display: block;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  margin: 0 auto 24px;
  border: 3px solid #1b2a4a;
}

/* ===== DÉDICACES ===== */
.dedicace-page {
  page-break-before: always;
  page-break-after: always;
}

.dedicace-page h2 {
  text-align: center;
  border-bottom: none;
  margin-bottom: 30px;
}

.dedicace-page h3 {
  text-align: center;
  margin-top: 30px;
}

.dedicace-page p {
  text-align: center;
  font-style: italic;
  line-height: 1.8;
}

.dedicace-page blockquote {
  text-align: center;
  border-left: none;
  background: none;
  font-size: 10pt;
  color: #555;
}

/* ===== TITRES ===== */
h1 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 22pt;
  font-weight: 700;
  color: #0d1b2a;
  text-align: center;
  margin: 40px 0 12px;
  padding-bottom: 0;
  border-bottom: none;
  letter-spacing: 1px;
  text-transform: uppercase;
  text-align: left;
  page-break-before: always;
}

/* Pas de saut pour le H1 à l'intérieur de la cover (géré par .cover) */
.cover h1 {
  page-break-before: avoid;
}

h2 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 15pt;
  font-weight: 600;
  color: #1b2a4a;
  margin-top: 32px;
  margin-bottom: 14px;
  padding-bottom: 5px;
  border-bottom: 1.5px solid #1b2a4a;
  page-break-before: always;
  page-break-after: avoid;
}

/* Pas de saut de page pour les h2 à l'intérieur des pages spéciales */
.about-page h2,
.dedicace-page h2,
.epigraph h2 {
  page-break-before: avoid;
}

h3 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 12.5pt;
  font-weight: 600;
  color: #2c3e50;
  margin-top: 24px;
  margin-bottom: 8px;
  page-break-after: avoid;
}

h4 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 11pt;
  font-weight: 600;
  color: #34495e;
  margin-top: 18px;
  margin-bottom: 6px;
  page-break-after: avoid;
}

/* ===== PARAGRAPHES ===== */
p {
  margin-top: 0;
  margin-bottom: 10px;
}

/* ===== SÉPARATEURS ===== */
hr {
  border: none;
  border-top: 0.5px solid #ccc;
  margin: 20px auto;
  width: 30%;
}

/* ===== LISTES ===== */
ul, ol {
  margin: 6px 0 12px;
  padding-left: 22px;
}
li { margin-bottom: 3px; }

/* ===== BLOCKQUOTE ===== */
blockquote {
  margin: 16px 24px;
  padding: 10px 18px;
  border-left: 3px solid #1b2a4a;
  background: #f8f9fa;
  font-style: italic;
  color: #333;
  page-break-inside: avoid;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
blockquote p { margin-bottom: 4px; }

/* ===== TABLEAUX ===== */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0;
  font-size: 9.5pt;
  page-break-inside: avoid;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
thead { background-color: #1b2a4a; color: #fff; }
th {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-weight: 600;
  padding: 7px 10px;
  text-align: left;
  font-size: 9pt;
  letter-spacing: 0.3px;
}
td {
  padding: 6px 10px;
  border-bottom: 1px solid #e0e0e0;
  vertical-align: top;
}
tbody tr:nth-child(even) {
  background-color: #f3f4f6;
}
tbody tr:nth-child(odd) {
  background-color: #ffffff;
}

/* ===== CODE ===== */
pre {
  background: #f4f4f4;
  border: 1px solid #ddd;
  border-radius: 3px;
  padding: 10px 14px;
  font-size: 8.5pt;
  line-height: 1.5;
  overflow-x: auto;
  page-break-inside: avoid;
  margin: 10px 0;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
code {
  font-family: "SF Mono", "Fira Code", Consolas, monospace;
  font-size: 9pt;
  background: #f0f0f0;
  padding: 1px 3px;
  border-radius: 2px;
}
pre code { background: none; padding: 0; }

/* ===== LIENS ===== */
a { color: #1b2a4a; text-decoration: none; }

strong { font-weight: 700; color: #111; }

/* ===== PARTIE (H1) — nouvelle page, titre centré verticalement ===== */
.partie-break {
  page-break-before: always;
  break-before: page;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  text-align: center;
}

.partie-break h1 {
  text-align: center;
  margin: 0;
}

.partie-break h1 + h2 {
  page-break-before: always;
}

/* ===== ÉPIGRAPHE ===== */
.epigraph {
  page-break-before: always;
  text-align: center;
  padding-top: 120px;
  font-style: italic;
  font-size: 12pt;
  color: #444;
  page-break-after: always;
}
.epigraph blockquote {
  border-left: none;
  background: none;
  text-align: center;
}
`;

// ─── Assembler le HTML complet ───
let html = `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>${katexCss}</style>
<style>${CSS}</style>
</head>
<body>

<!-- ===== PAGE DE GARDE ===== -->
<div class="cover">
  <div class="cover-dots">&#9670; &nbsp; &#9670; &nbsp; &#9670;</div>
  <div class="cover-title">BILOK-TRADEPILOT</div>
  <div class="cover-line"></div>
  <div class="cover-name">L e &nbsp; S y s t è m e</div>
  <div class="cover-subtitle">Architecture d'un Pipeline de Trading Automatisé<br>à 6 Modules avec Feedback Loop</div>
  <div class="pipeline">
┌──────────┐    ┌───────────┐    ┌─────────┐    ┌───────────┐    ┌─────────────┐    ┌─────────────┐
│ SCANNER  │──▶│ ANALYSEUR │──▶│ SCORING │──▶│ EXÉCUTION │──▶│PORTEFEUILLE │──▶│ PERFORMANCE │
│ 10 crit. │    │ 12+ strat.│    │ Score V2│    │  Brokers  │    │ Risk Parity │    │ P&L Attrib. │
└──────────┘    └───────────┘    └─────────┘    └───────────┘    └─────────────┘    └──────┬──────┘
      ▲                                                                                    │
      └─────────────────────────── feedback loop ─────────────────────────────────────────┘
  </div>
  <div class="cover-diamond">&#9670;</div>
  <div class="cover-author">Alain Bilok Evang</div>
  <div class="cover-edition">Première édition — 2026</div>
</div>

<!-- ===== À PROPOS ===== -->
<div class="about-page">
${photoBase64 ? `<img class="about-photo" src="${photoBase64}" alt="Photo de l'auteur">` : ""}
${renderMd(aboutSection)}
</div>

<!-- ===== DÉDICACES ===== -->
<div class="dedicace-page">
${renderMd(dedicaceSection)}
</div>

<!-- ===== ÉPIGRAPHE ===== -->
<div class="epigraph">
<blockquote><p><em>"Les marchés ne récompensent pas l'intelligence. Ils récompensent la discipline."</em></p></blockquote>
</div>

`;

// ─── Corps du livre : chaque PARTIE commence sur une nouvelle page ───
for (let i = 0; i < bodyParts.length; i++) {
  const part = bodyParts[i].trim();
  const isPartie = /^# (?:PARTIE |CONCLUSION|ANNEXES|AVANT-PROPOS|INTRODUCTION|REVUE DE LA LITTÉRATURE)/.test(part);
  if (isPartie) {
    // Séparer le titre H1 (première ligne) du contenu qui suit
    const lines = part.split("\n");
    const titleLine = lines[0];
    const rest = lines.slice(1).join("\n").trim();
    // Page titre centrée
    html += `<div class="partie-break">\n${renderMd(titleLine)}\n</div>\n\n`;
    // Contenu de la partie (enchaîné sans page blanche)
    if (rest) {
      html += `<div>\n${renderMd(rest)}\n</div>\n\n`;
    }
  } else {
    html += `<div>\n${renderMd(part)}\n</div>\n\n`;
  }
}

// Mentions légales (déjà dans bodyParts)
html += `
</body>
</html>`;

// ─── Écrire le HTML temporaire pour debug ───
const htmlPath = path.join(DOCS, "_livre_temp.html");
fs.writeFileSync(htmlPath, html, "utf-8");

// ─── Générer le PDF avec Puppeteer ───
async function generatePDF() {
  console.log("📖 Génération du PDF livre professionnel...");
  console.log(`   Markdown : ${INPUT}`);
  console.log(`   Photo    : ${photoBase64 ? "✓ intégrée" : "✗ absente"}`);

  // md-to-pdf installe puppeteer, on le réutilise
  let puppeteer;
  try {
    puppeteer = require("puppeteer");
  } catch {
    // Fallback : puppeteer installé par md-to-pdf dans node_modules
    puppeteer = require(path.join(__dirname, "..", "node_modules", "puppeteer-core"));
  }

  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage();

  await page.setContent(html, { waitUntil: "networkidle0" });

  await page.pdf({
    path: OUTPUT,
    format: "A4",
    printBackground: true,
    margin: { top: "25mm", right: "20mm", bottom: "28mm", left: "28mm" },
    displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate: `
      <div style="width:100%; font-size:8px; font-family:Georgia,serif; display:flex; justify-content:space-between; padding:0 28mm; color:#999;">
        <span style="font-style:italic;">Bilok-TradePilot — Le Système</span>
        <span><span class="pageNumber"></span></span>
      </div>
    `,
  });

  await browser.close();

  // Nettoyer le HTML temporaire
  fs.unlinkSync(htmlPath);

  const sizeMB = (fs.statSync(OUTPUT).size / 1024 / 1024).toFixed(1);
  console.log(`\n✅ PDF généré : ${OUTPUT}`);
  console.log(`   Taille : ${sizeMB} Mo`);
}

generatePDF().catch((err) => {
  console.error("❌ Erreur :", err.message);
  process.exit(1);
});
