import requests
import json

def main():
    api_key = 'AIzaSyDtVsXDLIortszwfVJQiljyEM64LUMSsG0'
    spreadsheet_id = '1pckPDFx47IpuE-xI3hVRaD_03HKFHwcqVngq_dcVlBg'
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/Transactions?key={api_key}'
    response = requests.get(url)
    data = response.json()
    if 'values' in data:
        headers = data['values'][0]  # First row as headers
        rows = data['values'][1:]    # Remaining data as rows

        transactions = []
        for row in rows:
            transaction = {headers[i]: row[i] for i in range(len(headers))}
            transactions.append(transaction)

        # Convert the list of dictionaries into a JSON formatted string
        json_output = json.dumps(transactions, indent=4)
        print(json_output)
    else:
        print('No data found.')

if __name__ == "__main__":
    main()