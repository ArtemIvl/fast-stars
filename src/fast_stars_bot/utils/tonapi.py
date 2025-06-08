import httpx
from typing import Optional
from config.settings import settings
from decimal import Decimal

API_KEY=settings.API_KEY
TON_API_URL="https://tonapi.io/v2"
TON_WALLET_ADDRESS=settings.TON_WALLET_ADDRESS

async def check_deposit_received(expected_amount: Decimal, expected_comment: str) -> Optional[Decimal]:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{TON_API_URL}/blockchain/accounts/{TON_WALLET_ADDRESS}/transactions",
                headers=headers,
                params={"limit": 20}
            )
        response.raise_for_status()
    except httpx.RequestError as e:
        print(f"Ошибка при обращении к TonAPI: {e}")
        return None
    
    data = response.json()
    txs = data.get("transactions", [])
    for tx in txs:
        in_msg = tx.get("in_msg")
        if not in_msg:
            continue

        decoded_body = in_msg.get("decoded_body", {})
        comment = decoded_body.get("text")
        value = in_msg.get("value")

        print(f"Ожидаем comment={expected_comment}, amount={expected_amount}")
        print(f"Транзакция: comment={comment}, amount={value}")

        if comment == expected_comment and value:
            amount = Decimal(value) / Decimal("1e9")
            rounded_expected = expected_amount.quantize(Decimal("0.000001"))
            rounded_actual = amount.quantize(Decimal("0.000001"))

            if rounded_actual >= rounded_expected:
                return amount
            
    return None