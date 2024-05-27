# FetchSpreadsheetData.

## Overview:
This module facilitates the automation of fetching transaction data from Google Spreadsheets that are populated by Tiller. Tiller is a tool that aggregates transactional data from various bank accounts into a single spreadsheet. The module provides a mechanism to programmatically retrieve this data, which can be crucial for applications involving financial analysis, budget tracking, or expense management.

## Functionality:
- Securely connects to Google Sheets to retrieve transaction data.
- Parses the spreadsheet data to convert it from raw format to structured JSON.
- Handles errors gracefully to manage cases where the spreadsheet might be empty or the API call fails.

## Usage:
The module defines a class `FetchSpreadsheetData` with a method `fetch_data` that fetches data from a specified Google Spreadsheet.

## Arguments:
- `apiKey (Secret)`: The API key required to authenticate requests to the Google Sheets API. It should have the necessary permissions to access the spreadsheet.
- `sheet (Secret)`: The ID of the Google Spreadsheet. This ID is typically found in the URL of the spreadsheet when opened in a web browser.
- `name (str)`: The name of the specific sheet within the Google Spreadsheet from which to fetch data.

## Return:
- The function returns a JSON formatted string. If transaction data is present, it returns a JSON string representing an array of transactions, where each transaction is a dictionary with column headers as keys. If no data is found, it returns an empty array '[]' in JSON format.

## Example Call:
`dagger call fetch-data --apiKey=env:[KEY] --sheet=env:[KEY] --name='Sheet1'`
