"""
Module Name: GetStocks 

Overview:
This module facilitates the retrieval and analysis of stock data from the S&P 500 index. It uses web scraping to obtain the list of S&P 500 companies and `yfinance` to fetch historical stock data. The module calculates the average annual return for each stock and identifies the top investment options based on these returns.

Functionality:
- Scrapes the S&P 500 company symbols from Wikipedia.
- Fetches historical stock data for each symbol using `yfinance`.
- Calculates the average annual return for each stock based on monthly closing prices.
- Ranks the stocks by their average annual returns and returns the top investment options.

Args:
- `alpha (Secret)`: This argument was initially required for Alpha Vantage API keys but is now redundant since `yfinance` is used. It can be ignored or removed.

Return:
- The `stocks` function returns a JSON formatted string representing the top investment options. Each investment option is a dictionary containing the stock symbol and its average annual return.
- The `sp500` function returns a JSON string containing the list of S&P 500 company symbols.
- The `get_historical_data` function fetches and returns historical stock data as a pandas DataFrame.
- The `calculate_avg_return` function computes the average annual return for the given historical data.

Example Call:
dagger call stocks
"""
from dagger import function, object_type
from bs4 import BeautifulSoup
import requests
import pandas as pd
from io import StringIO
import json
import yfinance as yf

@object_type
class GetStocks:
    @function
    async def stocks(self ) -> str:
        investment_options = await self.get_investment_options()
        investment_df = pd.DataFrame(investment_options)
        top_investments = investment_df.sort_values(by=['average_return'], ascending=False)
        top_investments_json = top_investments.head(20).to_dict(orient='records')
        return json.dumps({"top_investments": top_investments_json})
    def sp500(self) -> str:
        """Returns a container that echoes whatever string argument is provided"""
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'id': 'constituents'})
            table_html = str(table)
            df = pd.read_html(StringIO(table_html))[0]
            symbols = df['Symbol'].tolist()
            symbols_json = json.dumps({"symbols": symbols})
            return symbols_json
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
        except ValueError as e:
            print(f"Error parsing table: {e}")
        return json.dumps({"symbols": []})
    async def get_historical_data(self, symbol: str) -> pd.DataFrame:
            try:
                stock = yf.Ticker(symbol)
                df = stock.history(period="5y", interval="1mo")
                df['current_price'] = stock.info['currentPrice'] if 'currentPrice' in stock.info else None
                return df
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                return pd.DataFrame()
    def calculate_avg_return(self, df: pd.DataFrame) -> float:
        """Calculates the average annual return for a given DataFrame of historical data."""
        try:
            df['monthly_return'] = df['Close'].pct_change()
            average_monthly_return = df['monthly_return'].mean()
            average_annual_return = (1 + average_monthly_return) ** 12 - 1 
            return average_annual_return
        except Exception as e:
            print(f"Error calculating average return: {e}")
            return float('nan')
    async def get_investment_options(self) -> str:
        symbols_json = self.sp500()
        symbols = json.loads(symbols_json)["symbols"]
        options = []
        for symbol in symbols:
            try:
                df = await self.get_historical_data(symbol)
                print('df', df)
                if df is not None:
                    average_return = self.calculate_avg_return(df)
                    current_price = df['current_price'].iloc[-1] if 'current_price' in df.columns else None
                    print('avg', average_return)
                    options.append({
                        "symbol": symbol,
                        "average_return": average_return,
                        "current_price": current_price
                    })
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        return options