import os
import httpx

DUNE_API_KEY = os.getenv("DUNE_API_KEY")
DUNE_QUERY_ID = "4632804"

headers = {
    "Content-Type": "application/json",
    "x-dune-api-key": DUNE_API_KEY
}

async def fetch_smart_wallets(mode: str) -> list:
    """
    Holt Smart Wallets von Dune, gefiltert nach Modus ('moonbags' oder 'scalpbags').

    Rückgabeformat:
    [
        {
            "address": str,
            "winrate": float,
            "roi": float,
            "pnl": float,
            "age": int,
            "balance": float
        },
        ...
    ]
    """
    url = f"https://api.dune.com/api/v1/query/{DUNE_QUERY_ID}/results"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)

        data = response.json()
        rows = data.get("result", {}).get("rows", [])

        filtered_wallets = []

        for row in rows:
            winrate = row.get("winrate", 0)
            roi = row.get("roi", 0)

            if winrate >= 70 and roi >= 5:
                if mode == "scalpbags" and roi <= 30:
                    pass
                elif mode == "moonbags" and roi > 30:
                    pass
                else:
                    continue

                filtered_wallets.append({
                    "address": row.get("wallet"),
                    "winrate": winrate,
                    "roi": roi,
                    "pnl": row.get("realized_pnl", 0),
                    "age": row.get("wallet_age_days", "?"),
                    "balance": row.get("sol_balance", 0),
                })

        return filtered_wallets

    except Exception as e:
        print(f"❌ Fehler beim Abrufen von Smart Wallets: {e}")
        return []
