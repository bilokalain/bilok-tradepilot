#!/usr/bin/env node
/**
 * Bilok-TradePilot — Générateur PDF Livre Professionnel
 * Usage: node docs/build-pdf.js
 *
 * Deux passes Puppeteer :
 *   1. Couverture plein cadre (0 marges, 0 footer)
 *   2. Contenu avec marges, footer et numérotation
 * Fusion via pdf-lib.
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

const photoBase64 = fs.existsSync(PHOTO)
  ? `data:image/jpeg;base64,${fs.readFileSync(PHOTO).toString("base64")}`
  : null;

let katexCss = fs.readFileSync(KATEX_CSS, "utf-8");
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
const avantProposIdx = raw.indexOf("# AVANT-PROPOS");
const frontMatter = raw.substring(0, avantProposIdx);
const bodyRaw = raw.substring(avantProposIdx);

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

// Découper le body par # PARTIE / # CONCLUSION / etc.
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
function renderMd(text) { return md.render(text); }

// ═══════════════════════════════════════════════════════════
// CSS — optimisé pour zéro pages blanches, zéro texte coupé
// ═══════════════════════════════════════════════════════════
const CSS = `
*, *::before, *::after { box-sizing: border-box; }

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
  margin: 0;
  padding: 0;
}

/* ── À PROPOS ── */
.about-page { padding-top: 20px; page-break-after: always; }
.about-page h2 { text-align: center; border-bottom: none; margin-bottom: 20px; page-break-before: avoid; }
.about-photo {
  display: block; width: 120px; height: 120px; border-radius: 50%;
  object-fit: cover; margin: 0 auto 24px; border: 3px solid #1b2a4a;
}

/* ── DÉDICACES ── */
.dedicace-page { padding-top: 40px; page-break-before: always; page-break-after: always; }
.dedicace-page h2 { text-align: center; border-bottom: none; margin-bottom: 30px; page-break-before: avoid; }
.dedicace-page h3 { text-align: center; margin-top: 30px; }
.dedicace-page p { text-align: center; font-style: italic; line-height: 1.8; }
.dedicace-page blockquote { text-align: center; border-left: none; background: none; font-size: 10pt; color: #555; }

/* ── ÉPIGRAPHE ── */
.epigraph {
  page-break-before: always; page-break-after: always;
  padding-top: 120px; text-align: center;
  font-style: italic; font-size: 12pt; color: #444;
}
.epigraph blockquote { border-left: none; background: none; text-align: center; }

/* ── TITRES DE PARTIES (centrés sur leur page) ── */
.partie-title-page {
  page-break-before: always;
  page-break-after: always;
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  height: 70vh; text-align: center;
}
.partie-title-page h1 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 22pt; font-weight: 700; color: #0d1b2a;
  letter-spacing: 1.5px; text-transform: uppercase;
  border-bottom: 2px solid #c9a84c; padding-bottom: 10px;
  page-break-before: avoid; margin: 0;
}

/* ── TITRES GÉNÉRAUX ── */
h1 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 20pt; font-weight: 700; color: #0d1b2a;
  margin: 30px 0 12px; letter-spacing: 1px;
  text-transform: uppercase; text-align: left;
  border-bottom: 2px solid #c9a84c; padding-bottom: 6px;
  page-break-after: avoid;
}

h2 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 14pt; font-weight: 600; color: #1b2a4a;
  margin: 28px 0 10px; padding-bottom: 4px;
  border-bottom: 1px solid #1b2a4a;
  page-break-after: avoid;
}

h3 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 12pt; font-weight: 600; color: #2c3e50;
  margin: 20px 0 6px;
  page-break-after: avoid;
}

h4 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 11pt; font-weight: 600; color: #34495e;
  margin: 16px 0 4px;
  page-break-after: avoid;
}

/* ── PARAGRAPHES ── */
p { margin: 0 0 8px; }

/* ── SÉPARATEURS ── */
hr { border: none; border-top: 0.5px solid #ccc; margin: 16px auto; width: 30%; }

/* ── LISTES ── */
ul, ol { margin: 4px 0 10px; padding-left: 22px; }
li { margin-bottom: 2px; }

/* ── CITATIONS ── */
blockquote {
  margin: 12px 20px; padding: 8px 16px;
  border-left: 3px solid #1b2a4a; background: #f8f9fa;
  font-style: italic; color: #333;
  page-break-inside: avoid;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
blockquote p { margin-bottom: 3px; }

/* ── TABLEAUX ── */
table {
  width: 100%; border-collapse: collapse; margin: 12px 0;
  font-size: 9pt; page-break-inside: avoid;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
thead { background-color: #1b2a4a; color: #fff; }
th {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-weight: 600; padding: 6px 8px; text-align: left;
  font-size: 8.5pt; letter-spacing: 0.3px;
}
td { padding: 5px 8px; border-bottom: 1px solid #e0e0e0; vertical-align: top; }
tbody tr:nth-child(even) { background-color: #f3f4f6; }

/* ── CODE ── */
pre {
  background: #f4f4f4; border: 1px solid #ddd; border-radius: 3px;
  padding: 8px 12px; font-size: 8pt; line-height: 1.4;
  overflow-x: auto; page-break-inside: avoid; margin: 8px 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
code {
  font-family: "SF Mono", "Fira Code", Consolas, monospace;
  font-size: 8.5pt; background: #f0f0f0; padding: 1px 3px; border-radius: 2px;
}
pre code { background: none; padding: 0; }

a { color: #1b2a4a; text-decoration: none; }
strong { font-weight: 700; color: #111; }

/* ── KaTeX display ── */
.katex-display { margin: 10px 0; }
`;

// ═══════════════════════════════════════
// COUVERTURE HTML (page séparée)
// ═══════════════════════════════════════
const coverHtml = `<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 210mm; height: 297mm; margin: 0;
  background: #0d1b2a; color: #c9a84c;
  font-family: "Georgia", serif;
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  text-align: center;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.dots { font-size: 10pt; letter-spacing: 12px; margin-bottom: 30px; }
.title { font-size: 36pt; font-weight: 700; letter-spacing: 2px; margin-bottom: 18px; }
.line { width: 60px; height: 1.5px; background: #c9a84c; margin: 0 auto 18px; }
.name { font-size: 20pt; letter-spacing: 5px; margin-bottom: 18px; }
.subtitle { font-size: 11pt; font-style: italic; opacity: 0.85; line-height: 1.6; margin-bottom: 30px; }
.pipeline {
  font-family: "Courier New", monospace; font-size: 7pt; color: #c9a84c;
  white-space: pre; line-height: 1.5; text-align: center; opacity: 0.9; margin-bottom: 35px;
}
.diamond { font-size: 8pt; margin-bottom: 25px; }
.author { font-size: 13pt; letter-spacing: 2px; margin-bottom: 6px; }
.edition { font-size: 9.5pt; opacity: 0.65; font-style: italic; }
</style></head><body>
<div class="dots">&#9670; &nbsp; &#9670; &nbsp; &#9670;</div>
<div class="title">BILOK-TRADEPILOT</div>
<div class="line"></div>
<div class="name">L e &nbsp; S y s t è m e</div>
<div class="subtitle">Architecture d'un Pipeline de Trading Automatisé<br>à 6 Modules avec Feedback Loop</div>
<div class="pipeline">
┌──────────┐    ┌───────────┐    ┌─────────┐    ┌───────────┐    ┌─────────────┐    ┌─────────────┐
│ SCANNER  │──▶│ ANALYSEUR │──▶│ SCORING │──▶│ EXÉCUTION │──▶│PORTEFEUILLE │──▶│ PERFORMANCE │
│ 10 crit. │    │ 12+ strat.│    │ Score V2│    │  Brokers  │    │ Risk Parity │    │ P&L Attrib. │
└──────────┘    └───────────┘    └─────────┘    └───────────┘    └─────────────┘    └──────┬──────┘
      ▲                                                                                    │
      └─────────────────────────── feedback loop ─────────────────────────────────────────┘
</div>
<div class="diamond">&#9670;</div>
<div class="author">Alain Bilok Evang</div>
<div class="edition">Première édition — 2026</div>
</body></html>`;

// ═══════════════════════════════════════
// CONTENU HTML (tout sauf la couverture)
// ═══════════════════════════════════════
let contentHtml = `<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8">
<style>${katexCss}</style>
<style>${CSS}</style>
</head><body>

<!-- À PROPOS -->
<div class="about-page">
${photoBase64 ? `<img class="about-photo" src="${photoBase64}" alt="Photo de l'auteur">` : ""}
${renderMd(aboutSection)}
</div>

<!-- DÉDICACES -->
<div class="dedicace-page">
${renderMd(dedicaceSection)}
</div>

<!-- ÉPIGRAPHE -->
<div class="epigraph">
<blockquote><p><em>"Les marchés ne récompensent pas l'intelligence. Ils récompensent la discipline."</em></p></blockquote>
</div>

`;

// Corps du livre
for (let i = 0; i < bodyParts.length; i++) {
  const part = bodyParts[i].trim();
  const isPartie = /^# (?:PARTIE |CONCLUSION|ANNEXES|AVANT-PROPOS|INTRODUCTION|REVUE DE LA LITTÉRATURE)/.test(part);
  if (isPartie) {
    const lines = part.split("\n");
    const titleLine = lines[0];
    const rest = lines.slice(1).join("\n").trim();
    // Page titre centrée
    contentHtml += `<div class="partie-title-page">${renderMd(titleLine)}</div>\n`;
    // Contenu qui suit
    if (rest) contentHtml += `<div>${renderMd(rest)}</div>\n`;
  } else {
    contentHtml += `<div>${renderMd(part)}</div>\n`;
  }
}

contentHtml += `</body></html>`;

// ═══════════════════════════════════════
// GÉNÉRATION PDF — 2 passes + fusion
// ═══════════════════════════════════════
async function generatePDF() {
  console.log("📖 Génération du PDF livre professionnel...");
  console.log(`   Markdown : ${INPUT}`);
  console.log(`   Photo    : ${photoBase64 ? "✓ intégrée" : "✗ absente"}`);

  const puppeteer = require("puppeteer");
  const { PDFDocument } = require("pdf-lib");

  const browser = await puppeteer.launch({ headless: "new", args: ["--no-sandbox"] });

  // PASSE 1 — Couverture (plein cadre, zéro marge, zéro footer)
  console.log("   Passe 1  : couverture...");
  const pageCover = await browser.newPage();
  await pageCover.setContent(coverHtml, { waitUntil: "networkidle0" });
  const coverBytes = await pageCover.pdf({
    format: "A4", printBackground: true,
    margin: { top: "0", right: "0", bottom: "0", left: "0" },
    displayHeaderFooter: false,
  });
  await pageCover.close();

  // PASSE 2 — Contenu (marges, footer, numérotation)
  console.log("   Passe 2  : contenu...");
  const pageContent = await browser.newPage();
  await pageContent.setContent(contentHtml, { waitUntil: "networkidle0" });
  const contentBytes = await pageContent.pdf({
    format: "A4", printBackground: true,
    margin: { top: "22mm", right: "18mm", bottom: "22mm", left: "24mm" },
    displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate: `
      <div style="width:100%; font-size:8px; font-family:Georgia,serif; display:flex; justify-content:space-between; padding:0 24mm; color:#aaa;">
        <span style="font-style:italic;">Bilok-TradePilot — Le Système</span>
        <span><span class="pageNumber"></span></span>
      </div>
    `,
  });
  await pageContent.close();
  await browser.close();

  // FUSION — Cover (1 page) + Contenu
  console.log("   Fusion   : couverture + contenu...");
  const coverDoc = await PDFDocument.load(coverBytes);
  const contentDoc = await PDFDocument.load(contentBytes);
  const finalDoc = await PDFDocument.create();

  const [coverPage] = await finalDoc.copyPages(coverDoc, [0]);
  finalDoc.addPage(coverPage);

  const contentPageCount = contentDoc.getPageCount();
  for (let i = 0; i < contentPageCount; i++) {
    const [p] = await finalDoc.copyPages(contentDoc, [i]);
    finalDoc.addPage(p);
  }

  finalDoc.setTitle("Bilok-TradePilot — Le Système");
  finalDoc.setAuthor("Alain Bilok Evang");
  finalDoc.setSubject("Architecture d'un Pipeline de Trading Automatisé à 6 Modules avec Feedback Loop");
  finalDoc.setCreator("Bilok-TradePilot PDF Generator");

  const finalBytes = await finalDoc.save();
  fs.writeFileSync(OUTPUT, finalBytes);

  const sizeMB = (finalBytes.length / 1024 / 1024).toFixed(1);
  console.log(`\n✅ PDF généré : ${OUTPUT}`);
  console.log(`   Pages    : 1 (couverture) + ${contentPageCount} (contenu) = ${1 + contentPageCount}`);
  console.log(`   Taille   : ${sizeMB} Mo`);
}

generatePDF().catch((err) => {
  console.error("❌ Erreur :", err.message);
  process.exit(1);
});
