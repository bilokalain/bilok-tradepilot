"""
Construit la matrice combinée V2/V3/V4/V5
Pondération : 40% V2 (5 ans) + 30% V3 (10 ans) + 20% V4 (15 ans) + 10% V5 (20 ans)

Usage: python scripts/build_combined_matrix.py
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, ".")

FILES = {
    "v2": ("data/backtest_v2_5ans.json", 0.60),
    "v3": ("data/backtest_v3_10ans.json", 0.40),
}

OUTPUT = Path("data/backtest_full_500.json")


def main():
    versions = {}
    total_weight = 0

    for key, (path, weight) in FILES.items():
        p = Path(path)
        if p.exists():
            data = json.loads(p.read_text())
            versions[key] = {"data": data, "weight": weight}
            total_weight += weight
            print(f"  ✅ {key}: {len(data['results'])} actifs (poids {weight*100:.0f}%)")
        else:
            print(f"  ❌ {key}: fichier manquant ({path})")

    if not versions:
        print("Aucun fichier de backtest trouvé.")
        return

    # Renormaliser les poids si des versions manquent
    if total_weight < 1.0:
        for v in versions.values():
            v["weight"] /= total_weight
        print(f"\n  Poids renormalisés (total était {total_weight:.0f}%)")

    # Collecter tous les symboles
    all_symbols = set()
    for v in versions.values():
        all_symbols.update(v["data"]["results"].keys())

    print(f"\n  Symboles uniques: {len(all_symbols)}")

    # Construire la matrice combinée
    combined_results = {}
    for symbol in sorted(all_symbols):
        all_strategies_sharpes: dict[str, list[tuple[float, float]]] = {}  # strat → [(sharpe, weight)]

        for key, v in versions.items():
            r = v["data"]["results"].get(symbol)
            if not r:
                continue
            for s in r.get("strategies", []):
                strat = s["strategy"]
                sharpe = s.get("sharpe_ratio", 0)
                if strat not in all_strategies_sharpes:
                    all_strategies_sharpes[strat] = []
                all_strategies_sharpes[strat].append((sharpe, v["weight"]))

        if not all_strategies_sharpes:
            continue

        # Sharpe pondéré pour chaque stratégie
        weighted_sharpes = {}
        for strat, values in all_strategies_sharpes.items():
            total_w = sum(w for _, w in values)
            if total_w > 0:
                weighted_sharpes[strat] = sum(s * w for s, w in values) / total_w
            else:
                weighted_sharpes[strat] = 0

        best_strat = max(weighted_sharpes, key=weighted_sharpes.get)
        best_sharpe = weighted_sharpes[best_strat]

        # Récupérer les infos du premier fichier qui a cet actif
        first_data = None
        for v in versions.values():
            if symbol in v["data"]["results"]:
                first_data = v["data"]["results"][symbol]
                break

        combined_results[symbol] = {
            "name": first_data.get("name", symbol) if first_data else symbol,
            "asset_class": first_data.get("asset_class", "ACTION_US") if first_data else "ACTION_US",
            "data_points": first_data.get("data_points", 0) if first_data else 0,
            "best_strategy": best_strat,
            "best_sharpe": round(best_sharpe, 3),
            "versions_available": list(k for k, v in versions.items() if symbol in v["data"]["results"]),
            "strategies": [
                {"strategy": s, "sharpe_ratio": round(sh, 3)}
                for s, sh in sorted(weighted_sharpes.items(), key=lambda x: x[1], reverse=True)
            ],
        }

    # Stats globales
    stats = {
        "type": "combined_matrix",
        "versions": {k: {"weight": v["weight"], "assets": len(v["data"]["results"])} for k, v in versions.items()},
        "total_assets": len(combined_results),
        "by_strategy": {},
    }

    for sym, r in combined_results.items():
        strat = r["best_strategy"]
        if strat not in stats["by_strategy"]:
            stats["by_strategy"][strat] = {"count": 0, "avg_sharpe": 0}
        ss = stats["by_strategy"][strat]
        ss["count"] += 1
        ss["avg_sharpe"] = (ss["avg_sharpe"] * (ss["count"] - 1) + r["best_sharpe"]) / ss["count"]

    # Sauvegarder
    OUTPUT.write_text(json.dumps({"stats": stats, "results": combined_results}, default=str, indent=1))
    print(f"\n  💾 Matrice combinée sauvegardée: {OUTPUT}")
    print(f"     {len(combined_results)} actifs")

    # Classement
    print(f"\n  CLASSEMENT DES STRATÉGIES (Sharpe pondéré) :")
    for strat, ss in sorted(stats["by_strategy"].items(), key=lambda x: x[1]["avg_sharpe"], reverse=True):
        print(f"    {strat:22s}  {ss['count']:3d} actifs  Sharpe={ss['avg_sharpe']:.3f}")


if __name__ == "__main__":
    main()
