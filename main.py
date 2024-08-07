"""Flask application for Excel-to-PostgreSQL data management.

This application provides functionality to upload Excel sheets to a PostgreSQL
database, download data from the database as Excel sheets, and interact with
Google Sheets API.

The application uses openpyxl for Excel file operations and psycopg2 for
PostgreSQL database interactions.

Main endpoints:
    - '/': Serve the home page.
    - '/static/<path:filename>': Serve static files.
    - '/upload-table': Upload an Excel sheet to a PostgreSQL database.
    - '/download-table': Download data from a PostgreSQL database as an Excel sheet.
    - '/query-database': Query a database and return results in various formats.
    - '/authorize-google-sheets': Authorize with Google Sheets API.
    - '/google-sheets': Interact with Google Sheets.

For detailed information on each endpoint, refer to their respective docstrings.
"""

import enum
import io
import json
import os
import uuid
import traceback
import string
import datetime
from typing import Any

import flask
import psycopg2
import werkzeug.utils
import werkzeug.datastructures
from google_auth_oauthlib.flow import InstalledAppFlow

import databases
import excel_to_postgres
import google_api
import postgres
import server_util


IS_GUNICORN = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")


class OutputTypes(enum.Enum):
    """Enumeration of supported output types for database queries."""

    HTML_TABLE = 'html'
    DOWNLOAD = 'xlsx'
    GOOGLE_SHEET = 'googleSheet'


class ExcelUploadError(Exception):
    pass


ALLOWED_TABLE_NAME_CHARS = string.ascii_letters + string.digits + ' _'
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
STATIC_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'xlsm'}
EXCEL_EXTENSIONS = {'xlsx', 'xls', 'xlsm'}
CSV_EXTENSIONS = {'csv'}
ERROR_MESSAGES = {
    'no_file': 'Request has no file part',
    'no_config': 'Request has no config part',
    'no_file_selected': 'No file selected',
    'database_not_found': 'Database not found',
    'file_type_not_allowed': 'File type not allowed'
}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

app = flask.Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER
app.secret_key = 'This is your secret key to utilize session in Flask'


@app.route('/')
def index():
    """Serve the home page.

    Returns:
        flask.Response: The home page HTML.
    """
    return flask.send_from_directory(
        app.config['STATIC_FOLDER'],
        os.path.join('home', 'index.html')
    )


@app.route('/prompting')
def prompting():
    """Serve the prompting page.

    Returns:
        flask.Response: The prompting page HTML.
    """
    return flask.send_from_directory(
        app.config['STATIC_FOLDER'],
        os.path.join('prompting', 'index.html')
    )


@app.route('/static/<path:filename>')
def serve_static(filename: str):
    """Serve static files.

    Args:
        filename: The name of the file to serve.

    Returns:
        flask.Response: The requested static file.
    """
    return flask.send_from_directory(app.config['STATIC_FOLDER'], filename)


def process_table_file(
        file: werkzeug.datastructures.FileStorage,
        config: dict[str, str],
        database_id: str
) -> None:
    filename = werkzeug.utils.secure_filename(file.filename)
    file_extension = server_util.get_file_extension(filename)
    file_id = f'{uuid.uuid4()}-{uuid.uuid1()}'
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_id}.{file_extension}')

    try:
        file.save(file_path)

        if file_extension not in ALLOWED_EXTENSIONS:
            sheets = excel_to_postgres.get_sheet_names_xlsx(file_path)
            if config['sheet_name'] not in sheets:
                raise ExcelUploadError(f'Sheet not found. Available ({", ".join(sheets)})')

        database_params = databases.get_database_params_from_id(database_id)

        if file_extension in EXCEL_EXTENSIONS:
            excel_to_postgres.xlsx_to_sql(
                file_path,
                config['sheet_name'],
                config['table_name'],
                database_params
            )
        elif file_extension in CSV_EXTENSIONS:
            excel_to_postgres.csv_to_sql(
                file_path,
                config['table_name'],
                database_params
            )
        else:
            raise ExcelUploadError(f'Unsupported file type: {file_extension}')
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass


@app.route('/upload-table', methods=['POST'])
def upload_table() -> flask.Response | tuple[flask.Response, int]:
    """Upload an Excel sheet to a PostgreSQL database.

    Expects two files in the request:
    1. The Excel file (.xlsx, .xls, or .xlsm).
    2. A JSON config file containing database_id, table_name, and sheet_name.

    Returns:
        flask.Response: JSON response indicating success or error.

    Raises:
        ValueError: If the file or config is missing.
        psycopg2.Error: For database connection or query execution errors.
    """
    try:
        if 'file' not in flask.request.files:
            raise ExcelUploadError(ERROR_MESSAGES['no_file'])
        if 'config' not in flask.request.files:
            raise ExcelUploadError(ERROR_MESSAGES['no_config'])

        file = flask.request.files['file']
        config = flask.request.files['config']

        if file.filename == '' or config.filename == '':
            raise ExcelUploadError(ERROR_MESSAGES['no_file_selected'])

        if not server_util.allowed_file(file.filename, ALLOWED_EXTENSIONS):
            raise ExcelUploadError(ERROR_MESSAGES['file_type_not_allowed'])

        config_data = json.loads(config.read().decode('utf-8'))
        database_id = config_data['database_id']

        if not databases.database_exists(database_id):
            raise ExcelUploadError(ERROR_MESSAGES['database_not_found'])

        process_table_file(file, config_data, database_id)

        return flask.jsonify({'success': True})

    except ExcelUploadError as e:
        return flask.jsonify({'error': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return flask.jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


@app.route('/databases', methods=['POST'])
def get_databases():
    """Get the list of available databases.

    Returns:
        flask.Response: JSON response with the list of database IDs.
    """
    return flask.jsonify({'success': True, 'databases': databases.get_database_ids()})


@app.route('/append-database', methods=['POST'])
def append_database():
    """Append a new database to the list of available databases.

    Expects a JSON payload with 'id', 'host', 'port', 'user', 'password',
    and 'database' fields.

    Returns:
        flask.Response: JSON response indicating success or error.
    """
    data = flask.request.get_json()
    required_fields = ['id', 'host', 'port', 'user', 'password', 'database']
    if not all(field in data for field in required_fields):
        return flask.jsonify({'error': 'Missing required fields'}), 400

    database_params = postgres.DatabaseParameters(
        host=data['host'],
        database=data['database'],
        user=data['user'],
        password=data['password'],
        port=data['port']
    )

    databases.set_database(data['id'], database_params)

    return flask.jsonify({'success': True})


@app.route('/remove-database', methods=['POST'])
def remove_database():
    """Remove a database from the list of available databases.

    Expects a JSON payload with an 'id' field.

    Returns:
        flask.Response: JSON response indicating success or error.
    """
    data = flask.request.get_json()
    if 'id' not in data:
        return flask.jsonify({'error': 'Missing required fields'}), 400

    databases.remove_database(data['id'])
    return flask.jsonify({'success': True})


def valid_table_name(name: str):
    return all(char in ALLOWED_TABLE_NAME_CHARS for char in name)


@app.route('/table-schema', methods=['POST'])
def get_table_schema():
    """Get the schema of a table in a database.

    Expects a JSON payload with 'database_id' and 'table_name' fields.

    Returns:
        flask.Response: JSON response with the table schema or an error message.
    """
    data = flask.request.get_json()
    if 'database_id' not in data or 'table_name' not in data:
        return flask.jsonify({'error': 'Missing required fields'}), 400

    if not valid_table_name(data['table_name']):
        return flask.jsonify({'error': f'"{data["table_name"]}" is not a valid table name.'})

    try:
        result = databases.get_table_schema(data['database_id'], data['table_name'])

        if isinstance(result, dict):
            return flask.jsonify(result)

        return flask.jsonify({'success': True, 'schema': result})
    except Exception as e:
        return flask.jsonify({'error': f'An unexpected error occurred: {e}'}), 500


def validate_request_data(data: dict[str, Any]) -> None:
    required_fields = ['database_id', 'query', 'output_type']
    if not all(field in data for field in required_fields):
        raise ValueError('Missing required fields')

    if not databases.database_exists(data['database_id']):
        raise ValueError('Database not found')


def handle_html_table(table: list[list]) -> dict[str, Any]:
    return {
        'success': True,
        'table': table,
        'outputType': OutputTypes.HTML_TABLE.value
    }


def handle_download(table:  list[list] | list[dict], app_config: dict[str, str]) -> dict[str, Any]:
    file_path = os.path.join(app_config['DOWNLOAD_FOLDER'], f'{uuid.uuid4()}.xlsx')
    excel_to_postgres.create_xlsx(table, file_path, 'Data')
    return {
        'success': True,
        'link': f'/download-file?file={os.path.basename(file_path)}',
        'file': 'QueriedData.xlsx',
        'outputType': OutputTypes.DOWNLOAD.value,
    }


def handle_google_sheet(table:  list[list] | list[dict], data: dict[str, str]) -> dict[str, Any]:
    if not google_api.has_tokens():
        raise ValueError('Google API tokens not found. Please Re-Authorize the Google API.')

    if not google_api.valid_credentials():
        raise ValueError('Google API credentials are invalid. Please Re-Authorize the Google API.')

    if 'spreadsheet_id' not in data or 'sheet_name' not in data:
        raise ValueError('Missing required fields (spreadsheet_id or sheet_name)')

    for row in table:
        if isinstance(row, list):
            for i, value in enumerate(row):
                if isinstance(value, datetime.datetime):
                    row[i] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, datetime.date):
                    row[i] = value.strftime('%Y-%m-%d')
        elif isinstance(row, dict):
            for key, value in row.items():
                if isinstance(value, datetime.datetime):
                    row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, datetime.date):
                    row[key] = value.strftime('%Y-%m-%d')

    spreadsheet_id = google_api.fix_spreadsheet_id_if_link(data['spreadsheet_id'])
    sheet_name = data['sheet_name']

    google_api.add_table_and_clear_sheet(spreadsheet_id, table, sheet_name)
    return {
        'success': True,
        'outputType': OutputTypes.GOOGLE_SHEET.value,
    }


@app.route('/query-database', methods=['POST'])
def query_database():
    """Query a database and return the result in a specified format."""
    try:
        data = flask.request.get_json()
        validate_request_data(data)

        result = databases.run_query(data['database_id'], data['query'], data.get('sub_query'))
        if isinstance(result, dict) and 'error' in result:
            return flask.jsonify(result), 500

        output_type = OutputTypes(data['output_type'])

        if output_type == OutputTypes.HTML_TABLE:
            response = handle_html_table(result)
        elif output_type == OutputTypes.DOWNLOAD:
            response = handle_download(result, app.config)
        elif output_type == OutputTypes.GOOGLE_SHEET:
            response = handle_google_sheet(result, data)
        else:
            raise ValueError('Invalid output type')

        return flask.jsonify(response)

    except ValueError as e:
        return flask.jsonify({'error': str(e)}), 400
    except Exception as e:
        return flask.jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


@app.route('/download-file', methods=['GET'])
def download_file():
    """Download a file from the server.

    Expects a 'file' query parameter with the filename.

    Returns:
        flask.Response: File download response or error message.
    """
    if 'file' not in flask.request.args:
        return flask.jsonify({'error': 'Missing required fields'}), 400

    file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], flask.request.args['file'])
    if not os.path.exists(file_path):
        return flask.jsonify({'error': 'File not found'}), 400

    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        return flask.send_file(
            io.BytesIO(file_data),
            download_name='DownloadedFile.' + server_util.get_file_extension(file_path),
            as_attachment=True
        )
    except Exception as e:
        return flask.jsonify({'error': str(e)}), 500


@app.route('/get-xlsx-sheets', methods=['POST'])
def get_xlsx_sheets():
    """Get the sheet names of an Excel file.

    Expects an Excel file in the request.

    Returns:
        flask.Response: JSON response with sheet names or error message.
    """
    if 'file' not in flask.request.files:
        return flask.jsonify({'error': 'Request has no file part'})

    file = flask.request.files['file']

    if file.filename == '':
        return flask.jsonify({'error': 'No file selected'})

    if file and server_util.allowed_file(file.filename, ALLOWED_EXTENSIONS):
        filename = werkzeug.utils.secure_filename(file.filename)
        file_extension = server_util.get_file_extension(filename)

        if file_extension in CSV_EXTENSIONS:
            return flask.jsonify({'error': 'CSV files are not supported', 'csv': True})

        file_id = f'{uuid.uuid4()}-{uuid.uuid1()}'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_id}.{file_extension}')
        try:
            file.save(file_path)
            sheets = excel_to_postgres.get_sheet_names_xlsx(file_path)
            return flask.jsonify({'success': True, 'sheets': sheets})
        except Exception as e:
            raise
        finally:
            try:
                os.remove(file_path)
            except OSError:
                pass
    else:
        return flask.jsonify({'error': 'File type not allowed'})


@app.route('/google-has-credentials', methods=['POST'])
def google_has_credentials():
    """Check if Google API credentials are present.

    Returns:
        flask.Response: JSON response indicating if credentials are present.
    """
    return flask.jsonify({'success': True, 'hasCredentials': google_api.has_credentials()})


@app.route('/authorize-google-sheets', methods=['GET'])
def authorize_google_sheets():
    """Initiate the Google Sheets API authorization flow.

    Returns:
        flask.Response: Redirect to Google's authorization page.
    """
    if not google_api.has_credentials():
        return flask.redirect(flask.url_for('index'))

    flow = InstalledAppFlow.from_client_secrets_file(
        google_api.GOOGLE_API_CREDENTIALS_PATH, google_api.SCOPES
    )
    flow.redirect_uri = flask.url_for('authorize_google_sheets_callback', _external=True)
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
    )
    return flask.redirect(auth_url)


@app.route('/authorize-google-sheets-callback', methods=['GET'])
def authorize_google_sheets_callback():
    """Handle the Google Sheets API authorization callback.

    Returns:
        flask.Response: Redirect to the home page after successful authorization.
    """
    if not google_api.has_credentials():
        return flask.redirect(flask.url_for('index'))

    flow = InstalledAppFlow.from_client_secrets_file(
        google_api.GOOGLE_API_CREDENTIALS_PATH, google_api.SCOPES
    )
    flow.redirect_uri = flask.url_for('authorize_google_sheets_callback', _external=True)
    code = flask.request.args.get('code')
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open(google_api.TOKENS_PATH, "w") as token:
        token.write(creds.to_json())

    return flask.redirect(flask.url_for('index'))


@app.route('/google-valid-tokens', methods=['POST'])
def google_valid_tokens():
    """Check if Google API credentials are valid.

    Returns:
        flask.Response: JSON response indicating token validity.
    """
    if not google_api.has_credentials():
        return flask.jsonify({'valid': False})

    return flask.jsonify({'valid': google_api.valid_credentials()})


@app.route('/google-sheets', methods=['POST'])
def google_sheets():
    """Get the sheet names of a Google Spreadsheet.

    Expects a JSON payload with a 'spreadsheet_id' field.

    Returns:
        flask.Response: JSON response with sheet names or error message.
    """
    if not google_api.has_credentials():
        return flask.jsonify({'error': f'Google API credentials not found. Missing `{google_api.GOOGLE_API_CREDENTIALS_PATH}` found.'}), 400

    data = flask.request.get_json()
    if 'spreadsheet_id' not in data:
        return flask.jsonify({'error': 'Missing required fields'}), 400

    try:
        sheets = google_api.get_sheets(google_api.fix_spreadsheet_id_if_link(data['spreadsheet_id']), names=True)
    except Exception as e:
        return flask.jsonify({'error': str(e)}), 500

    return flask.jsonify({'success': True, 'sheets': sheets})


@app.route('/google-place-table-from-query', methods=['POST'])
def google_place_table():
    """Place a table from a database query into a Google Spreadsheet.

    Expects a JSON payload with the following keys:
    - spreadsheet_id: ID of the Google Spreadsheet
    - sheet_name: Name of the sheet within the spreadsheet
    - query: SQL query to execute
    - database_id: ID of the database to query

    Returns:
        A JSON response indicating success or containing an error message.

    Raises:
        psycopg2.Error: If there's an error executing the database query.
        Exception: If there's an error adding the table to the Google Sheet.
    """
    if not google_api.has_credentials():
        return flask.jsonify({'error': f'Google API credentials not found. Missing `{google_api.GOOGLE_API_CREDENTIALS_PATH}` found.'}), 400

    if not google_api.has_tokens():
        return flask.jsonify({'error': 'Google API tokens not found. Please Authorize the Google API.'}), 400

    if not google_api.valid_credentials():
        return flask.jsonify({'error': 'Google API credentials are invalid. Please Re-Authorize the Google API.'}), 400

    data = flask.request.get_json()
    required_fields = ['spreadsheet_id', 'sheet_name', 'query', 'database_id']
    if not all(field in data for field in required_fields):
        return flask.jsonify({'error': 'Missing required fields'}), 400

    try:
        table = postgres.execute_query(
            databases.get_database_params_from_id(data['database_id']),
            data['query']
        )
    except psycopg2.Error as e:
        return flask.jsonify({'error': str(e)}), 500

    try:
        google_api.add_table_to_sheet(
            data['spreadsheet_id'],
            table,
            data['sheet_name'],
        )
    except Exception as e:
        return flask.jsonify({'error': str(e)}), 500

    return flask.jsonify({'success': True})


# Saved Query Section

@app.route('/get-queries', methods=['POST'])
def get_saved_queries():
    """Retrieve all saved queries.

    Returns:
        A JSON response containing a list of saved queries.
    """
    return flask.jsonify({'success': True, 'queries': databases.get_queries()})


@app.route('/save-query', methods=['POST'])
def save_query():
    """Save a new query.

    Expects a JSON payload with the following keys:
    - name: Name of the query
    - query: SQL query string

    Returns:
        A JSON response indicating success or containing an error message.
    """
    data = flask.request.get_json()
    if 'name' not in data or 'query' not in data:
        return flask.jsonify({'error': 'Missing required fields'}), 400

    databases.set_query(data['name'], data['query'])
    return flask.jsonify({'success': True})


def initialize_backend():
    """
    Initialize the backend services.

    Loads database connection parameters and saved queries into memory
    """
    databases.initialize_database()


def main():
    """Main function to run the Flask app.

    Initializes the database connections and saved queries,
    then starts the Flask development server.
    """
    initialize_backend()
    app.run(port=7777)


if IS_GUNICORN:
    initialize_backend()
elif __name__ == '__main__':
    main()



