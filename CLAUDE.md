# Projet Trading — Outil d'aide à la décision financière

Plateforme d'analyse de marchés financiers avec scan de données, indicateurs techniques, stratégies personnalisées et signaux d'achat/vente.

## Stack

- **Next.js 15** (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **Prisma ORM** + PostgreSQL (Supabase)
- **NextAuth.js** (authentification)
- **APIs Marché** : Yahoo Finance, Alpha Vantage, Binance (crypto)
- **OpenAI** : analyse de sentiment (news, réseaux sociaux)
- **Lightweight Charts** (TradingView) : graphiques interactifs
- Hébergement : Vercel

## Architecture

### Modules principaux

1. **Scanner de marché** — Scan automatique d'actifs selon des critères
2. **Indicateurs techniques** — RSI, MACD, Bollinger, EMA, SMA, Volume, ATR, Stochastique, Fibonacci
3. **Stratégies** — Moteur de règles personnalisables (IF conditions THEN signal)
4. **Signaux** — Tableau de bord des signaux achat/vente avec scoring
5. **Backtesting** — Tester une stratégie sur des données historiques
6. **Watchlist** — Liste d'actifs surveillés avec alertes
7. **Journal de trading** — Historiser les décisions prises et les résultats
8. **Sentiment** — Analyse IA des news pour chaque actif

### Marchés cibles

- Actions (US, EU)
- ETF
- Crypto (via Binance/CoinGecko)
- Forex
- Matières premières

## Charte Graphique

| Couleur | Valeur | Usage |
|---------|--------|-------|
| Fond principal | `#0A0F1C` | Dashboard sombre |
| Fond cartes | `#111827` | Cards |
| Primaire | `#3B82F6` | Bleu — actions, liens |
| Achat (haussier) | `#10B981` | Vert — signaux achat |
| Vente (baissier) | `#EF4444` | Rouge — signaux vente |
| Neutre | `#F59E0B` | Orange — attente |
| Texte principal | `#F9FAFB` | Blanc |
| Texte secondaire | `#9CA3AF` | Gris clair |
| Accent | `#8B5CF6` | Violet — IA/sentiment |

Thème sombre uniquement. Police : Inter (texte), JetBrains Mono (données financières).

## Sécurité

- Authentification NextAuth (email/password)
- Données financières en lecture seule (pas de trading automatique)
- Clés API stockées côté serveur uniquement
- Outil d'aide à la décision, pas de conseil financier

## URLs prévues

- `/` — Dashboard principal (résumé marchés, signaux du jour)
- `/scanner` — Scanner de marché avec filtres
- `/actif/[symbol]` — Détail d'un actif (graphique, indicateurs, signaux)
- `/strategies` — Gestion des stratégies
- `/backtesting` — Backtesting de stratégies
- `/watchlist` — Ma watchlist
- `/journal` — Journal de trading
- `/sentiment` — Analyse de sentiment IA
- `/parametres` — Configuration (API keys, préférences)
