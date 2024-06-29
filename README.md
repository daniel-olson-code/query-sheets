# Query Sheet

### Intent

Automate .xlsx modification or creation in an AI friendly space.

I created this project for my portfolio. 
I'm hoping to showcase my ability to write python code 
by connecting to a database, using APIs, processing files, etc.

Currently the flask app is used only to support a quick and simple UI to a single user locally 
and does not follow good practices in running a full scale web server.

At the same time, the reason I came up with the idea 
is that I have worked in the digital marketing space within Amazon Ads.
Though I spent most my time with the APIs, I saw the need to automate a very wide variety of tasks, 
that all could probably be done easily with SQL queries 
outputting .xlsx files. 

Many companies that don't have the budget for 
developing an application using Amazons APIs
can benefit from this tool.

---

### WARNING
This is intended to be run locally and with one process at a time(for those thinking of gunicorn or something similar). 
This should not be run on a public server without being modified.

---

### Functionality:
* Upload xlsx/xlsm/xltx/xltm files into your Postgres Database
* Query and output result into a .xlsx file, Google Sheet or very simple html table

That's it! Pretty simple but extremely powerful with the rise of AI.
Since most people who don't understand Postgres can probably get ChatGPT, Claude, etc.
to do what they want. 
This would allow most people to automate their data worksheet processes. 
Or learn SQL, it's easier than you might think.

---

### Support

Consider leaving a star.

If you have benefited from this project and/or would like to see more features. Consider supporting

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/daniel.olson)

--- 

### Prerequisites
* python 3.10 or above 
  * [download](https://www.python.org/downloads/)
* Postgres database 
  * Google how to get one on your Operation System
  * Or buy one

---

### Setup Guide:

#### For Programmers
* `pip install -r requirements.txt` 
* `python3 main.py`

#### For Non-Programmers
* Download project
* Open terminal to project directory
* [Optional & HIGHLY RECOMMENDED] Set up python virtual environment
* [Help] Run the following commands inside the terminal with copy/paste
* install packages: `pip install -r requirements.txt` (for errors, see below)
* run server: `gunicorn --timeout 1200 -k gevent -b localhost:7777 main:app`
* open web browser to [http://localhost:7777](http://127.0.0.1:7777)
* Ctrl + C in terminal to stop server

_pip errors. Instead try:_ 
* `python3 -m pip install -r requirements.txt` 
* `python -m pip install -r requirements.txt`


---

### "How To" Once Installed

#### Fill in the correct information to connect to your Postgres Database

1. Input `id` (Give this connection a unique name)
2. Input `Host`
3. Input `User`
4. Input `Password`
5. Input `Database`
6. Input or leave as is `Port`


Don't have a database, user, etc.? 
For `Host` get your databases ip address. If running on the same computer put `localhost`.
For `User`, `Password`, `Database`. 
Connect to Postgres.
(For the following commands replace values `my_database` and `my_user` with useful names.)
Run `create database my_database;` 
then `create user my_user with password 'super-secret-password';`
and finally `ALTER DATABASE my_database OWNER TO my_user;`


![Image](screenshots/Create%20Database.png)

#### [Optional] Authorize Google Sheet API 

* If you have no button. See below for setting up credentials. 
* Once you have credentials with the correct file name, you should see this button after refreshing the page.

![Image](screenshots/Authorize%20Google.png)

#### Upload Table
1. Select the database
2. Fill the table name
3. Upload a xlsx/xlsm/xltx/xltm file
4. Select the sheet to upload
5. Click `Upload!`

![Image](screenshots/Upload%20Table.png)

#### Query Database and receive output

1. Write SQL query
2. Click `Save` or Ctrl / Cmd + S
3. [Optional] Save Locally
   1. Click `Save As`
   2. Provide a unique "file" name
   3. Click `Save As` again

![Image](screenshots/Query%20Section.png)

#### [Optional] Iterate over Query with Sub-Query values

**This section is for advanced users**

This will iterate through each row of the Sub-Query
replacing sub-strings of keys(column names) wrapped in double braces 
in the Query string with the table values
appending all the results together into a single table.

### Example:

table `test`:

<pre>
| a | b | c |
-------------
| 1 | 2 | 3 |
| 4 | 5 | 6 |
</pre>


query: `select '{{b}}' as foo;`

sub-query: `select * from test;`

**result table:**

<pre>
| foo |
-------
| '2' |
| '5' |
</pre>

![Image](screenshots/Advanced%20Sub-Query.png)

#### Lasty Run the Query

![Image](screenshots/Run%20Query.png)

---

### Google Sign In / Sheets API Credentials:

#### Requirements:

* A Google Cloud Account (**free**)
* Google API Credentials `json`
* Enabled Google Sheets API within same projects as credentials

_We currently don't have screen shots presenting this process._

1. you'll need a Google Cloud account. Don't worry it's **free**. Just go to [https://cloud.google.com](https://cloud.google.com/) and use your Google Account.
2. For the following step set `http://localhost:7777` and `http://127.0.0.1:7777` as origin urls then `http://localhost:7777/authorize-google-sheets-callback` and `http://127.0.0.1:7777/authorize-google-sheets-callback` as redirect urls. There should be inputs at the end of the next step to do this.
2. To get the credentials needed for  follow Google's guide [here](https://developers.google.com/workspace/guides/create-credentials), this [stack overflow question](https://stackoverflow.com/questions/58460476/where-to-find-credentials-json-for-google-api-client) may also be helpful.
3. Once you have the credentials in a `.json` format rename it to `google_credentials.json` and place it inside the project folder
4. Enable the _Google Sheets API_ within the same project [here](https://console.cloud.google.com/marketplace/product/google/sheets.googleapis.com)









<!-- 
   ![Image](https://fastly.picsum.photos/id/4/5000/3333.jpg?hmac=ghf06FdmgiD0-G4c9DdNM8RnBIN7BO0-ZGEw47khHP4)
-->
