'use strict';


/** @const {!Object<string, string>} */
const outputTypes = {
  htmlTable: 'html',
  download: 'xlsx',
  googleSheet: 'googleSheet',
};


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
 * A component for adding a new database connection.
 *
 * @param {Object} props - The component props.
 * @param {Function} props.fetchDatabases - Function to refresh the list of databases.
 * @param {Function} props.setCreatingDatabase - Function to update the database creation state.
 * @return {JSX.Element} The rendered form for adding a new database.
 */
const AddNewDatabase = ({ fetchDatabases, setCreatingDatabase }) => {
  const [newDatabase, setNewDatabase] = React.useState({
    id: 'My Cool Database',
    host: 'localhost',
    user: '',
    password: '',
    database: '',
    port: '5432',
  });

  /**
   * Updates a specific field in the newDatabase state.
   *
   * @param {string} field - The field to update.
   * @param {string} value - The new value for the field.
   */
  const updateDatabaseField = (field, value) => {
    setNewDatabase(prevState => ({
      ...prevState,
      [field]: field === 'database' || field === 'port' ? value.trim() : value,
    }));
  };

  /**
   * Handles the submission of the new database form.
   */
  const handleSubmit = async () => {
    await fetchApi('/append-database', newDatabase);
    fetchDatabases();
    setNewDatabase({
      id: 'My Cool Database',
      host: 'localhost',
      user: '',
      password: '',
      database: '',
      port: '5432',
    });
    setCreatingDatabase(false);
  };

  return (
    <div className="container">
      {Object.entries(newDatabase).map(([field, value]) => (
        <React.Fragment key={field}>
          <label htmlFor={field}>{field.charAt(0).toUpperCase() + field.slice(1)}: </label>
          <input
            type={field === 'password' ? 'password' : 'text'}
            id={field}
            value={value}
            onChange={(e) => updateDatabaseField(field, e.target.value)}
          />
        </React.Fragment>
      ))}
      <br />
      <button className="btn" onClick={handleSubmit}>
        New Database
      </button>
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
      if(data.error) {
        if(!data.csv) {
          showToast(`error: ${data.error}`)
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
    if (!xlsxFile || !newDbTableName || !currentDatabase) {
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
 * A component for executing and managing database queries.
 * @param {!Object} props - The component props.
 * @param {!Array<string>} props.databases - List of available databases.
 * @param {string} props.currentDatabase - The currently selected database.
 * @param {boolean} props.canUseGoogleApi - Whether the user can use the Google API.
 * @return {!React.Component} The rendered query component.
 */
const Query = ({currentDatabase, canUseGoogleApi}) => {
  // State declarations
  const [query, setQuery] = React.useState('');
  const [useSubQuery, setUseSubQuery] = React.useState(false);
  const [subQuery, setSubQuery] = React.useState('');
  const [table, setTable] = React.useState([]);
  const [savedQuery, setSavedQuery] = React.useState('current');
  const [savedQueries, setSavedQueries] = React.useState({current: ''});
  const [savingQueryAs, setSavingQueryAs] = React.useState({text: '', on: false});
  const [outputType, setOutputType] = React.useState(outputTypes.download);
  const [outputSpreadsheetId, setOutputSpreadsheetId] = React.useState('');
  const [outputSheetName, setOutputSheetName] = React.useState('');

  const codeEditor = React.useRef({editor: null}).current;

  // for event listener cleanup
  const lastKeydownFunc = React.useRef({value: null}).current;

  const overrideControlS = saveFunc => {
    const eventTrigger = e => {
      if (e.key === 's' && (e.metaKey || e.ctrlKey)){  // original deprecated --> (e.keyCode === 83 && (navigator.platform.match("Mac") ? e.metaKey : e.ctrlKey))
        e.preventDefault();
        if(saveFunc) saveFunc();
      }
    };

    document.addEventListener('keydown', eventTrigger);

    // cleanup/remove last event
    if(lastKeydownFunc.value) {
      document.removeEventListener('keydown', lastKeydownFunc.value);
    }
    
    lastKeydownFunc.value = eventTrigger;
  }

  React.useEffect(() => {
    initializeCodeEditor();
    loadQueries();
  }, []);

  React.useEffect(() => {
    overrideControlS(saveQuery);
  }, [query, savedQuery, savedQueries])

  /**
   * Checks if the Ace editor has been created.
   * @return {boolean} True if the editor exists, false otherwise.
   */
  const checkEditor = () => {
    const _class = 'ace_text-input';
    var editorsCreated = document.getElementsByClassName(_class);
    return editorsCreated.length > 0;
  };

  /**
   * Initializes the Ace editor.
   * @return {!Promise<void>}
   */
  const initializeCodeEditor = async () => {
    await new Promise((resolve) => setTimeout(resolve, 1));

    if (!document.getElementById('editor')) {
      await new Promise((resolve) => setTimeout(resolve, 100));
      return initializeCodeEditor();
    }

    try {
      var editor = ace.edit('editor', {
        theme: 'ace/theme/monokai',
        mode: 'ace/mode/html',
        placeholder: 'SQL code..'
      });
    } catch (e) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return initializeCodeEditor();
    }

    var modelist = ace.require('ace/ext/modelist');
    var modeName = modelist.getModeForPath('some.sql').mode;
    editor.session.setMode(modeName);
    editor.session.setValue('');
    editor.getSession().on('change', function() {
      var val = editor.getSession().getValue();
      setQuery(val || '');
    });
    editor.getSession().on("keydown", e => {
      // or e.key === 's'
      if (e.code === 'KeyS' && (e.metaKey || e.ctrlKey)){  // deprecated --> (e.keyCode === 83 && (navigator.platform.match("Mac") ? e.metaKey : e.ctrlKey))
        e.preventDefault();
        if(saveFunc) saveFunc();
      }
    })

    codeEditor.editor = editor;

    if (!checkEditor()) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return initializeCodeEditor();
    }
  };

  /**
   * Loads saved queries from the server.
   * @return {!Promise<void>}
   */
  const loadQueries = async () => {
    const data = await fetchApi('/get-queries', {});
    if (data.success) {
      setSavedQueries(data.queries);
      if (savedQuery === 'current') {
        setQuery(data.queries.current);
        await new Promise((resolve) => setTimeout(resolve, 1000));
        if (codeEditor.editor) {
          codeEditor.editor.getSession().setValue(data.queries.current);
        }
      }
    }
  };

  /**
   * Saves the current query to the server.
   * @param {string=} overrideName - Optional name to save the query as.
   * @return {!Promise<void>}
   */
  const saveQuery = async overrideName => {
    const name = overrideName || savedQuery;
    savedQueries[name] = query;
    setSavedQueries({...savedQueries});
    await fetchApi('/save-query', {name, query});
  };

  /**
   * Changes the current query to a saved one.
   * @param {string} k - The key of the saved query to load.
   */
  const changeQuery = k => {
    setSavedQuery(k);
    setQuery(savedQueries[k]);
    if (codeEditor.editor) {
      codeEditor.editor.getSession().setValue(savedQueries[k]);
    }
  };

  /**
   * Executes the current query.
   * @return {!Promise<void>}
   */
  const runQuery = async () => {
    try {
      if (!canUseGoogleApi && outputType === outputTypes.googleSheet) {
        showToast('Google API is not available!');
        return;
      }

      startWaitForResponse();
      const data = await fetchApi(
        '/query-database',
        {
          query,
          database_id: currentDatabase,
          output_type: outputType,
          spreadsheet_id: outputSpreadsheetId,
          sheet_name: outputSheetName,
          sub_query: useSubQuery ? savedQueries[subQuery] : null,
        }
      );
      if (data.success) {
        if (data.outputType === outputTypes.htmlTable) {
          setTable(data.table);
          showToast('Table Ready!');
        }
        if (data.outputType === outputTypes.download) {
          const a = document.createElement('a');
          a.href = data.link;
          a.download = data.file;
          a.click();
          showToast('Downloaded!');
        }
        if (data.outputType === outputTypes.googleSheet) {
          showToast('Outputed to Google Sheet!');
        }
      } else {
        showToast(`error: ${data.error}`);
      }
    } finally {
      stopWaitForResponse();
    }
  };

  return <div>
  <div className='wrapper'>
    <div>
      <div>
        <label>Saved Queries:</label>
        <br/>
        <select value={savedQuery} onChange={e=>{setSavedQuery(e.target.value);changeQuery(e.target.value);}}>
          {Object.keys(savedQueries).map((val, i)=><option key={`savedQuery-${i}`} value={val}>{val}</option>)}
        </select>
        <button className={savedQueries[savedQuery] === query ? 'btn' : 'btn-error'} onClick={async ()=>{
          // const data = await fetchApi('/save-query', {query, name: savedQuery});
          // if(data.success) {
          //   setSavedQueries([...savedQueries, savedQuery]);
          //   setSavedQuery('');
          // }
          console.log('save')
          saveQuery();
        }}>Save</button>
        {!savingQueryAs.on 
          ? null
          : <input type='text' value={savingQueryAs.text} onChange={e=>setSavingQueryAs({...savingQueryAs, text: (e.target.value || '')})} />}
          <button className='btn' onClick={async ()=>{
            if(savingQueryAs.on) {
              saveQuery(`${savingQueryAs.text}`);
              changeQuery(`${savingQueryAs.text}`);
            }
            setSavingQueryAs({...savingQueryAs, on: !savingQueryAs.on});
          }}> Save As </button>
      </div>
    <div>
    <label>Query: </label>
    {/* <textarea value={query} onChange={e=>setQuery(e.target.value)} cols="40" rows="5"></textarea> */}
    <div id="editor"></div> 
    </div>
    </div>
    <br/>
    <label htmlFor='subQuery'> Advanced: </label>
    <button className='btn' onClick={()=>{
      if(!useSubQuery && !savedQueries.hasOwnProperty(subQuery) && Object.keys(savedQueries).length > 0) {
        setSubQuery(Object.keys(savedQueries).map(k=>k)[0]);
      }
      setUseSubQuery(!useSubQuery)
    }}>
      {useSubQuery ? 'Sub-Query: On' : 'Sub-Query: Off'}
    </button>
    {!useSubQuery ? null 
    :<select value={subQuery} onChange={e=>{setSubQuery(e.target.value);}}>
      {Object.keys(savedQueries).map((val, i)=><option key={`subQuery-${i}`} value={val}>{val}</option>)}
    </select>}
    <br/>
    <select value={outputType} onChange={e=>setOutputType(e.target.value)}>
      {Object.keys(outputTypes)
        .filter(val=>(canUseGoogleApi ? true : (val !== 'googleSheet')))
        .map((val, i)=><option key={`outputType-${i}`} value={outputTypes[val]}>{val}</option>)}
    </select>
    
    {outputType !== outputTypes.googleSheet ? null : <div>
      <br/>
      <label>Spreadsheet Id or Url: </label>
      <input type='text' value={outputSpreadsheetId} onChange={e=>setOutputSpreadsheetId(e.target.value || '')} />
      <br/>
      <label>Sheet Name: </label>
      <input type='text' value={outputSheetName} onChange={e=>setOutputSheetName(e.target.value || '')} />
    </div>}

    <button className='btn' onClick={runQuery}>
      Query
    </button>
    
  </div>

  {/* <Table headers={['Available Reports']} rows={availableReports.map(val=>[val])} width='50vw' height='50vh'/> */}
    <div style={{margin: 50}}></div>
  {table.length === 0 ? null : 
    <Table 
      style={{margin: '50px'}}
      width='90vw' 
      height='50vh'
      headers={table[0]} 
      rows={table.slice(1)} 
    />}
</div>
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

/**
 * A button component for creating a new database.
 * @param {Object} props - The component props.
 * @param {boolean} props.creatingDatabase - Whether a database is currently being created.
 * @param {function(): void} props.toggleCreatingDatabase - Function to toggle database creation state.
 * @return {React.Component} The rendered button component.
 */
const CreateDatabaseButton = (props) => {
  const {creatingDatabase, toggleCreatingDatabase} = props;
  return (
    <div className="float-top-right">
      <button onClick={toggleCreatingDatabase}>
        {creatingDatabase ? 'X' : 'Create Database'}
      </button>
    </div>
  );
};

/**
 * A button component for authorizing Google Sheets.
 * @return {React.Component} The rendered button component.
 */
const AuthorizeGoogleSheetsButton = ({canUseGoogleApi}) => {
  /**
   * Redirects the user to the Google Sheets authorization link.
   */
  const authorizeGoogleSheets = async () => {
    window.location.href = '/authorize-google-sheets';
  };

  if(!canUseGoogleApi) return null;

  return (
    <div>
      <button onClick={authorizeGoogleSheets}>
        Authorize Google Sheets
      </button>
    </div>
  );
};

/**
 * A button component for making AI prompted queries.
 * @return {React.Component} The rendered button component.
 */
const MakeAIPromptedButton = () => {
  return (
    <div>
      <button onClick={() => {window.location.href = '/prompting';}}>
        Make AI Prompted
      </button>
    </div>
  );
};

/**
 * The main application component.
 * @return {React.Component} The rendered application.
 */
const App = () => {
  const [canUseGoogleApi, setCanUseGoogleApi] = React.useState(false);

  const [databases, setDatabases] = React.useState([]);
  const [currentDatabase, setCurrentDatabase] = React.useState('');
  const [creatingDatabase, setCreatingDatabase] = React.useState(false);

  const toggleCreatingDatabase = () => setCreatingDatabase(!creatingDatabase);

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
  const fetchCanUseGoogleApi = async () => {
    const data = await fetchApi('/google-has-credentials');
    if (data.success) {
      setCanUseGoogleApi(data.hasCredentials);
    }
  };

  React.useEffect(() => {
    fetchDatabases();
    fetchCanUseGoogleApi();
  }, []);

  if (databases.length === 0) {
    return <AddNewDatabase fetchDatabases={fetchDatabases} setCreatingDatabase={setCreatingDatabase}/>;
  }

  return (
    <div>
      
      <Toast/>
      <WaitForResponseUI/>
      <CreateDatabaseButton creatingDatabase={creatingDatabase} toggleCreatingDatabase={toggleCreatingDatabase}/>
      <div className='float-top-left'>
        <AuthorizeGoogleSheetsButton canUseGoogleApi={canUseGoogleApi}/>
        <MakeAIPromptedButton/>
      </div>
      <div className='margin-when-skinny'></div>
      {!creatingDatabase ? null : (
        <AddNewDatabase
          fetchDatabases={fetchDatabases}
          setCreatingDatabase={setCreatingDatabase}
        />
      )}
      <h1> Query Sheets </h1>
      <UploadTable
        currentDatabase={currentDatabase}
        setCurrentDatabase={setCurrentDatabase}
        databases={databases}
      />
      <Query
        currentDatabase={currentDatabase}
        canUseGoogleApi={canUseGoogleApi}
      />
    </div>
  );
};

// Render the application
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App/>);

