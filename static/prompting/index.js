'use strict';


const PROMPT_TEMPLATE = `
I want to write a PostgreSQL query. It can be multple statements separated by semi-colons (";").
Please put double quotes around column names when writing the query.

{{schema}}

Please write a query that returns values as described bellow:
{{userPrompt}}
`;

const getPrompt = (schema, userPrompt) => {
  const schemaPrefix = 'The tables I\'d like to query have the following schema:\n';
  console.log('schema', schema);
  if(schema) {
    schema = schemaPrefix + schema;
  }
  return PROMPT_TEMPLATE
    .replace('{{schema}}', schema)
    .replace('{{userPrompt}}', userPrompt);
};


/**
 * Turn table name and schema into text for AI table definition.
 * @param {string} tableName The table nme to be defined
 * @param {Array[Object]} schema The schema of the table to be defined
 * @returns {string} The table definition
 */
const tableSchemaToText = (tableName, schema) => {
  const columnDefinitions = schema.map(column => `"${column.name}" ${column.data_type}`).join(', ');
  return `${tableName}(${columnDefinitions})`;
}

/**
 * Performs an asynchronous POST request to the specified URL.
 *
 * @param {string} url - The URL to send the request to.
 * @param {Object} [requestBody={}] - The request body to be sent as JSON.
 * @return {Promise<Object>} A promise that resolves to the JSON response.
 */
const fetchApi = async (url, requestBody = {}) => {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

  return response.json();
};

/**
 * Checks if the given value is a plain object.
 *
 * @param {*} value - The value to check.
 * @return {boolean} True if the value is a plain object, false otherwise.
 */
const isPlainObject = (value) => {
  return typeof value === 'object' && !Array.isArray(value) && value !== null;
};


/**
 * Renders a customizable table component.
 *
 * @param {Object} props - The component props.
 * @param {string[]} props.headers - The table headers.
 * @param {Array<Array<*>>} props.rows - The table rows data.
 * @param {string} [props.width='50%'] - The table width.
 * @param {string} [props.height='50%'] - The table height.
 * @param {Object<string, React.ComponentType<{row: Object}>>} [props.replaceRows] - Custom components to replace specific cells.
 * @param {Object} [props.style] - Additional styles for the table container.
 * @return {JSX.Element} The rendered table component.
 */
const Table = ({
  headers,
  rows,
  width = '50%',
  height = '50%',
  replaceRows,
  style,
}) => {
  return (
    <div
      style={{
        width,
        height,
        overflow: 'scroll',
        ...(style || {}),
      }}
    >
      <table>
        {/* <thead> */}
          <tr>
            {headers.map((header, index) => (
              <th key={`header-${index}`}>{header}</th>
            ))}
          </tr>
        {/* </thead> */}
        {/* <tbody> */}
          {rows.map((row, rowIndex) => (
            <tr key={`row-${rowIndex}`}>
              {row.map((cell, cellIndex) => {
                if (replaceRows && replaceRows[cellIndex]) {
                  const CustomComponent = replaceRows[cellIndex];
                  const rowData = headers.reduce((acc, header, index) => {
                    acc[header] = row[index];
                    return acc;
                  }, {});
                  return (
                    <td key={`cell-${rowIndex}-${cellIndex}`}>
                      <CustomComponent row={rowData} />
                    </td>
                  );
                }
                return <td key={`cell-${rowIndex}-${cellIndex}`}>{cell || '_'}</td>;
              })}
            </tr>
          ))}
        {/* </tbody> */}
      </table>
    </div>
  );
};


/**
 * Sanitizes a table name to ensure it's valid for database use.
 *
 * @param {string} tableName - The original table name to sanitize.
 * @return {string} The sanitized table name.
 */
const sanitizeTableName = (tableName) => {
  const NUMERIC_CHARS = '0123456789';
  const VALID_CHAR_REGEX = /[^a-zA-Z0-9]/g;

  let sanitizedName = tableName;

  // Prepend underscore if the table name starts with a number
  if (NUMERIC_CHARS.includes(sanitizedName[0])) {
    sanitizedName = '_' + sanitizedName;
  }

  // Replace any non-alphanumeric characters with underscores
  return sanitizedName.replace(VALID_CHAR_REGEX, '_');
};


/**
 * @fileoverview Provides a loading and toast notification system for React applications.
 */

/**
 * Enum for loading event types.
 * @enum {string}
 */
const LoadingType = {
  ADD_TO_WAIT_FOR_RESPONSE: 'addToWaitForResponse',
  REMOVE_TO_WAIT_FOR_RESPONSE: 'removeToWaitForResponse',
  TOAST: 'toast',
};

/**
 * Creates Event objects for each loading type.
 * @type {Object<string, Event>}
 */
const loadingEvents = Object.keys(LoadingType).reduce((acc, key) => {
  acc[key] = new Event(LoadingType[key]);
  return acc;
}, {});

/**
 * Dispatches a loading event.
 * @param {Event} loadingEvent - The event to dispatch.
 */
const dispatchLoadingEvent = (loadingEvent) => {
  document.dispatchEvent(loadingEvent);
};

/**
 * Adds an event listener for a loading type.
 * @param {string} loadingType - The type of loading event to listen for.
 * @param {Function} callback - The function to call when the event is triggered.
 */
const addLoadingListener = (loadingType, callback) => {
  document.addEventListener(loadingType, callback, false);
};

/**
 * Starts waiting for a response.
 */
const startWaitForResponse = () => {
  dispatchLoadingEvent(loadingEvents.ADD_TO_WAIT_FOR_RESPONSE);
};

/**
 * Stops waiting for a response.
 */
const stopWaitForResponse = () => {
  dispatchLoadingEvent(loadingEvents.REMOVE_TO_WAIT_FOR_RESPONSE);
};

/**
 * Adds a listener for the start of a response wait.
 * @param {Function} callback - The function to call when waiting starts.
 */
const onResponseWaitStart = (callback) => {
  addLoadingListener(LoadingType.ADD_TO_WAIT_FOR_RESPONSE, callback);
};

/**
 * Adds a listener for the end of a response wait.
 * @param {Function} callback - The function to call when waiting ends.
 */
const onResponseWaitEnd = (callback) => {
  addLoadingListener(LoadingType.REMOVE_TO_WAIT_FOR_RESPONSE, callback);
};

/**
 * Stores the current toast message.
 * @type {{message: string}}
 */
const toastData = { message: '' };

/**
 * Displays a toast message.
 * @param {string} message - The message to display in the toast.
 */
const showToast = (message) => {
  toastData.message = message;
  console.log('Toast:', message);
  dispatchLoadingEvent(loadingEvents.TOAST);
};

/**
 * Adds a listener for toast events.
 * @param {Function} callback - The function to call when a toast is shown.
 */
const onToast = (callback) => {
  const wrappedCallback = () => {
    callback(toastData.message);
  };
  addLoadingListener(LoadingType.TOAST, wrappedCallback);
};

/**
 * A React component that displays toast messages.
 * @return {JSX.Element} The rendered Toast component.
 */
const Toast = () => {
  const [message, setMessage] = React.useState('');
  const [className, setClassName] = React.useState('');
  const toastCount = React.useRef(0);

  const displayToast = (msg) => {
    console.log(`Displaying toast: "${msg}"`);
    toastCount.current++;
    setMessage(msg);
    setClassName('show');

    setTimeout(() => {
      toastCount.current--;
      if (toastCount.current === 0) {
        setMessage('');
        setClassName('');
      }
    }, 3000);
  };

  React.useEffect(() => {
    onToast(displayToast);
  }, []);

  return (
    <div id="toast" className={className}>
      {message}
    </div>
  );
};


/**
 * A component for uploading Excel files to a database table.
 * @param {!Object} props - The component props.
 * @param {!Array<string>} props.databases - List of available databases.
 * @param {string} props.currentDatabase - The currently selected database.
 * @param {function(string): void} props.setCurrentDatabase - Function to set the current database.
 * @return {!React.Component} The rendered upload form component.
 */
const UploadTable = ({databases, currentDatabase, setCurrentDatabase}) => {
  const [xlsxFile, setXlsxFile] = React.useState(null);
  const [newDbTableName, setNewDbTableName] = React.useState('');
  const [xlsxSheetName, setXlsxSheetName] = React.useState('');
  const [sheets, setSheets] = React.useState([]);

  /**
   * Fetches and sets the list of sheets from the selected Excel file.
   * @return {!Promise<void>}
   */
  const checkFileSheets = React.useCallback(async () => {
    if (!xlsxFile) return;

    const formData = new FormData();
    formData.append('file', xlsxFile);

    try {
      const response = await fetch('/get-xlsx-sheets', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();

      if (data.success) {
        setSheets(data.sheets);
        if (data.sheets.length > 0) {
          setXlsxSheetName(data.sheets[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching sheets:', error);
      showToast('Failed to fetch sheets from the file');
    }
  }, [xlsxFile]);

  React.useEffect(() => {
    checkFileSheets();
  }, [checkFileSheets]);

  /**
   * Handles file selection change.
   * @param {!Event} event - The change event.
   */
  const onFileChange = (event) => {
    setXlsxFile(event.target.files[0]);
  };

  /**
   * Handles file upload to the server.
   * @return {!Promise<void>}
   */
  const onFileUpload = async () => {
    if (!xlsxFile || !newDbTableName || !xlsxSheetName || !currentDatabase) {
      showToast(`Please select a table name, sheet name, database, and file`);
      return;
    }

    try {
      startWaitForResponse();
      const formData = new FormData();
      formData.append('file', xlsxFile);

      const config = {
        database_id: currentDatabase,
        table_name: newDbTableName,
        sheet_name: xlsxSheetName,
      };
      const blob = new Blob([JSON.stringify(config)], {type: 'application/json'});
      formData.append('config', blob, 'config.json');

      const response = await fetch('/upload-table', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();

      if (data.success) {
        showToast('File uploaded successfully');
      } else if (data.error) {
        showToast(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      showToast('An error occurred while uploading the file');
    } finally {
      stopWaitForResponse();
    }
  };

  return (
    <div className="wrapper">
      <h3>Upload .xlsx, .xls or .xlsm to Database</h3>
      <div>
        <label htmlFor="database-select">Database: </label>
        <select
          id="database-select"
          value={currentDatabase}
          onChange={(e) => setCurrentDatabase(e.target.value)}
        >
          {databases.map((database, index) => (
            <option key={`database-${index}`} value={database}>
              {database}
            </option>
          ))}
        </select>

        <label htmlFor="table-name-input">Table Name: </label>
        <input
          id="table-name-input"
          type="text"
          value={newDbTableName}
          onChange={(e) => setNewDbTableName(sanitizeTableName(e.target.value))}
        />

        <label htmlFor="file-input">File: </label>
        <input id="file-input" type="file" onChange={onFileChange} />

        {sheets.length > 0 && (
          <div>
            <label htmlFor="sheet-select">Sheet Name: </label>
            <select
              id="sheet-select"
              value={xlsxSheetName}
              onChange={(e) => setXlsxSheetName(e.target.value)}
            >
              {sheets.map((sheet, index) => (
                <option key={`sheet-${index}`} value={sheet}>
                  {sheet}
                </option>
              ))}
            </select>
          </div>
        )}

        <button className="btn" onClick={onFileUpload}>
          Upload!
        </button>
      </div>
    </div>
  );
};


/**
 * A component that displays a loading screen when waiting for a response.
 * @return {React.Component|null} The rendered loading screen or null.
 */
const WaitForResponseUI = () => {
  const [waitingForResponse, setWaitingForResponse] = React.useState(false);

  React.useEffect(() => {
    onResponseWaitStart(() => setWaitingForResponse(true));
    onResponseWaitEnd(() => setWaitingForResponse(false));
  }, []);

  return !waitingForResponse ? null : (
    <div className="screen">
      <div>
        <h1> This may take a moment. </h1>
        <h5>Please don't close or refresh this page. Thank you</h5>
      </div>
      <br/>
      <div className="loader">
        <div className="dot"></div>
        <div className="dot"></div>
        <div className="dot"></div>
      </div>
    </div>
  );
};

const HomeButton = () => {
  return (
    <div className="float-top-left">
      <button onClick={()=>{window.location.href = '/';}}>
        Home
      </button>
    </div>
  );
}


/**
 * The main application component.
 * @return {React.Component} The rendered application.
 */
const App = () => {
  const [canUseGoogleApi, setCanUseGoogleApi] = React.useState(false);

  const [databases, setDatabases] = React.useState([]);
  const [currentDatabase, setCurrentDatabase] = React.useState('');
  const [creatingDatabase, setCreatingDatabase] = React.useState(false);

  const [tableNames, setTableNames] = React.useState('');

  const [userPrompt, _setUserPrompt] = React.useState(localStorage.getItem('userPrompt') || '');
  const setUserPrompt = v => {
    _setUserPrompt(v);
    localStorage.setItem('userPrompt', v);
  }
  const [finalPrompt, setFinalPrompt] = React.useState('');

  /**
   * Fetches available databases from the server.
   * @return {Promise<void>}
   */
  const fetchDatabases = async () => {
    const data = await fetchApi('/databases');
    if (data.success) {
      setDatabases(data.databases);
      if (data.databases.length > 0 && !currentDatabase) {
        setCurrentDatabase(data.databases[0]);
      }
    }
  };

  /**
   * Fetches to see if Google API is available
   * @returns {Promise<void>}
   */
  const fetchTableSchema = async tableName => {
    const data = await fetchApi('/table-schema', {
      database_id: currentDatabase, table_name: tableName
    });
    console.log('schema', data);
    if (data.success) {
      return data.schema;
    } else if (data.error) {
      showToast(data.error);
    }
    return null;
  };

  const generatePrompt = async () => {
    try{
      startWaitForResponse();

      const tableSchemas = {};
      if(tableNames.trim()) {
        const tableNamesArray = tableNames.split(',').map(name => name.trim());
        for (const tableName of tableNamesArray) {
          const schema = await fetchTableSchema(tableName);
          tableSchemas[tableName] = schema
          console.log('schema', schema);
          if (!schema) {
            setTimeout(() => {
              showToast(`Failed to fetch schema for table "${tableName}"`);
            }, 3000);
            return;
          }
        }
      }

      let shcemaText = '';
      console.log('tableSchemas.length', tableSchemas.length)
      if (Object.keys(tableSchemas).length > 0) {
        shcemaText = Object.keys(tableSchemas).map(k=>tableSchemaToText(k, tableSchemas[k])).join('\n\n');
      }
      const prompt = getPrompt(shcemaText, userPrompt)
      // const prompt = PROMPT_TEMPLATE
      // .replace('{{userPrompt}}', userPrompt)
      // .replace('{{schema}}', Object.keys(tableSchemas).map(k=>tableSchemaToText(k, tableSchemas[k])).join('\n\n'));

      setFinalPrompt(prompt);
    } finally {
      stopWaitForResponse();
    }
  };

  React.useEffect(() => {
    fetchDatabases();
  }, []);

  if (databases.length === 0) {
    return <div>
      <div>
        <p> No databases found. </p>
      </div>
    </div>
  }

  return (
    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center'}}>
      <HomeButton/>
      <Toast/>
      <WaitForResponseUI/>

      
      
      <h1> SQL AI Prompting </h1>
      <label htmlFor="database-select"> Database: </label>
      <select
        id="database-select"
        value={currentDatabase}
        onChange={(e) => setCurrentDatabase(e.target.value)}
      >
        {databases.map((database, index) => (
          <option key={`database-${index}`} value={database}>
            {database}
          </option>
        ))}
      </select>
      <label> Table Names (separate by commas) </label>
      <input type="text" value={tableNames} onChange={e => setTableNames(e.target.value)}/>
      <label> Prompt: </label>
      <textarea className='user-prompt' value={userPrompt} onChange={e => setUserPrompt(e.target.value)}>
        
      </textarea>

      <button onClick={generatePrompt}> Generate Pompt </button>

      <label>Final Prompt:</label>
      <textarea className='prompt' readOnly value={finalPrompt}/>
    </div>
  );
};

// Render the application
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App/>);

