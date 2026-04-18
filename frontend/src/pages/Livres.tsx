import { useState, useEffect, useRef } from "react";
import { BookOpen, Download, ChevronRight, Search } from "lucide-react";

// Structure du livre
const BOOK_STRUCTURE = [
  {
    part: "AVANT-PROPOS",
    chapters: [
      { id: "avant-propos", title: "Pourquoi ce livre" },
    ],
  },
  {
    part: "INTRODUCTION",
    chapters: [
      { id: "introduction", title: "La Philosophie du Système" },
    ],
  },
  {
    part: "REVUE DE LA LITTÉRATURE",
    chapters: [
      { id: "lit1", title: "Finance comportementale et biais cognitifs" },
      { id: "lit2", title: "Théorie des marchés et efficience" },
      { id: "lit3", title: "Trading systématique et quantitatif" },
      { id: "lit4", title: "Gestion du risque et dimensionnement" },
      { id: "lit5", title: "Analyse technique et microstructure" },
      { id: "lit6", title: "Intelligence artificielle et NLP financier" },
    ],
  },
  {
    part: "PARTIE I — LA VISION",
    chapters: [
      { id: "ch1", title: "Chapitre 1 : Qu'est-ce qu'une thèse de trading" },
      { id: "ch2", title: "Chapitre 2 : Construire une thèse solide" },
      { id: "ch3", title: "Chapitre 3 : Intégrer les thèses dans le pipeline" },
    ],
  },
  {
    part: "PARTIE II — LE SCANNER",
    chapters: [
      { id: "ch4", title: "Chapitre 4 : Architecture du Scanner" },
      { id: "ch5", title: "Chapitre 5 : Analyse Technique" },
      { id: "ch6", title: "Chapitre 6 : Corrélation" },
      { id: "ch7", title: "Chapitre 7 : Sentiment" },
      { id: "ch8", title: "Chapitre 8 : Génome Explosif" },
      { id: "ch9", title: "Chapitre 9 : Capital Institutionnel (IPI)" },
      { id: "ch10", title: "Chapitre 10 : Vélocité Fondamentale (IVF)" },
      { id: "ch11", title: "Chapitre 11 : Macro Tailwind (MTS)" },
      { id: "ch12", title: "Chapitre 12 : Topologie Sociale (SGI)" },
      { id: "ch13", title: "Chapitre 13 : Unicité du Signal (SUS)" },
      { id: "ch14", title: "Chapitre 14 : Analyse Fondamentale V2" },
      { id: "ch15", title: "Chapitre 15 : Narrative Momentum" },
      { id: "ch16", title: "Chapitre 16 : Le Score Scanner Final" },
    ],
  },
  {
    part: "PARTIE III — L'ANALYSEUR",
    chapters: [
      { id: "ch17", title: "Chapitre 17 : Détection probabiliste du régime" },
      { id: "ch18", title: "Chapitre 18 : Les 12+ stratégies adaptatives" },
      { id: "ch19", title: "Chapitre 19 : Sélection et Strategy Decay" },
      { id: "ch20", title: "Chapitre 20 : Les catalyseurs" },
      { id: "ch21", title: "Chapitre 21 : Signaux inter-marchés" },
    ],
  },
  {
    part: "PARTIE IV — LE SCORING",
    chapters: [
      { id: "ch22", title: "Chapitre 22 : Le Score V2" },
      { id: "ch23", title: "Chapitre 23 : Score Bayésien Adaptatif" },
      { id: "ch24", title: "Chapitre 24 : Qualité du Contexte (SQC)" },
      { id: "ch25", title: "Chapitre 25 : La Thèse de Trade Complète" },
      { id: "ch26", title: "Chapitre 26 : Le Sizing Kelly" },
    ],
  },
  {
    part: "PARTIE V — L'EXÉCUTION",
    chapters: [
      { id: "ch27", title: "Chapitre 27 : Architecture d'exécution" },
      { id: "ch28", title: "Chapitre 28 : Le Scaling d'entrée" },
      { id: "ch29", title: "Chapitre 29 : Correction des biais" },
      { id: "ch30", title: "Chapitre 30 : Gestion post-entrée" },
      { id: "ch31", title: "Chapitre 31 : Arbitrage d'Opportunité" },
      { id: "ch32", title: "Chapitre 32 : File d'attente intelligente" },
    ],
  },
  {
    part: "PARTIE VI — LE PORTEFEUILLE",
    chapters: [
      { id: "ch33", title: "Chapitre 33 : Risk Parity Dynamique" },
      { id: "ch34", title: "Chapitre 34 : Stress Testing" },
      { id: "ch35", title: "Chapitre 35 : Régime portefeuille" },
      { id: "ch36", title: "Chapitre 36 : Contrôle du Drawdown" },
      { id: "ch37", title: "Chapitre 37 : Reversal Guard" },
    ],
  },
  {
    part: "PARTIE VII — LA PERFORMANCE",
    chapters: [
      { id: "ch38", title: "Chapitre 38 : Attribution causale du P&L" },
      { id: "ch39", title: "Chapitre 39 : Métriques professionnelles" },
      { id: "ch40", title: "Chapitre 40 : Le Meta-Score" },
      { id: "ch41", title: "Chapitre 41 : Early Warning System" },
      { id: "ch42", title: "Chapitre 42 : Taux de détection" },
      { id: "ch43", title: "Chapitre 43 : Benchmarking" },
    ],
  },
  {
    part: "PARTIE VIII — LA BOUCLE DE FEEDBACK",
    chapters: [
      { id: "ch44", title: "Chapitre 44 : La boucle Module 6 → Module 1" },
      { id: "ch45", title: "Chapitre 45 : Le Scoring Calibrator" },
      { id: "ch46", title: "Chapitre 46 : L'Entry Quality Tracker" },
      { id: "ch47", title: "Chapitre 47 : Le Strategy Decay" },
    ],
  },
  {
    part: "PARTIE IX — L'INFRASTRUCTURE",
    chapters: [
      { id: "ch48", title: "Chapitre 48 : Le Stack Technique" },
      { id: "ch49", title: "Chapitre 49 : Le Pipeline Celery" },
      { id: "ch50", title: "Chapitre 50 : Le Multi-Broker" },
      { id: "ch51", title: "Chapitre 51 : Le Déploiement" },
      { id: "ch52", title: "Chapitre 52 : La Robustesse" },
    ],
  },
  {
    part: "PARTIE X — LA PRATIQUE",
    chapters: [
      { id: "ch53", title: "Chapitre 53 : La journée type" },
      { id: "ch54", title: "Chapitre 54 : Lire le Dashboard" },
      { id: "ch55", title: "Chapitre 55 : Prendre une décision" },
      { id: "ch56", title: "Chapitre 56 : Gérer les pertes" },
      { id: "ch57", title: "Chapitre 57 : Les limites du modèle" },
      { id: "ch58", title: "Chapitre 58 : La roadmap" },
      { id: "ch59", title: "Chapitre 59 : La règle d'or" },
    ],
  },
];

export default function Livres() {
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeChapter, setActiveChapter] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/LIVRE_COMPLET.md")
      .then((res) => {
        if (!res.ok) throw new Error("Livre non trouvé");
        return res.text();
      })
      .then(setContent)
      .catch(() => setContent("# Livre en cours de rédaction\n\nLe contenu sera bientôt disponible."))
      .finally(() => setLoading(false));
  }, []);

  // Convertir le markdown en HTML basique
  const renderMarkdown = (md: string) => {
    return md
      .split("\n")
      .map((line, i) => {
        // Headers
        if (line.startsWith("# ") && !line.startsWith("## ") && line.includes("BILOK-TRADEPILOT"))
          return `<h1 class="text-4xl font-bold text-gold mt-16 mb-2 pb-4 border-b-2 border-gold/20 text-center" id="ch${i}">${line.slice(2)}</h1>
          <div class="my-8 flex justify-center">
            <svg viewBox="0 0 800 310" xmlns="http://www.w3.org/2000/svg" style="max-width:700px;width:100%">
              <!-- Background -->
              <rect width="800" height="310" rx="16" fill="#0a0a0a" stroke="#D4AF3740" stroke-width="1.5"/>

              <!-- Title -->
              <text x="400" y="38" text-anchor="middle" fill="#D4AF37" font-size="14" font-weight="bold" font-family="monospace" letter-spacing="3">PIPELINE ARCHITECTURE</text>
              <line x1="200" y1="50" x2="600" y2="50" stroke="#D4AF3730" stroke-width="1"/>

              <!-- Module boxes -->
              <!-- Scanner -->
              <rect x="30" y="80" width="110" height="65" rx="10" fill="#D4AF3715" stroke="#D4AF37" stroke-width="1.5"/>
              <text x="85" y="103" text-anchor="middle" fill="#D4AF37" font-size="10" font-weight="bold" font-family="sans-serif">MODULE 1</text>
              <text x="85" y="118" text-anchor="middle" fill="#e0e0e0" font-size="11" font-weight="bold" font-family="sans-serif">Scanner</text>
              <text x="85" y="134" text-anchor="middle" fill="#888" font-size="8" font-family="sans-serif">10 critères</text>

              <!-- Arrow 1 -->
              <line x1="140" y1="112" x2="165" y2="112" stroke="#D4AF37" stroke-width="1.5" marker-end="url(#arrowGold)"/>

              <!-- Analyseur -->
              <rect x="165" y="80" width="110" height="65" rx="10" fill="#60A5FA15" stroke="#60A5FA" stroke-width="1.5"/>
              <text x="220" y="103" text-anchor="middle" fill="#60A5FA" font-size="10" font-weight="bold" font-family="sans-serif">MODULE 2</text>
              <text x="220" y="118" text-anchor="middle" fill="#e0e0e0" font-size="11" font-weight="bold" font-family="sans-serif">Analyseur</text>
              <text x="220" y="134" text-anchor="middle" fill="#888" font-size="8" font-family="sans-serif">12+ stratégies</text>

              <!-- Arrow 2 -->
              <line x1="275" y1="112" x2="300" y2="112" stroke="#60A5FA" stroke-width="1.5" marker-end="url(#arrowBlue)"/>

              <!-- Scoring -->
              <rect x="300" y="80" width="110" height="65" rx="10" fill="#A78BFA15" stroke="#A78BFA" stroke-width="1.5"/>
              <text x="355" y="103" text-anchor="middle" fill="#A78BFA" font-size="10" font-weight="bold" font-family="sans-serif">MODULE 3</text>
              <text x="355" y="118" text-anchor="middle" fill="#e0e0e0" font-size="11" font-weight="bold" font-family="sans-serif">Scoring</text>
              <text x="355" y="134" text-anchor="middle" fill="#888" font-size="8" font-family="sans-serif">8 sources → GO</text>

              <!-- Arrow 3 -->
              <line x1="410" y1="112" x2="435" y2="112" stroke="#A78BFA" stroke-width="1.5" marker-end="url(#arrowPurple)"/>

              <!-- Exécution -->
              <rect x="435" y="80" width="110" height="65" rx="10" fill="#34D39915" stroke="#34D399" stroke-width="1.5"/>
              <text x="490" y="103" text-anchor="middle" fill="#34D399" font-size="10" font-weight="bold" font-family="sans-serif">MODULE 4</text>
              <text x="490" y="118" text-anchor="middle" fill="#e0e0e0" font-size="11" font-weight="bold" font-family="sans-serif">Exécution</text>
              <text x="490" y="134" text-anchor="middle" fill="#888" font-size="8" font-family="sans-serif">Brokers</text>

              <!-- Arrow 4 -->
              <line x1="545" y1="112" x2="570" y2="112" stroke="#34D399" stroke-width="1.5" marker-end="url(#arrowGreen)"/>

              <!-- Portfolio -->
              <rect x="570" y="80" width="110" height="65" rx="10" fill="#FBBF2415" stroke="#FBBF24" stroke-width="1.5"/>
              <text x="625" y="103" text-anchor="middle" fill="#FBBF24" font-size="10" font-weight="bold" font-family="sans-serif">MODULE 5</text>
              <text x="625" y="118" text-anchor="middle" fill="#e0e0e0" font-size="11" font-weight="bold" font-family="sans-serif">Portefeuille</text>
              <text x="625" y="134" text-anchor="middle" fill="#888" font-size="8" font-family="sans-serif">Risk Parity</text>

              <!-- Arrow down to Performance -->
              <line x1="625" y1="145" x2="625" y2="185" stroke="#FBBF24" stroke-width="1.5" marker-end="url(#arrowYellow)"/>

              <!-- Performance -->
              <rect x="570" y="185" width="110" height="65" rx="10" fill="#F4727215" stroke="#F47272" stroke-width="1.5"/>
              <text x="625" y="208" text-anchor="middle" fill="#F47272" font-size="10" font-weight="bold" font-family="sans-serif">MODULE 6</text>
              <text x="625" y="223" text-anchor="middle" fill="#e0e0e0" font-size="11" font-weight="bold" font-family="sans-serif">Performance</text>
              <text x="625" y="239" text-anchor="middle" fill="#888" font-size="8" font-family="sans-serif">P&amp;L Attribution</text>

              <!-- Feedback Loop Arrow (curved) -->
              <path d="M 570 217 L 300 217 C 150 217 100 217 85 185 L 85 145" stroke="#F47272" stroke-width="1.5" fill="none" stroke-dasharray="6 3" marker-end="url(#arrowRed)"/>
              <text x="320" y="210" text-anchor="middle" fill="#F47272" font-size="9" font-style="italic" font-family="sans-serif">feedback loop</text>

              <!-- Subtitle -->
              <text x="400" y="290" text-anchor="middle" fill="#888" font-size="11" font-family="Georgia, serif" font-style="italic">De la thèse au P&amp;L — un système qui apprend de ses propres décisions</text>

              <!-- Arrow markers -->
              <defs>
                <marker id="arrowGold" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#D4AF37"/></marker>
                <marker id="arrowBlue" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#60A5FA"/></marker>
                <marker id="arrowPurple" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#A78BFA"/></marker>
                <marker id="arrowGreen" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#34D399"/></marker>
                <marker id="arrowYellow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#FBBF24"/></marker>
                <marker id="arrowRed" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#F47272"/></marker>
              </defs>
            </svg>
          </div>`;
        if (line.startsWith("# ") && !line.startsWith("## "))
          return `<h1 class="text-4xl font-bold text-gold mt-16 mb-6 pb-4 border-b-2 border-gold/20" id="ch${i}">${line.slice(2)}</h1>`;
        if (line.startsWith("## ") && (line.includes("PROPOS DE L") || line.includes("À PROPOS")))
          return `<h2 class="text-2xl font-bold mt-12 mb-6 text-text-primary text-center" id="ch${i}">${line.slice(3)}</h2><div class="flex justify-center mb-6"><img src="/author.jpg" alt="Alain Bilok Evang" class="w-48 h-48 rounded-full object-cover border-4 border-gold/30 shadow-lg shadow-gold/10" /></div>`;
        if (line.startsWith("## "))
          return `<h2 class="text-2xl font-bold mt-12 mb-4 text-text-primary" id="ch${i}">${line.slice(3)}</h2>`;
        if (line.startsWith("### "))
          return `<h3 class="text-xl font-bold mt-10 mb-3 text-gold/90" id="ch${i}">${line.slice(4)}</h3>`;
        if (line.startsWith("#### "))
          return `<h4 class="text-lg font-semibold mt-8 mb-2 text-text-primary" id="ch${i}">${line.slice(5)}</h4>`;

        // Blockquote
        if (line.startsWith("> "))
          return `<blockquote class="border-l-4 border-gold/40 pl-4 py-2 my-4 italic text-text-secondary">${line.slice(2)}</blockquote>`;

        // Code block
        if (line.startsWith("```"))
          return line === "```" ? `</pre>` : `<pre class="bg-surface rounded-lg p-4 my-4 text-sm font-mono overflow-x-auto border border-border/50">`;

        // Table
        if (line.startsWith("|")) {
          const cells = line.split("|").filter(Boolean).map((c) => c.trim());
          if (line.includes("---"))
            return "";
          const tag = line.includes("**") || BOOK_STRUCTURE.some((p) => cells.some((c) => p.part.includes(c))) ? "th" : "td";
          const cellClass = tag === "th"
            ? "px-3 py-2 text-left text-xs font-semibold text-text-secondary bg-surface/50"
            : "px-3 py-2 text-sm border-t border-border/30";
          return `<tr>${cells.map((c) => `<${tag} class="${cellClass}">${formatInline(c)}</${tag}>`).join("")}</tr>`;
        }

        // Horizontal rule
        if (line === "---")
          return `<hr class="my-8 border-border/30" />`;

        // List
        if (line.match(/^- \*\*/))
          return `<li class="ml-4 mb-2 text-sm leading-relaxed list-disc">${formatInline(line.slice(2))}</li>`;
        if (line.startsWith("- "))
          return `<li class="ml-4 mb-1 text-sm leading-relaxed list-disc">${formatInline(line.slice(2))}</li>`;
        if (line.match(/^\d+\. /))
          return `<li class="ml-4 mb-2 text-sm leading-relaxed list-decimal">${formatInline(line.replace(/^\d+\. /, ""))}</li>`;

        // Empty line
        if (line.trim() === "") return `<div class="h-3"></div>`;

        // Regular paragraph
        return `<p class="text-sm leading-relaxed mb-2 text-text-primary/90">${formatInline(line)}</p>`;
      })
      .join("\n");
  };

  const formatInline = (text: string) => {
    return text
      .replace(/\*\*\*(.*?)\*\*\*/g, '<strong class="font-bold italic text-gold">$1</strong>')
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-text-primary">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic text-text-secondary">$1</em>')
      .replace(/`(.*?)`/g, '<code class="px-1.5 py-0.5 bg-surface rounded text-gold font-mono text-xs">$1</code>');
  };

  const handlePrint = () => {
    const printWindow = window.open("", "_blank");
    if (!printWindow) return;

    const lines = content.split("\n");
    let htmlBody = "";
    let isFirstH1 = true;
    let inCodeBlock = false;
    let inTable = false;
    let tableRows: string[][] = [];
    let tableHasHeader = false;
    let headerRowCount = 0;

    // Helper: inline formatting
    const fmt = (text: string): string => {
      return text
        .replace(/\*\*\*(.*?)\*\*\*/g, "<strong><em>$1</em></strong>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/`(.*?)`/g, "<code>$1</code>");
    };

    // Helper: flush accumulated table rows into a proper <table>
    const flushTable = () => {
      if (tableRows.length === 0) return;
      let t = '<table><thead>';
      if (tableHasHeader && headerRowCount > 0) {
        for (let r = 0; r < headerRowCount; r++) {
          t += "<tr>" + tableRows[r].map(c => `<th>${fmt(c)}</th>`).join("") + "</tr>";
        }
        t += "</thead><tbody>";
        for (let r = headerRowCount; r < tableRows.length; r++) {
          t += "<tr>" + tableRows[r].map(c => `<td>${fmt(c)}</td>`).join("") + "</tr>";
        }
      } else {
        t += "</thead><tbody>";
        for (const row of tableRows) {
          t += "<tr>" + row.map(c => `<td>${fmt(c)}</td>`).join("") + "</tr>";
        }
      }
      t += "</tbody></table>";
      htmlBody += t;
      tableRows = [];
      tableHasHeader = false;
      headerRowCount = 0;
      inTable = false;
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // If we were in a table and this line is not a table row, flush
      if (inTable && !line.startsWith("|")) {
        flushTable();
      }

      // Code blocks
      if (line.startsWith("```")) {
        if (inCodeBlock) {
          htmlBody += "</pre>";
          inCodeBlock = false;
        } else {
          htmlBody += '<pre class="code-block">';
          inCodeBlock = true;
        }
        continue;
      }
      if (inCodeBlock) {
        htmlBody += line + "\n";
        continue;
      }

      // ===== COVER PAGE =====
      if (line.startsWith("# ") && !line.startsWith("## ") && line.includes("BILOK-TRADEPILOT") && isFirstH1) {
        isFirstH1 = false;
        htmlBody += `
<div class="cover-page">
  <div class="cover-ornament">\u25C6 \u25C6 \u25C6</div>
  <h1 class="cover-title">BILOK-TRADEPILOT</h1>
  <div class="cover-line"></div>
  <p class="cover-subtitle">Le Syst\u00e8me</p>
  <p class="cover-desc">Architecture d\u2019un Pipeline de Trading Automatis\u00e9<br/>
  \u00e0 6 Modules avec Feedback Loop</p>
  <div class="pipeline-ascii">
\u250C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510   \u250C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510   \u250C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510   \u250C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510   \u250C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510   \u250C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
\u2502 SCANNER  \u2502\u2500\u25B6\u2502ANALYSEUR \u2502\u2500\u25B6\u2502 SCORING  \u2502\u2500\u25B6\u2502EXECUTION \u2502\u2500\u25B6\u2502PORTEFEUILLE\u2502\u2500\u25B6\u2502 PERFORMANCE \u2502
\u2502 10 crit. \u2502   \u2502 12+ strat\u2502   \u2502 Score V2 \u2502   \u2502 Brokers  \u2502   \u2502 Risk Parity\u2502   \u2502 P&amp;L Attrib.\u2502
\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u252C\u2500\u2500\u2500\u2500\u2500\u2500\u2518
  \u25B2                                                                              \u2502
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 feedback loop \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
  </div>
  <div class="cover-ornament" style="margin-top:40px">\u25C6</div>
  <p class="cover-author">Alain Bilok Evang</p>
  <p class="cover-year">Premi\u00e8re \u00e9dition \u2014 2026</p>
</div>`;
        continue;
      }

      // ===== PARTIE pages (major sections) =====
      if (line.startsWith("# PARTIE") || (line.startsWith("## ") && line.includes("PARTIE ")) || line === "# CONCLUSION" || line.startsWith("# ANNEXES") || line.startsWith("## ANNEXES")) {
        const title = line.replace(/^#+\s*/, "");
        htmlBody += `<div class="part-page"><div class="part-ornament">\u25C6</div><h1 class="part-title">${title}</h1><div class="part-line"></div></div>`;
        continue;
      }

      // ===== DEDICACES =====
      if (line.startsWith("## D\u00c9DICACES") || line.startsWith("## DÉDICACES")) {
        htmlBody += '<div class="dedication-page"><h2 class="dedication-title">D\u00e9dicaces</h2>';
        continue;
      }

      // ===== AUTHOR PAGE =====
      if (line.startsWith("## ") && (line.includes("PROPOS DE L") || line.includes("\u00c0 PROPOS"))) {
        htmlBody += `<div class="author-page"><h2 class="author-title">${line.slice(3)}</h2><img src="/author.jpg" class="author-photo" alt="Alain Bilok Evang" /></div>`;
        continue;
      }

      // ===== Section headers (## Section) =====
      if (line.startsWith("## Section") || line.startsWith("### Section")) {
        htmlBody += `<div class="section-header"><h3 class="section-title">${line.replace(/^#+\s*/, "")}</h3></div>`;
        continue;
      }

      // ===== HEADERS =====
      if (line.startsWith("# ") && !line.startsWith("## ")) {
        htmlBody += `<h1>${fmt(line.slice(2))}</h1>`;
        continue;
      }
      if (line.startsWith("## ")) {
        htmlBody += `<h2>${fmt(line.slice(3))}</h2>`;
        continue;
      }
      if (line.startsWith("### Chapitre")) {
        // Chapters flow continuously - no page break
        htmlBody += `<h3 class="chapter-title">${fmt(line.slice(4))}</h3>`;
        continue;
      }
      if (line.startsWith("### ")) {
        htmlBody += `<h3>${fmt(line.slice(4))}</h3>`;
        continue;
      }
      if (line.startsWith("#### ")) {
        htmlBody += `<h4>${fmt(line.slice(5))}</h4>`;
        continue;
      }

      // ===== BLOCKQUOTE =====
      if (line.startsWith("> ")) {
        htmlBody += `<blockquote>${fmt(line.slice(2))}</blockquote>`;
        continue;
      }

      // ===== HORIZONTAL RULE =====
      if (line.trim() === "---") {
        htmlBody += "<hr/>";
        continue;
      }

      // ===== TABLES =====
      if (line.startsWith("|")) {
        // Check if this is a separator row (|---|---|)
        if (/^\|[\s\-:|]+\|$/.test(line.trim()) || line.replace(/[|\s\-:]/g, "") === "") {
          // This is the header separator - mark that rows before this are headers
          tableHasHeader = true;
          headerRowCount = tableRows.length;
          inTable = true;
          continue;
        }
        // Parse cells
        const cells = line.split("|").slice(1); // skip first empty from leading |
        // Remove last if empty (trailing |)
        if (cells.length > 0 && cells[cells.length - 1].trim() === "") cells.pop();
        const trimmed = cells.map(c => c.trim());
        if (trimmed.length > 0) {
          tableRows.push(trimmed);
          inTable = true;
        }
        continue;
      }

      // ===== LISTS =====
      if (line.startsWith("- ")) {
        htmlBody += `<li class="ul-item">${fmt(line.slice(2))}</li>`;
        continue;
      }
      if (/^\d+\.\s/.test(line)) {
        htmlBody += `<li class="ol-item">${fmt(line.replace(/^\d+\.\s*/, ""))}</li>`;
        continue;
      }

      // ===== EMPTY LINE =====
      if (line.trim() === "") {
        continue; // No <br/> spam - paragraphs handle their own spacing
      }

      // ===== PARAGRAPH =====
      htmlBody += `<p>${fmt(line)}</p>`;
    }

    // Flush any remaining table
    if (inTable) flushTable();
    // Close any remaining code block
    if (inCodeBlock) htmlBody += "</pre>";

    const fullHtml = `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"/>
<title>Bilok-TradePilot \u2014 Le Syst\u00e8me</title>
<style>
/* Force background colors to print */
* {
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
  color-adjust: exact !important;
}

@page {
  size: A4;
  margin: 20mm 18mm 20mm 22mm;
}

body {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 11pt;
  line-height: 1.7;
  color: #1a1a1a;
  background: white;
  margin: 0;
  padding: 0;
}

/* ========== COVER PAGE ========== */
.cover-page {
  page-break-after: always;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #0c1a2e !important;
  color: white;
  margin: -20mm -18mm -20mm -22mm;
  padding: 40px 60px;
  box-sizing: border-box;
}
.cover-title {
  font-size: 36pt;
  font-weight: bold;
  color: #D4AF37;
  letter-spacing: 4px;
  margin: 15px 0 0 0;
  text-align: center;
  border: none;
  page-break-before: avoid;
}
.cover-subtitle {
  font-size: 20pt;
  color: #D4AF37;
  letter-spacing: 6px;
  font-weight: 300;
  margin: 5px 0 20px 0;
}
.cover-desc {
  font-size: 12pt;
  color: #a0b4c8;
  text-align: center;
  line-height: 1.5;
  font-style: italic;
  margin: 0;
}
.cover-line {
  width: 100px;
  height: 2px;
  background: #D4AF37 !important;
  margin: 12px auto;
}
.cover-ornament {
  color: #D4AF37;
  font-size: 12pt;
  letter-spacing: 12px;
  margin: 20px 0;
  opacity: 0.6;
}
.cover-author {
  font-size: 14pt;
  color: #e0d5c0;
  margin-top: 15px;
  letter-spacing: 2px;
}
.cover-year {
  font-size: 10pt;
  color: #8899aa;
  margin-top: 6px;
}
.pipeline-ascii {
  font-family: 'Courier New', monospace;
  font-size: 7pt;
  color: #D4AF37;
  white-space: pre;
  line-height: 1.3;
  margin: 20px 0 0 0;
  text-align: left;
  opacity: 0.85;
}

/* ========== PART PAGES ========== */
.part-page {
  page-break-before: always;
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 0;
}
.part-title {
  font-size: 20pt;
  color: #142d4c;
  letter-spacing: 2px;
  font-weight: bold;
  border: none;
  margin: 0;
  page-break-before: avoid;
  text-align: center;
}
.part-line {
  width: 60px;
  height: 2px;
  background: #D4AF37 !important;
  margin: 12px auto 0;
}
.part-ornament {
  color: #D4AF37;
  font-size: 14pt;
  margin-bottom: 15px;
  opacity: 0.5;
}

/* ========== AUTHOR PAGE ========== */
.author-page {
  page-break-before: always;
  page-break-after: always;
  text-align: center;
  padding-top: 60px;
}
.author-title {
  font-size: 16pt;
  color: #142d4c;
  margin-bottom: 20px;
  letter-spacing: 2px;
  border: none;
  page-break-before: avoid;
}
.author-photo {
  display: block;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  object-fit: cover;
  margin: 15px auto 25px;
  border: 3px solid #D4AF37;
}

/* ========== DEDICATION PAGE ========== */
.dedication-page {
  page-break-before: always;
  page-break-after: always;
  padding-top: 120px;
  text-align: center;
}
.dedication-title {
  font-size: 18pt;
  text-align: center;
  color: #142d4c;
  margin-bottom: 30px;
  letter-spacing: 3px;
  border: none;
  page-break-before: avoid;
}

/* ========== SECTIONS ========== */
.section-header {
  margin: 30px 0 15px 0;
  padding: 10px 0;
  border-top: 1px solid #D4AF37;
  border-bottom: 1px solid #D4AF37;
}
.section-title {
  font-size: 14pt;
  color: #142d4c;
  text-align: center;
  margin: 0;
  font-style: italic;
}

/* ========== HEADINGS ========== */
h1 {
  font-size: 20pt;
  color: #142d4c;
  text-align: center;
  margin: 30px 0 12px 0;
  padding-bottom: 6px;
  border-bottom: 2px solid #D4AF37;
  page-break-before: always;
}
h2 {
  font-size: 15pt;
  color: #142d4c;
  margin: 25px 0 8px 0;
  padding-bottom: 4px;
  border-bottom: 1px solid #D4AF37;
}
h3 {
  font-size: 13pt;
  color: #142d4c;
  margin: 20px 0 6px 0;
  font-style: italic;
  /* No page-break - chapters flow continuously */
}
h3.chapter-title {
  font-size: 13pt;
  color: #142d4c;
  margin: 25px 0 8px 0;
  padding-bottom: 5px;
  border-bottom: 1px solid #D4AF3750;
  font-style: italic;
  page-break-before: avoid;
}
h4 {
  font-size: 11pt;
  font-weight: bold;
  color: #1a3a5c;
  margin: 15px 0 5px 0;
}

/* ========== BODY TEXT ========== */
p {
  margin: 0 0 6px 0;
  text-align: justify;
  orphans: 3;
  widows: 3;
}
strong {
  color: #142d4c;
}

/* ========== BLOCKQUOTES ========== */
blockquote {
  border-left: 3px solid #D4AF37;
  padding: 8px 14px;
  margin: 12px 0;
  font-style: italic;
  color: #444;
  background: #f8f5ef !important;
}

/* ========== TABLES ========== */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 9pt;
  page-break-inside: avoid;
}
thead th {
  background: #f0ebe0 !important;
  padding: 6px 8px;
  text-align: left;
  border-bottom: 2px solid #D4AF37;
  font-size: 9pt;
  font-weight: bold;
  color: #333;
}
tbody td {
  padding: 5px 8px;
  border-bottom: 1px solid #e0dbd0;
  vertical-align: top;
}
tbody tr:nth-child(even) td {
  background: #faf8f3 !important;
}

/* ========== CODE ========== */
.code-block {
  background: #f5f2ec !important;
  padding: 10px 14px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 9pt;
  overflow-x: auto;
  border-left: 3px solid #D4AF37;
  margin: 10px 0;
  white-space: pre-wrap;
  page-break-inside: avoid;
}
code {
  background: #f0ebe0 !important;
  padding: 1px 3px;
  border-radius: 2px;
  font-family: 'Courier New', monospace;
  font-size: 9pt;
  color: #8B6914;
}

/* ========== LISTS ========== */
li {
  margin-bottom: 3px;
  margin-left: 18px;
  list-style-position: outside;
}
li.ul-item {
  list-style-type: disc;
}
li.ol-item {
  list-style-type: decimal;
}

/* ========== MISC ========== */
hr {
  border: none;
  border-top: 1px solid #D4AF37;
  margin: 20px 0;
  opacity: 0.4;
}

/* ========== PRINT OVERRIDES ========== */
@media print {
  body { background: white; }
  .cover-page {
    margin: -20mm -18mm -20mm -22mm;
    background: #0c1a2e !important;
  }
  /* Avoid blank pages */
  .part-page { height: auto; min-height: 50vh; }
  h1, h2, h3, h4 { page-break-after: avoid; }
  p, blockquote, li { page-break-inside: avoid; }
  table { page-break-inside: avoid; }
  .code-block { page-break-inside: avoid; }
}
</style>
</head>
<body>
${htmlBody}
</body>
</html>`;

    printWindow.document.write(fullHtml);
    printWindow.document.close();
    setTimeout(() => printWindow.print(), 800);
  };

  // Filtrer les chapitres par recherche
  const filteredStructure = searchQuery
    ? BOOK_STRUCTURE.map((section) => ({
        ...section,
        chapters: section.chapters.filter((ch) =>
          ch.title.toLowerCase().includes(searchQuery.toLowerCase())
        ),
      })).filter((s) => s.chapters.length > 0)
    : BOOK_STRUCTURE;

  // Scroller vers un chapitre
  const scrollToChapter = (title: string) => {
    setActiveChapter(title);
    if (!contentRef.current) return;
    // Chercher le titre dans le contenu rendu
    const headers = contentRef.current.querySelectorAll("h1, h2, h3, h4");
    for (const h of headers) {
      if (h.textContent?.includes(title.replace(/^Chapitre \d+ : /, ""))) {
        h.scrollIntoView({ behavior: "smooth", block: "start" });
        break;
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full border-2 border-transparent border-t-gold animate-spin mx-auto mb-4" />
          <p className="text-text-secondary text-sm">Chargement du livre...</p>
        </div>
      </div>
    );
  }

  const wordCount = content.split(/\s+/).length;
  const pageEstimate = Math.round(wordCount / 300);

  return (
    <div className="flex gap-0 -mx-6 -mt-6" style={{ height: "calc(100vh - 64px)" }}>
      {/* Sidebar — Sommaire */}
      {sidebarOpen && (
        <div className="w-72 min-w-[288px] bg-card border-r border-border overflow-y-auto p-4">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen size={18} className="text-gold" />
            <h3 className="text-sm font-bold">Sommaire</h3>
          </div>

          {/* Recherche dans le sommaire */}
          <div className="relative mb-4">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Rechercher..."
              className="w-full bg-surface border border-border rounded-lg pl-8 pr-3 py-1.5 text-xs focus:outline-none focus:border-gold/50"
            />
          </div>

          {/* Stats */}
          <div className="flex gap-3 mb-4 text-[10px] text-text-secondary">
            <span>{wordCount.toLocaleString()} mots</span>
            <span>~{pageEstimate} pages</span>
            <span>{BOOK_STRUCTURE.reduce((s, p) => s + p.chapters.length, 0)} chapitres</span>
          </div>

          {/* Arbre */}
          <div className="space-y-3">
            {filteredStructure.map((section) => (
              <div key={section.part}>
                <p className="text-[10px] font-bold text-gold uppercase tracking-wider mb-1">{section.part}</p>
                <div className="space-y-0.5">
                  {section.chapters.map((ch) => (
                    <button
                      key={ch.id}
                      onClick={() => scrollToChapter(ch.title)}
                      className={`w-full text-left flex items-center gap-1.5 px-2 py-1 rounded text-[11px] transition-colors ${
                        activeChapter === ch.title
                          ? "bg-gold/10 text-gold"
                          : "text-text-secondary hover:text-text-primary hover:bg-surface"
                      }`}
                    >
                      <ChevronRight size={10} className="flex-shrink-0 opacity-40" />
                      <span className="truncate">{ch.title.replace(/^Chapitre \d+ : /, "")}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contenu principal */}
      <div className="flex-1 overflow-y-auto" ref={contentRef}>
        {/* Header */}
        <div className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 text-text-secondary hover:text-text-primary bg-surface rounded-lg transition-colors"
              title={sidebarOpen ? "Masquer le sommaire" : "Afficher le sommaire"}
            >
              <BookOpen size={16} />
            </button>
            <div>
              <h2 className="text-lg font-bold">Bilok-TradePilot — Le Système</h2>
              <p className="text-[10px] text-text-secondary">Architecture d'un Pipeline de Trading Automatisé</p>
            </div>
          </div>
          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-3 py-1.5 bg-gold/10 text-gold border border-gold/20 rounded-lg text-xs font-semibold hover:bg-gold/20 transition-colors"
          >
            <Download size={14} />
            Exporter PDF
          </button>
        </div>

        {/* Contenu du livre */}
        <div
          className="max-w-3xl mx-auto px-8 py-8"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
        />
      </div>
    </div>
  );
}
