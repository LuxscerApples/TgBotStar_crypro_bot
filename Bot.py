import os, asyncio, aiohttp, math, re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from bs4 import BeautifulSoup

BOT = os.getenv("BOT_TOKEN")
TON = os.getenv("TON_API_KEY")
OWN = int(os.getenv("OWNER_ID", "0"))

bot = Bot(token=BOT)
dp = Dispatcher()


@dp.message(Command("start"))
async def s(m: types.Message):
    await m.answer("Приветствую! Я бот для помощи по криптовалюте и НФТ. /help для полного доступа команд.")


@dp.message(Command("help"))
async def h(m: types.Message):
    await m.answer("Команды:\n/calculator пример — решает пример\n/Nftinfo имя или ссылка — инфо о NFT\n/course — курсы валют и крипты\n/about — о боте")


@dp.message(Command("about"))
async def about(m: types.Message):
    await m.answer("🤖 Бот-помощник по крипте и NFT\n📊 Курсы, калькулятор, инфо о NFT\n⚡ Создано на aiogram 3")


@dp.message(Command("calculator", "calc"))
async def calc(m: types.Message):
    a = m.text.split(maxsplit=1)
    if len(a) < 2:
        return await m.answer("/calculator 2+2*2")
    expr = a[1].replace(" ", "")
    expr = expr.replace("×", "*").replace("÷", "/").replace("−", "-").replace(",", ".")
    expr = expr.replace("√(", "math.sqrt(").replace("sqrt(", "math.sqrt(")
    expr = expr.replace("^", "**")
    expr = expr.replace("π", "math.pi")
    try:
        res = eval(expr, {"math": math, "__builtins__": {}})
        await m.answer(f"🧮 {a[1]} = {res}")
    except Exception as e:
        await m.answer(f"❌ Ошибка: {str(e)[:50]}")


@dp.message(Command("Nftinfo", "nftinfo"))
async def nft(m: types.Message):
    a = m.text.split(maxsplit=1)
    if len(a) < 2:
        return await m.answer("Примеры:\n/Nftinfo ChillFlame\n/Nftinfo http://t.me/nft/ChillFlame-11111")
    query = a[1].strip()

    if "t.me/nft/" in query or "t.me/" in query:
        name = query.split("/nft/")[-1] if "/nft/" in query else query
        name = re.sub(r"-\d+$", "", name)
        fragment_url = f"https://fragment.com/gift/{name}"
    else:
        name = query
        fragment_url = f"https://fragment.com/gift/{name}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with aiohttp.ClientSession() as s:
            async with s.get(fragment_url, headers=headers, timeout=15) as r:
                if r.status != 200:
                    return await m.answer(f"❌ Fragment: {r.status}")
                html = await r.text()

        soup = BeautifulSoup(html, "html.parser")

        title = soup.find("title").text if soup.find("title") else name

        price_txt = "—"
        floor_elem = soup.find(string=re.compile(r"TON", re.IGNORECASE))
        if floor_elem:
            parent = floor_elem.parent
            if parent:
                price_txt = parent.get_text(strip=True)[:30]

        info = soup.find("meta", {"name": "description"})
        desc = info["content"] if info else "—"

        issued = re.search(r"(\d[\d\s\xa0]*)\s*(?:issued|выпущено|minted)", html, re.IGNORECASE)
        issued_txt = issued.group(0)[:50] if issued else "—"

        t = f"🎁 NFT: {name}\n🌐 Fragment: {fragment_url}\n💰 Floor: ищем в TON API...\n📝 {desc[:100]}"

        try:
            api_url = f"https://tonapi.io/v2/nfts/searchItems?collection_name={name}&limit=1"
            api_headers = {"Authorization": f"Bearer {TON}"}
            async with aiohttp.ClientSession() as ss:
                async with ss.get(api_url, headers=api_headers, timeout=10) as rr:
                    if rr.status == 200:
                        data = await rr.json()
                        items = data.get("nft_items", [])
                        if items:
                            item = items[0]
                            addr = item.get("address", "—")
                            owner = item.get("owner", {}).get("address", "—")
                            if owner and len(owner) > 12:
                                owner = owner[:6] + "..." + owner[-4:]
                            if addr and len(addr) > 12:
                                addr = addr[:6] + "..." + addr[-4:]
                            t += f"\n👤 Владелец: {owner}\n🔗 {addr}\n🌐 https://tonviewer.com/{addr}"
        except:
            pass

        await m.answer(t)
    except Exception as e:
        await m.answer(f"❌ Ошибка: {str(e)[:100]}")


@dp.message(Command("course", "price"))
async def course(m: types.Message):
    t = "💹 КУРСЫ В ДОЛЛАРАХ (USD):\n\n📊 Крипта:\n"
    try:
        async with aiohttp.ClientSession() as s:
            url = "https://api.coinpaprika.com/v1/tickers"
            async with s.get(url, timeout=10) as r:
                d = await r.json()
                ids = {
                    "btc-bitcoin": "BTC", "eth-ethereum": "ETH", "sol-solana": "SOL",
                    "toncoin-ton": "TON", "doge-dogecoin": "DOGE", "xrp-xrp": "XRP",
                    "bnb-binance-coin": "BNB", "ada-cardano": "ADA", "trx-tron": "TRX",
                    "matic-polygon": "MATIC", "ltc-litecoin": "LTC", "avax-avalanche": "AVAX",
                    "dot-polkadot": "DOT", "link-chainlink": "LINK", "near-near-protocol": "NEAR",
                    "atom-cosmos": "ATOM"
                }
                for x in d:
                    if x["id"] in ids:
                        p = x["quotes"]["USD"]["price"]
                        t += f"{ids[x['id']]}: ${p:,.4f}\n"
    except:
        t += "⚠️ крипта недоступна\n"

    t += "\n💵 Фиат (1 единица = $):\n"
    try:
        async with aiohttp.ClientSession() as s:
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            async with s.get(url, timeout=10) as r:
                d = await r.json()
                rates = d.get("rates", {})
                for code, name in [("RUB", "₽ Рубль"), ("EUR", "€ Евро"), ("CNY", "¥ Юань"), ("GBP", "£ Фунт"), ("JPY", "¥ Йена"), ("KZT", "₸ Тенге"), ("UAH", "₴ Гривна"), ("TRY", "₺ Лира")]:
                    if code in rates:
                        t += f"1 {code} = ${rates[code]:.4f}\n"
    except:
        t += "⚠️ фиат недоступен"

    await m.answer(t)


async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
