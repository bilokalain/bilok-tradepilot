"""Setup Alpaca Paper Trading

Guide interactif pour configurer Alpaca et vérifier la connexion.
Compte gratuit : https://app.alpaca.markets/signup

1. Créer un compte sur alpaca.markets
2. Aller dans Paper Trading → API Keys
3. Générer une clé API + Secret
4. Lancer ce script pour vérifier
"""

import sys
import os
sys.path.insert(0, ".")


def main():
    print("\n" + "=" * 60)
    print("  Bilok-TradePilot — Configuration Alpaca Paper Trading")
    print("=" * 60)

    # Vérifier si déjà configuré
    from backend.config.settings import settings

    if settings.ALPACA_API_KEY and settings.ALPACA_SECRET_KEY:
        print(f"\n  Clés trouvées dans .env")
        print(f"  API Key : {settings.ALPACA_API_KEY[:8]}...")
        print(f"  Base URL: {settings.ALPACA_BASE_URL}")
        print(f"\n  Test de connexion...")

        try:
            from backend.modules.execution.broker_alpaca import AlpacaBroker
            broker = AlpacaBroker()
            account = broker.get_account()
            print(f"\n  Connexion réussie !")
            print(f"  Compte : {account['id'][:12]}...")
            print(f"  Equity : ${account['equity']:,.2f}")
            print(f"  Cash   : ${account['cash']:,.2f}")
            print(f"  Mode   : {'PAPER' if account['paper'] else 'LIVE'}")
            print(f"\n  Alpaca est prêt.")
        except Exception as e:
            print(f"\n  Erreur de connexion : {e}")
            print(f"  Vérifiez vos clés API dans .env")
    else:
        print(f"""
  Alpaca n'est pas encore configuré.

  Étapes :
  1. Créez un compte gratuit sur https://app.alpaca.markets/signup
  2. Allez dans Paper Trading → API Keys
  3. Générez une API Key et un Secret Key
  4. Ajoutez-les dans votre fichier .env :

     ALPACA_API_KEY=votre_api_key
     ALPACA_SECRET_KEY=votre_secret_key
     ALPACA_BASE_URL=https://paper-api.alpaca.markets

  5. Relancez ce script : python scripts/setup_alpaca.py
""")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
