import platform
import aiohttp
import asyncio
from datetime import datetime, timedelta
from icecream import ic


class ExchangeRateProvider:
    async def get_exchange_rates(self, session, date):
        raise NotImplementedError("Subclasses must implement this method")


class PrivatBankApi(ExchangeRateProvider):
    async def get_exchange_rates(self, session, date):
        url = f'https://api.privatbank.ua/p24api/exchange_rates?date={date}'
        async with session.get(url) as response:
            if response.ok:
                return date, await response.json()
            else:
                raise Exception(
                    f"Error fetching data for {date}. "
                    f"Status code: {response.status}"
                )


class DataExtractor:

    @staticmethod
    def extract_values(data):
        extracted_values = []

        for date, result in data:
            exchange_rate = result.get('exchangeRate', [])
            rates = {'date': date, 'values': []}

            for currency in exchange_rate:
                if currency['currency'] in ['EUR', 'USD']:
                    rates['values'].append({
                        'currency': currency['currency'],
                        'sale': currency['saleRate'],
                        'purchase': currency['purchaseRate']
                    })

            extracted_values.append(rates)

        return extracted_values


async def main():
    days = 0
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        try:
            days = int(input(
                f"Enter the number of days (1-10) "
                f"[Attempt {attempt}/{max_attempts}]: "
            ))
            if 1 <= days <= 10:
                break
            else:
                print("Number of days must be between 1 and 10.")
        except ValueError as e:
            print(f"Error: {e}")

        if attempt == max_attempts:
            print("Exceeded maximum number of attempts. Exiting.")
            return

    api_provider = PrivatBankApi()
    data_extractor = DataExtractor()

    async with aiohttp.ClientSession() as session:
        today = datetime.today()
        dates = [today - timedelta(days=i) for i in range(days)]

        tasks = [api_provider.get_exchange_rates(
            session, date.strftime("%d.%m.%Y")) for date in dates]
        exchange_rates = await asyncio.gather(*tasks)

    extracted_values = data_extractor.extract_values(exchange_rates)
    ic(extracted_values)


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
