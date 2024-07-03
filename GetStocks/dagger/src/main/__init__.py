"""
Module Name: GetStocks 

Overview:
This module returns S&P 500 index stocks in sectors of your choosing grouped by sector (in terms of average_return)

Functionality:
- Scrapes the S&P 500 company symbols from Wikipedia.
- Fetches historical stock data for each symbol using `yfinance`.
- Calculates the average annual return for each stock based on monthly closing prices.
- Groups stocks by sector, ranks them by their average annual returns for each sector

Args:
- `sectors_of_interest (str)`: A string containing a list of all sectors you want to filter for.
- `period (int)`: The number of years of historical data to fetch.

Return:
- The `stocks` function returns a JSON containing all stocks grouped by sector and ranked by average return. Each stock is returned as a dictionary containing the stock symbol, average return, industry, stock prices and monthly return.

Example Call:
dagger call stocks --sectors_of_interest="Health Care,Information Technology,Financials,Energy" --period=5
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
    async def stocks(self, sectors_of_interest: str, period: int) -> str:
        investment_options = await self.get_investment_options(sectors_of_interest, period)
        investment_df = pd.DataFrame(investment_options)
        investment_df = investment_df.sort_values(by=['industry', 'average_return'], ascending=[True, False])
        investments_json = investment_df.to_dict(orient='records')
        for investment in investments_json:
            investment['average_return'] = str(investment['average_return'])
        return json.dumps({"investments": investments_json})
    
    def sp500(self, sectors_of_interest_list) -> str:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'id': 'constituents'})
            table_html = str(table)
            df = pd.read_html(StringIO(table_html))[0]
            df_filtered = df[df['GICS Sector'].isin(sectors_of_interest_list)]
            symbols = df_filtered['Symbol'].tolist()
            industries = df_filtered['GICS Sector'].tolist()
            symbols_and_industries = [{"symbol": symbol, "industry": industry} for symbol, industry in zip(symbols, industries)]
            return json.dumps({"symbols_and_industries": symbols_and_industries})

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
        except ValueError as e:
            print(f"Error parsing table: {e}")
        return json.dumps({"symbols": []})
    
    async def get_historical_data(self, symbol: str, period: int) -> pd.DataFrame:
        try:
            stock = yf.Ticker(symbol)
            period_str = f"{period}y"
            df = stock.history(period=period_str, interval="1mo")
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates the monthly return and adds it to the DataFrame."""
        try:
            df['monthly_return'] = df['Close'].pct_change()
            return df
        except Exception as e:
            print(f"Error calculating returns: {e}")
            return df
        
    def calculate_avg_return(self, df: pd.DataFrame) -> float:
        """Calculates the average annual return for a given DataFrame of historical data."""
        try:
            average_monthly_return = df['monthly_return'].mean()
            average_annual_return = (1 + average_monthly_return) ** 12 - 1 
            return average_annual_return
        except Exception as e:
            print(f"Error calculating average return: {e}")
            return float('nan')
                
    async def get_investment_options(self, sectors_of_interest: str, period: int) -> list:
        sectors_of_interest_list = sectors_of_interest.split(",")
        symbols_and_industries_json = self.sp500(sectors_of_interest_list)
        symbols_and_industries = json.loads(symbols_and_industries_json)["symbols_and_industries"]
        options = []
        for item in symbols_and_industries:
            symbol = item["symbol"]
            industry = item["industry"]
            try:
                df = await self.get_historical_data(symbol, period)
                if not df.empty:
                    df = self.calculate_returns(df)
                    average_return = self.calculate_avg_return(df)

                    df.reset_index(inplace=True) 
                    options.append({
                        "symbol": symbol,
                        "average_return": average_return,
                        "industry": industry,
                        "stock_prices": {row['Date'].strftime('%Y-%m-%d'): row['Close'] for index, row in df.iterrows()},
                        "monthly_return": {row['Date'].strftime('%Y-%m-%d'): row['monthly_return'] for index, row in df.iterrows()}
                    })
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        return options