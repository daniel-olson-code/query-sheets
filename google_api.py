"""
Google Sheets API interaction module.

This module provides functions for interacting with Google Sheets API,
including authentication, data manipulation, and sheet management.
"""

from __future__ import print_function, annotations
import time
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import List, Any
from googleapiclient.errors import HttpError
import socket
import os.path
import string

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_API_CREDENTIALS_PATH = 'google_credentials.json'
TOKENS_PATH = 'token.json'

# Uncomment to extend the API's timeout limit
socket.setdefaulttimeout(60 * 60)


def has_credentials() -> bool:
    """
    Check if Google API credentials file exists.

    Returns:
        bool: True if the credentials file exists, False otherwise.
    """
    global GOOGLE_API_CREDENTIALS_PATH
    return os.path.exists(GOOGLE_API_CREDENTIALS_PATH)


def has_tokens() -> bool:
    """
    Check if Google API tokens file exists.

    Returns:
        bool: True if the tokens file exists, False otherwise.
    """
    global TOKENS_PATH
    return os.path.exists(TOKENS_PATH)


def chunks(lst: List, n: int) -> List:
    """
    Yield successive n-sized chunks from lst.

    Args:
        lst: The list to be chunked.
        n: The size of each chunk.

    Yields:
        List: A chunk of the original list.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_column_letter(col_idx: int) -> str:
    """
    Convert a column number into a column letter (e.g., 3 -> 'C').

    Args:
        col_idx: The column index (1-based).

    Returns:
        str: The corresponding column letter(s).
    """
    letters = []
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx, 26)
        if remainder == 0:
            remainder = 26
            col_idx -= 1
        letters.append(chr(remainder + 64))
    return ''.join(reversed(letters))


def coordinate_from_string(cell: str) -> tuple[str, int]:
    """
    Split a cell reference into column and row.

    Args:
        cell: Cell reference (e.g., 'A1').

    Returns:
        tuple: Column letters and row number.
    """
    i = 0
    while cell[i] in string.ascii_letters:
        i += 1
    return cell[:i], int(cell[i:])


def column_index_from_string(column: str) -> int:
    """
    Convert a column letter into its corresponding index.

    Args:
        column: Column letter(s) (e.g., 'A', 'AA').

    Returns:
        int: The corresponding column index (1-based).
    """
    result = 0
    for i, c in enumerate(column.upper()[::-1]):
        result += (string.ascii_uppercase.index(c) + 1) * 26 ** i
    return result


def translate_range(_range: str, row: int = 0, col: int = 0, func=None) -> str:
    """
    Translate a range by given row and column offsets.

    Args:
        _range: The original range.
        row: Row offset.
        col: Column offset.
        func: Optional function to apply to row and column.

    Returns:
        str: The translated range.
    """
    cell_range = _range if '!' not in _range else _range.split('!')[1]
    cells = [cell_range] if ':' not in cell_range else cell_range.split(':')
    custom_sheet = '!' in _range
    _sheet = _range.split('!')[0]

    # column_index_from_string, coordinate_from_string, get_column_letter
    for i in range(len(cells)):
        cell = cells[i]
        try:
            _cell = coordinate_from_string(cell)
            _r, _c = _cell[1], column_index_from_string(_cell[0])
            _r, _c = (_r + row, _c + col) if not callable(func) else func(_r, _c)
            _cell = cell.replace(_cell[0], get_column_letter(_c)) \
                .replace(f'{_cell[1]}', f'{_r}')
        except IndexError:  # CellCoordinatesException as e:  # error thrown for ranges like A:B instead of A1:B4

            _r, _c = 1, column_index_from_string(cell)
            _r, _c = (_r + row, _c + col) if not callable(func) else func(_r, _c)
            _cell = cell.replace(cell, get_column_letter(_c))
        cells[i] = _cell
    cell_range = ':'.join(cells)
    return cell_range if not custom_sheet else f'{_sheet}!{cell_range}'

def fix_spreadsheet_id_if_link(spreadsheet_id: str) -> str:
    """
    Extract the spreadsheet ID from a Google Sheets URL if provided.

    Args:
        spreadsheet_id: The spreadsheet ID or URL.

    Returns:
        str: The extracted spreadsheet ID.
    """
    return spreadsheet_id.split('/d/')[-1].split('/')[0]


def revoke_token() -> requests.Response:
    """
    Revoke the current Google API token.

    Returns:
        requests.Response: The response from the revocation request.
    """
    creds = get_creds()
    return requests.post('https://oauth2.googleapis.com/revoke',
                         params={'token': creds.token},
                         headers={'content-type': 'application/x-www-form-urlencoded'})


def valid_credentials() -> bool:
    """
    Check if the current credentials are valid.

    Returns:
        bool: True if credentials are valid, False otherwise.
    """
    creds = get_creds()

    if creds is None:
        return False

    return creds.valid


def get_creds() -> Credentials:
    """
    Get or refresh Google API credentials.

    Returns:
        Credentials: The Google API credentials.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKENS_PATH):
        # v = (s3.load_s3_json(token_path))
        # if isinstance(v, str):
        #     v = json.loads(v)
        # print(type(v))
        # args = [
        #     v,
        #     [creds['scopes']]
        #     if not isinstance(creds['scopes'], list)
        #     else creds['scopes']
        # ]
        # print(args)
        creds = Credentials.from_authorized_user_file(TOKENS_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        # else:
        #     flow = InstalledAppFlow.from_client_secrets_file(
        #         google_credentials_path, SCOPES)
        #     creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKENS_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def get_sheets(spreadsheet_id: str, names: bool = False, creds=None, service=None) -> List[dict]:
    """
    Get information about sheets in a spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        names: If True, return only sheet names.
        creds: Optional credentials.
        service: Optional Google Sheets API service.

    Returns:
        List[dict]: Information about sheets or sheet names.
    """
    creds = get_creds() if creds is None else creds
    service = build('sheets', 'v4', credentials=creds) if service is None else service
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    # print('sheet_metadata', sheet_metadata)
    sheets = sheet_metadata.get('sheets', '')
    # print('sheets,', sheets)
    title = sheets[0].get("properties", {}).get("title", "Sheet1")
    # print('title', title)
    sheet_id = sheets[0].get("properties", {}).get("sheetId", 0)
    # print('sheet_id')
    if names:
        return [v.get("properties", {}).get('title') for v in sheets]
    return [v.get("properties", {}) for v in sheets]

def get_sheet_width_then_height(spreadsheet_id: str, sheet_name: str, creds=None, service=None) -> tuple[int, int]:
    """
    Get the width and height of a specific sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        sheet_name: The name of the sheet.
        creds: Optional credentials.
        service: Optional Google Sheets API service.

    Returns:
        tuple[int, int]: The width and height of the sheet.
    """
    sheets = get_sheets(spreadsheet_id)
    for sheet in sheets:
        if sheet.get('title', 'Sheet1') == sheet_name:
            # return sheet
            return sheet.get('gridProperties', {}).get('columnCount', 0), sheet.get('gridProperties', {}).get('rowCount', 0)

def get_big_sheet_data(spreadsheet_id: str, sheet_name: str, chunk_size: int = 1000, creds=None, service=None, include_formulas: bool = True, unformat_value: bool = False) -> List[List[Any]]:
    """
    Retrieve data from a large sheet in chunks.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        sheet_name: The name of the sheet.
        chunk_size: The size of each chunk to retrieve.
        creds: Optional credentials.
        service: Optional Google Sheets API service.
        include_formulas: If True, include formulas in the retrieved data.
        unformat_value: If True, retrieve unformatted values.

    Returns:
        List[List[Any]]: The retrieved sheet data.
    """
    creds = get_creds() if creds is None else creds  # get_creds() if creds is None else creds
    service = build('sheets', 'v4', credentials=creds) if service is None else service
    size = get_sheet_width_then_height(spreadsheet_id, sheet_name, creds, service)
    i, j = 0, 0
    table = []

    def fix(rows):
        largest = max([len(row) for row in rows])
        for i in range(len(rows)):
            missing_rows = [''] * (largest - len(rows[i]))
            rows[i] = rows[i] + missing_rows
        return rows

    for y in range(0, size[1], 1000):
        rows = []
        for x in range(0, size[0], 1000):
            a1 = f'{sheet_name}!{get_column_letter(min(size[0], x + 1))}{min(size[1], y + 1)}:{get_column_letter(min(size[0], x + 1000))}{min(size[1], y + 1000)}'
            sheet = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=a1,  # f'{sheet_name}!{x}:{y}',
                majorDimension='ROWS',
                valueRenderOption=('UNFORMATTED_VALUE' if unformat_value else ('FORMULA' if include_formulas else 'FORMATTED_VALUE'))
            ).execute()
            time.sleep(1.)
            if 'values' not in sheet:
                continue

            rows.append(fix(sheet['values']))

        table.extend(rows[0] if rows else [])
        # rows = list(chain.from_iterable(rows))

    return fix(table)

def sheet_id_from_name(name: str, spreadsheet_id: str, creds=None, service=None) -> int:
    """
    Get the sheet ID from its name.

    Args:
        name: The name of the sheet.
        spreadsheet_id: The ID of the spreadsheet.
        creds: Optional credentials.
        service: Optional Google Sheets API service.

    Returns:
        int: The sheet ID.
    """
    creds = get_creds() if creds is None else creds
    service = build('sheets', 'v4', credentials=creds) if service is None else service
    return [sheet['sheetId'] for sheet in get_sheets(spreadsheet_id, creds=creds, service=service) if sheet['title'] == name][0]


def rename_spreadsheet_sheet(spreadsheet_id: str, old_sheet_name: str, new_name: str, creds=None, service=None) -> dict:
    """
    Rename a sheet in a spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        old_sheet_name: The current name of the sheet.
        new_name: The new name for the sheet.
        creds: Optional credentials.
        service: Optional Google Sheets API service.

    Returns:
        dict: The response from the rename operation.
    """
    creds = get_creds() if creds is None else creds
    service = build('sheets', 'v4', credentials=creds) if service is None else service
    return service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id_from_name(old_sheet_name, spreadsheet_id, creds, service),
                            "title": new_name
                        },
                        "fields": "title"
                    }
                }
            ]
        }
    ).execute()

def resize_sheet(spreadsheet_id: str, sheet_name: str, appended_columns: int = 0, appended_row: int = 0, creds=None, service=None) -> tuple[dict, dict]:
    """
    Resize a sheet by adding columns and/or rows.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        sheet_name: The name of the sheet.
        appended_columns: Number of columns to append.
        appended_row: Number of rows to append.
        creds: Optional credentials.
        service: Optional Google Sheets API service.

    Returns:
        tuple[dict, dict]: Responses from column and row append operations.
    """
    creds = get_creds() if creds is None else creds
    service = build('sheets', 'v4', credentials=creds) if service is None else service
    sheet_id = sheet_id_from_name(sheet_name, spreadsheet_id)
    r1 = r2 = None
    if appended_columns > 0:
        resource = {
            "requests": [
                {
                    "appendDimension": {
                        "length": appended_columns,
                        "dimension": "COLUMNS",
                        "sheetId": sheet_id
                    }
                }
            ]
        }
        # response = JSON.parse(UrlFetchApp.fetch(ssBatchUpdateUrl, options));
        r1 = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=resource
        ).execute()
    if appended_row > 0:
        resource = {
            "requests": [
                {
                    "appendDimension": {
                        "length": appended_row,
                        "dimension": "ROWS",
                        "sheetId": sheet_id
                    }
                }
            ]
        }
        # response = JSON.parse(UrlFetchApp.fetch(ssBatchUpdateUrl, options));
        r2 = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=resource
        ).execute()
    return r1, r2

def add_table_to_sheet(spreadsheet_id: str, table: list[list] | list[dict] | Any, sheet: str = 'Sheet1', cell: str = 'A1') -> dict:
    """
    Add a table to a sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        table: The table data to add.
        sheet: The name of the sheet.
        cell: The starting cell for the table.

    Returns:
        dict: The response from the update operation.
    """
    dbl = sheet.startswith('"') and sheet.endswith('"')
    sgl = sheet.startswith("'") and sheet.endswith("'")
    if ' ' in sheet and (not dbl or not sgl):
        sheet = f"'{sheet}'"
    creds = get_creds()  # get_creds()
    service = build('sheets', 'v4', credentials=creds)

    # "pip install pandas" is not required for this python script, but is supported
    is_pandas_dataframe = not isinstance(table, list)

    if is_pandas_dataframe:
        end_cell = translate_range(cell, len(table), len(table.columns))
    else:
        if not len(table):
            return
        end_cell = translate_range(cell, len(table), len(table[0]))
    if is_pandas_dataframe:
        try:
            table = table.fillna('').T.reset_index().T.values.tolist()
        except Exception as e:
            print('The below error may be due that a panda dataframe was expected')
            raise
    else:
        if isinstance(table[0], dict):
            headers = list(table[0].keys())
            new_table = [headers]
            for row in table:
                new_table.append(list(row.values()))
            table = new_table
        elif isinstance(table[0], list):
            pass
        else:
            raise ValueError('table must be pandas.Dataframe, list[list] or list[dict].')

    response_date = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        valueInputOption='USER_ENTERED',  # 'RAW',
        range=f'{sheet}!{cell}:{end_cell}',
        body={
            'majorDimension': 'ROWS',
            'values': table
        }
    ).execute()
    return response_date

def add_table_and_clear_sheet(spreadsheet_id: str, table: list[list] | list[dict] | Any, sheet_name: str = 'Sheet1', cell: str = 'A1') -> None:
    """
    Clear a sheet and add a new table to it.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        table: The table data to add.
        sheet_name: The name of the sheet.
        cell: The starting cell for the table.
    """
    sheets = get_sheets(spreadsheet_id, names=True)
    time.sleep(.5)  # wait to prevent rate limiting

    only_one_sheet = len(sheets) == 1
    sheet_already_exists = sheet_name in sheets

    # delete sheet to not have any "extra" unwanted data or formating
    if sheet_already_exists:
        # create sheet if there's only on to prevent errors
        if only_one_sheet:
            create_sheet(spreadsheet_id, '__temp__')
            time.sleep(.5)  # wait to prevent rate limiting
        delete_sheet(spreadsheet_id, sheet_name)
        time.sleep(.5)  # wait to prevent rate limiting
        if only_one_sheet:
            delete_sheet(spreadsheet_id, '__temp__')
            time.sleep(.5)  # wait to prevent rate limiting

    create_sheet(spreadsheet_id, sheet_name)
    time.sleep(.5)  # wait to prevent rate limiting

    add_table_to_sheet(
        spreadsheet_id,
        table,
        sheet_name,
        cell=cell
    )

def place_chunks(spreadsheet_id: str, sheet_name: str, table: list[list] | list[dict], chunk_size: int = 1000) -> None:
    """
    Place a large table into a sheet in chunks.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        sheet_name: The name of the sheet.
        table: The table data to add.
        chunk_size: The size of each chunk.
    """
    size = get_sheet_width_then_height(spreadsheet_id, sheet_name)
    # stop if table is empty
    if not table:
        return

    # stop if no headers
    if not table[0]:
        return

    more_rows_in_table_than_sheet = (len(table) + 1) - size[1] > 0
    table_wider_than_sheet = (len(table[0]) + 1) - size[0] > 0
    if more_rows_in_table_than_sheet or table_wider_than_sheet:
        resize_sheet(
            spreadsheet_id,
            sheet_name,
            appended_columns=max(0, (len(table[0]) + 1) - size[0]),  # columns to add
            appended_row=max(0, (len(table) + 1) - size[1])  # rows to add
        )
        time.sleep(1.)

    row_index = 1
    if isinstance(table[0], dict):
        headers = list(table[0].keys())
        table = [headers] + [list(row.values()) for row in table]
    if not isinstance(table[0], list):
        raise ValueError('table must be list[list] or list[dict].')

    for sub_table in chunks(table, chunk_size):
        add_table_to_sheet(spreadsheet_id, sub_table, f'A{row_index}', sheet_name)
        time.sleep(1.)
        row_index += chunk_size

def delete_sheet(spreadsheet_id: str, sheet_name: str, creds=None, service=None) -> dict:
    """
    Delete a sheet from a spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        sheet_name: The name of the sheet to delete.
        creds: Optional credentials.
        service: Optional Google Sheets API service.

    Returns:
        dict: The response from the delete operation.
    """
    creds = get_creds() if creds is None else creds  # get_creds() if creds is None else creds
    service = build('sheets', 'v4', credentials=creds) if service is None else service
    return service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': [{"deleteSheet": {"sheetId": sheet_id_from_name(sheet_name, spreadsheet_id)}}]}
    ).execute()

def create_sheet(spreadsheet_id: str, sheet: str, creds=None) -> None:
    """
    Create a new sheet in a spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        sheet: The name of the new sheet.
        creds: Optional credentials.
    """
    creds = get_creds() if creds is None else creds
    sheetservice = build('sheets', 'v4', credentials=creds)

    body = {
        "requests": {
            "addSheet": {
                "properties": {
                    "title": sheet
                }
            }
        }
    }

    sheetservice.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()


# from __future__ import print_function, annotations
# import time
# import requests
# from google.auth.transport.requests import Request  # pip install google-api-python-client
# from google.oauth2.credentials import Credentials  # pip install google-api-python-client
# from googleapiclient.discovery import build  # pip install google-api-python-client
# from typing import List, Any
# from googleapiclient.errors import HttpError
# import socket
# import os.path
# import string
#
# # If modifying these scopes, delete the file token.json.
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets']  # .readonly']
# GOOGLE_API_CREDENTIALS_PATH = 'google_credentials.json'
# TOKENS_PATH = 'token.json'
#
# # uncomment to extend the API's timeout limit
# socket.setdefaulttimeout(60 * 60)
#
#
# def chunks(lst, n):
#     """
#     Yield successive n-sized chunks from lst.
#     src: https://stackoverflow.com/questions/312443/how-do-i-split-a-list-into-equally-sized-chunks
#     """
#     for i in range(0, len(lst), n):
#         yield lst[i:i + n]
#
#
# def get_column_letter(col_idx):
#     """Convert a column number into a column letter (3 -> 'C')
#     Right shift the column col_idx by 26 to find column letters in reverse
#     order.  These numbers are 1-based, and can be converted to ASCII
#     ordinals by adding 64.
#     """
#     letters = []
#     while col_idx > 0:
#         col_idx, remainder = divmod(col_idx, 26)
#         # check for exact division and borrow if needed
#         if remainder == 0:
#             remainder = 26
#             col_idx -= 1
#         letters.append(chr(remainder + 64))
#     column = ''.join(reversed(letters))
#     return column
#
#
# def coordinate_from_string(cell: str):
#     i = 0
#     while cell[i] in string.ascii_letters:
#         i += 1
#     return cell[:i], int(cell[i:])
#
#
# def column_index_from_string(column: str):
#     result = 0
#     for i, c in enumerate(column.upper()[::-1]):
#         result += (string.ascii_uppercase.index(c) + 1) * 26 ** i
#     return result
# # # 10's -> A's
# # get_column_letter(
# #     sum(map(lambda a: 26**a, range(5))))  # 5th A's place
#
#
# def translate_range(_range: str, row: int=0, col: int=0, func=None):  # func = lambda col, row: (col+1, row+1)
#     cell_range = _range if '!' not in _range else _range.split('!')[1]
#     cells = [cell_range] if ':' not in cell_range else cell_range.split(':')
#     custom_sheet = '!' in _range
#     _sheet = _range.split('!')[0]
#
#     # column_index_from_string, coordinate_from_string, get_column_letter
#     for i in range(len(cells)):
#         cell = cells[i]
#         try:
#             _cell = coordinate_from_string(cell)
#             _r, _c = _cell[1], column_index_from_string(_cell[0])
#             _r, _c = (_r + row, _c + col) if not callable(func) else func(_r, _c)
#             _cell = cell.replace(_cell[0], get_column_letter(_c)) \
#                 .replace(f'{_cell[1]}', f'{_r}')
#         except IndexError:  # CellCoordinatesException as e:  # error thrown for ranges like A:B instead of A1:B4
#
#             _r, _c = 1, column_index_from_string(cell)
#             _r, _c = (_r + row, _c + col) if not callable(func) else func(_r, _c)
#             _cell = cell.replace(cell, get_column_letter(_c))
#         cells[i] = _cell
#     cell_range = ':'.join(cells)
#     return cell_range if not custom_sheet else f'{_sheet}!{cell_range}'
#
#
# def fix_spreadsheet_id_if_link(spreadsheet_id: str):
#     """
#     If the spreadsheet_id is a link, extract the spreadsheet_id from the link.
#     Otherwise, return the spreadsheet_id as is.
#
#     Args:
#         spreadsheet_id (str): The spreadsheet_id, which could be a link.
#     Returns:
#         str: The spreadsheet_id.
#     """
#     return spreadsheet_id.split('/d/')[-1].split('/')[0]
#
#
# def revoke_token():
#     creds = get_creds()
#     r = requests.post('https://oauth2.googleapis.com/revoke',
#                       params={'token': creds.token},
#                       headers={'content-type': 'application/x-www-form-urlencoded'})
#     return r
#
#
# def valid_credentials():
#     """
#     Checks if the credentials are valid.
#
#     Args:
#         None
#     Returns:
#         bool: True if valid, False otherwise.
#     """
#     creds = get_creds()
#
#     if creds is None:
#         return False
#
#     return creds.valid
#
# def get_creds():
#     """Shows basic usage of the Sheets API.
#     Prints values from a sample spreadsheet.
#     """
#     creds = None
#     # The file token.json stores the user's access and refresh tokens, and is
#     # created automatically when the authorization flow completes for the first
#     # time.
#     if os.path.exists(TOKENS_PATH):
#         # v = (s3.load_s3_json(token_path))
#         # if isinstance(v, str):
#         #     v = json.loads(v)
#         # print(type(v))
#         # args = [
#         #     v,
#         #     [creds['scopes']]
#         #     if not isinstance(creds['scopes'], list)
#         #     else creds['scopes']
#         # ]
#         # print(args)
#         creds = Credentials.from_authorized_user_file(TOKENS_PATH, SCOPES)
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         # else:
#         #     flow = InstalledAppFlow.from_client_secrets_file(
#         #         google_credentials_path, SCOPES)
#         #     creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open(TOKENS_PATH, 'w') as token:
#             token.write(creds.to_json())
#     return creds
#
#
# def get_sheets(spreadsheet_id, names=False, creds=None, service=None):
#     creds = get_creds() if creds is None else creds
#     service = build('sheets', 'v4', credentials=creds) if service is None else service
#     sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
#     # print('sheet_metadata', sheet_metadata)
#     sheets = sheet_metadata.get('sheets', '')
#     # print('sheets,', sheets)
#     title = sheets[0].get("properties", {}).get("title", "Sheet1")
#     # print('title', title)
#     sheet_id = sheets[0].get("properties", {}).get("sheetId", 0)
#     # print('sheet_id')
#     if names:
#         return [v.get("properties", {}).get('title') for v in sheets]
#     return [v.get("properties", {}) for v in sheets]
#
#
# def get_sheet_width_then_height(spreadsheet_id: str, sheet_name: List[str], creds=None, service=None):
#     sheets = get_sheets(spreadsheet_id)
#     for sheet in sheets:
#         if sheet.get('title', 'Sheet1') == sheet_name:
#             # return sheet
#             return sheet.get('gridProperties', {}).get('columnCount', 0), sheet.get('gridProperties', {}).get('rowCount', 0)
#
#
# def get_big_sheet_data(spreadsheet_id, sheet_name, chunk_size=1000, creds=None, service=None, include_formulas=True, unformat_value=False):
#     creds = get_creds() if creds is None else creds  # get_creds() if creds is None else creds
#     service = build('sheets', 'v4', credentials=creds) if service is None else service
#     size = get_sheet_width_then_height(spreadsheet_id, sheet_name, creds, service)
#     i, j = 0, 0
#     table = []
#
#     def fix(rows):
#         largest = max([len(row) for row in rows])
#         for i in range(len(rows)):
#             missing_rows = [''] * (largest - len(rows[i]))
#             rows[i] = rows[i] + missing_rows
#         return rows
#
#     for y in range(0, size[1], 1000):
#         rows = []
#         for x in range(0, size[0], 1000):
#             a1 = f'{sheet_name}!{get_column_letter(min(size[0], x + 1))}{min(size[1], y + 1)}:{get_column_letter(min(size[0], x + 1000))}{min(size[1], y + 1000)}'
#             sheet = service.spreadsheets().values().get(
#                 spreadsheetId=spreadsheet_id,
#                 range=a1,  # f'{sheet_name}!{x}:{y}',
#                 majorDimension='ROWS',
#                 valueRenderOption=('UNFORMATTED_VALUE' if unformat_value else ('FORMULA' if include_formulas else 'FORMATTED_VALUE'))
#             ).execute()
#             time.sleep(1.)
#             if 'values' not in sheet:
#                 continue
#
#             rows.append(fix(sheet['values']))
#
#         table.extend(rows[0] if rows else [])
#         # rows = list(chain.from_iterable(rows))
#
#     return fix(table)
#
#
# def sheet_id_from_name(name: str, spreadsheet_id: str, creds=None, service=None):
#     creds = get_creds() if creds is None else creds
#     service = build('sheets', 'v4', credentials=creds) if service is None else service
#     return [sheet['sheetId'] for sheet in get_sheets(spreadsheet_id, creds=creds, service=service) if sheet['title'] == name][0]
#
#
# def rename_spreadsheet_sheet(spreadsheet_id: str, old_sheet_name: str, new_name: str, creds=None, service=None):
#     creds = get_creds() if creds is None else creds
#     service = build('sheets', 'v4', credentials=creds) if service is None else service
#     return service.spreadsheets().batchUpdate(
#         spreadsheetId=spreadsheet_id,
#         body={
#             "requests": [
#                 {
#                     "updateSheetProperties": {
#                         "properties": {
#                             "sheetId": sheet_id_from_name(old_sheet_name, spreadsheet_id, creds, service),
#                             "title": new_name
#                         },
#                         "fields": "title"
#                     }
#                 }
#             ]
#         }
#     ).execute()
#
#
# def resize_sheet(spreadsheet_id: str, sheet_name: List[str], appended_columns: int = 0, appended_row: int = 0, creds=None, service=None):
#     creds = get_creds() if creds is None else creds
#     service = build('sheets', 'v4', credentials=creds) if service is None else service
#     sheet_id = sheet_id_from_name(sheet_name, spreadsheet_id)
#     r1 = r2 = None
#     if appended_columns > 0:
#         resource = {
#             "requests": [
#                 {
#                     "appendDimension": {
#                         "length": appended_columns,
#                         "dimension": "COLUMNS",
#                         "sheetId": sheet_id
#                     }
#                 }
#             ]
#         }
#         # response = JSON.parse(UrlFetchApp.fetch(ssBatchUpdateUrl, options));
#         r1 = service.spreadsheets().batchUpdate(
#             spreadsheetId=spreadsheet_id,
#             body=resource
#         ).execute()
#     if appended_row > 0:
#         resource = {
#             "requests": [
#                 {
#                     "appendDimension": {
#                         "length": appended_row,
#                         "dimension": "ROWS",
#                         "sheetId": sheet_id
#                     }
#                 }
#             ]
#         }
#         # response = JSON.parse(UrlFetchApp.fetch(ssBatchUpdateUrl, options));
#         r2 = service.spreadsheets().batchUpdate(
#             spreadsheetId=spreadsheet_id,
#             body=resource
#         ).execute()
#     return r1, r2
#
#
# def add_table_to_sheet(spreadsheet_id: str, table: list[list] | list[dict] | Any, sheet='Sheet1', cell='A1'):
#     dbl = sheet.startswith('"') and sheet.endswith('"')
#     sgl = sheet.startswith("'") and sheet.endswith("'")
#     if ' ' in sheet and (not dbl or not sgl):
#         sheet = f"'{sheet}'"
#     creds = get_creds()  # get_creds()
#     service = build('sheets', 'v4', credentials=creds)
#
#     # "pip install pandas" is not required for this python script, but is supported
#     is_pandas_dataframe = not isinstance(table, list)
#
#     if is_pandas_dataframe:
#         end_cell = translate_range(cell, len(table), len(table.columns))
#     else:
#         if not len(table):
#             return
#         end_cell = translate_range(cell, len(table), len(table[0]))
#     if is_pandas_dataframe:
#         try:
#             table = table.fillna('').T.reset_index().T.values.tolist()
#         except Exception as e:
#             print('The below error may be due that a panda dataframe was expected')
#             raise
#     else:
#         if isinstance(table[0], dict):
#             headers = list(table[0].keys())
#             new_table = [headers]
#             for row in table:
#                 new_table.append(list(row.values()))
#             table = new_table
#         elif isinstance(table[0], list):
#             pass
#         else:
#             raise ValueError('table must be pandas.Dataframe, list[list] or list[dict].')
#
#     response_date = service.spreadsheets().values().update(
#         spreadsheetId=spreadsheet_id,
#         valueInputOption='USER_ENTERED',  # 'RAW',
#         range=f'{sheet}!{cell}:{end_cell}',
#         body={
#             'majorDimension': 'ROWS',
#             'values': table
#         }
#     ).execute()
#     return response_date
#
#
# def add_table_and_clear_sheet(spreadsheet_id: str, table: list[list] | list[dict] | Any, sheet_name='Sheet1', cell='A1'):
#     sheets = get_sheets(spreadsheet_id, names=True)
#     time.sleep(.5)  # wait to prevent rate limiting
#
#     only_one_sheet = len(sheets) == 1
#     sheet_already_exists = sheet_name in sheets
#
#     # delete sheet to not have any "extra" unwanted data or formating
#     if sheet_already_exists:
#         # create sheet if there's only on to prevent errors
#         if only_one_sheet:
#             create_sheet(spreadsheet_id, '__temp__')
#             time.sleep(.5)  # wait to prevent rate limiting
#         delete_sheet(spreadsheet_id, sheet_name)
#         time.sleep(.5)  # wait to prevent rate limiting
#         if only_one_sheet:
#             delete_sheet(spreadsheet_id, '__temp__')
#             time.sleep(.5)  # wait to prevent rate limiting
#
#     create_sheet(spreadsheet_id, sheet_name)
#     time.sleep(.5)  # wait to prevent rate limiting
#
#     add_table_to_sheet(
#         spreadsheet_id,
#         table,
#         sheet_name,
#         cell=cell
#     )
#
# def place_chunks(
#         spreadsheet_id: str,
#         sheet_name: str,
#         table: list[list] | list[dict],
#         chunk_size=1000
# ) -> None:
#     """
#     Places table into a sheet placing it in chunks.
#
#     Args:
#         spreadsheet_id (str): The spreadsheet id.
#         sheet_name (str): The name of the sheet.
#         table (list[list] | list[dict]): The table to place.
#         chunk_size (int, optional): The chunk size. Defaults to 1000.
#
#     Returns:
#         None
#     """
#     size = get_sheet_width_then_height(spreadsheet_id, sheet_name)
#     # stop if table is empty
#     if not table:
#         return
#
#     # stop if no headers
#     if not table[0]:
#         return
#
#     more_rows_in_table_than_sheet = (len(table) + 1) - size[1] > 0
#     table_wider_than_sheet = (len(table[0]) + 1) - size[0] > 0
#     if more_rows_in_table_than_sheet or table_wider_than_sheet:
#         resize_sheet(
#             spreadsheet_id,
#             sheet_name,
#             appended_columns=max(0, (len(table[0]) + 1) - size[0]),  # columns to add
#             appended_row=max(0, (len(table) + 1) - size[1])  # rows to add
#         )
#         time.sleep(1.)
#
#     row_index = 1
#     if isinstance(table[0], dict):
#         headers = list(table[0].keys())
#         table = [headers] + [list(row.values()) for row in table]
#     if not isinstance(table[0], list):
#         raise ValueError('table must be list[list] or list[dict].')
#
#     for sub_table in chunks(table, chunk_size):
#         add_table_to_sheet(spreadsheet_id, sub_table, f'A{row_index}', sheet_name)
#         time.sleep(1.)
#         row_index += chunk_size
#
#
# def delete_sheet(spreadsheet_id, sheet_name, creds=None, service=None):
#     creds = get_creds() if creds is None else creds  # get_creds() if creds is None else creds
#     service = build('sheets', 'v4', credentials=creds) if service is None else service
#     return service.spreadsheets().batchUpdate(
#         spreadsheetId=spreadsheet_id,
#         body={'requests': [{"deleteSheet": {"sheetId": sheet_id_from_name(sheet_name, spreadsheet_id)}}]}
#     ).execute()
#
#
# def create_sheet(spreadsheet_id: str, sheet: str, creds=None):
#     creds = get_creds() if creds is None else creds
#     sheetservice = build('sheets', 'v4', credentials=creds)
#
#     body = {
#         "requests": {
#             "addSheet": {
#                 "properties": {
#                     "title": sheet
#                 }
#             }
#         }
#     }
#
#     sheetservice.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
#
#
