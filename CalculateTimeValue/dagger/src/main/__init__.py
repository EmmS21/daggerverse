"""
Module Name: CalculateTimeValue

Overview:
This module provides functionality to calculate the time value of money for either debt or stock investments over a specified period, factoring in inflation. It uses data from the Federal Reserve Economic Data (FRED) API to obtain the current inflation rate and incorporates this information into the calculations.
This module is used to help an autonomous agent decide how to more efficiently prioritize paying back a debt

Functionality:
- Fetches the annual inflation rate from the FRED API based on the Consumer Price Index (CPI).
- Calculates the future value of a given amount of money, either as debt or as a stock investment, over a specified period with monthly compounding.
- Adjusts the calculation for inflation to provide a more accurate representation of the time value of money.

Args:
- `period (int)`: The total number of months over which the time value calculation will be performed.
- `amount (str)`: The initial amount of money to be evaluated.
- `rate (str)`: The annual interest rate for debt or the annual return rate for stocks, provided as a decimal.
- `fred_str (Secret)`: The API key required to authenticate requests to the FRED API. This key should have the necessary permissions to access the required data.

Return:
- The function returns a JSON formatted string. For each month in the specified period, it provides the future value of the amount as either debt or stock, adjusted for inflation. The JSON string represents an array of monthly future values, where each entry is a dictionary with the month and the calculated future value.

Example Call:
 dagger call calculate --period=12 --amount=10000 --rate=0.04 --fred_str=env:FRED
 """

from dagger import function, object_type, Secret
import requests
import json

@object_type
class CalculateTimeValue:
    @function
    async def calculate(self, period: int, amount: str, rate: str, fred_str: Secret) -> str:
        """Returns a container that echoes whatever string argument is provided"""
        inflation_rate_str =  await self.get_inflation('CPIAUCSL', fred_str)
        inflation_rate = float(inflation_rate_str.strip('%'))/100
        return self.calculate_time_value(period, inflation_rate, float(amount), 'debt', float(rate))
    
    async def get_inflation(self, series_id: str, fred_str: Secret) -> float:
        api_key =  await fred_str.plaintext()
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json"
        response = requests.get(url)
        data = response.json()
        latest_observation = data['observations'][-1]
        previous_year_observation = data['observations'][-13] if len(data['observations']) > 12 else None
        if previous_year_observation:
            latest_cpi = float(latest_observation['value'])
            previous_cpi = float(previous_year_observation['value'])
            annual_inflation_rate = (latest_cpi - previous_cpi) / previous_cpi
            inflation_rate_str = f"{annual_inflation_rate * 100:.2f}%"
        else:
            inflation_rate_str = "Insufficient data to calculate annual inflation rate"

        return inflation_rate_str
    def calculate_time_value(self, max_period, inflation, amount, calculation_type, interest_rate_or_return) -> str:
        monthly_inflation_rate = (1 + inflation) ** (1 / 12) - 1
        monthly_rate = (1 + interest_rate_or_return) ** (1 / 12) - 1

        results = []

        for month in range(1, max_period + 1):
            if calculation_type == 'debt':
                adjusted_rate = (1 + monthly_rate) / (1 + monthly_inflation_rate) - 1
                future_value = amount * (1 + adjusted_rate) ** month
                results.append({
                    "month": month,
                    "future_value_debt": round(future_value, 2)
                })
            elif calculation_type == 'stock':
                adjusted_rate = (1 + monthly_rate) / (1 + monthly_inflation_rate) - 1
                future_value = amount * (1 + adjusted_rate) ** month
                results.append({
                    "month": month,
                    "future_value_stock": round(future_value, 2)
                })
            else:
                raise ValueError("Invalid calculation type. Must be 'debt' or 'stock'.")

        result_json = json.dumps(results)
        return result_json