# Overview

These instructions describe how to create a client application that can read from an existing Google Sheet.
In summary (details further down below):

1. Create a Google API Project, and enable the Google Sheets API within it.
2. Create a Service Account + Service Key
3. Add the Service Account to the Google Sheet via the Share interface.
4. Configure the client library with the Service Account/Key, and the ID of the Google Sheet.
5. Use the client library to create a "service" object, which enables you to read/write the values in
   the Google Sheet. For instruction on how to use this service object, refer to the
   [Google Sheets API Guide](https://developers.google.com/sheets/api/guides/concepts).

# Pre-requisites

* Python3
* pip3 (usually installed via python3-pip RPM)
* The code in this directory

# Setup instructions

## Install python libraries

    $ pip-3 install --upgrade google-oauth google-api-python-client

## Setup Google APIs

### Setup the client application's Project

A client application's credentials are stored within a Project, so a Project must be
created/selected before credentials can be created for the client.

1. Visit the [Google API Console](https://console.developers.google.com/).
2. At the very top of the page is the current Project name (next to the Google APIs icon).
   Select the Project that will store credentials for your client application.

   To create a new Project, click the Project selector at the very top. It will open a window
   that lets you select the organization. Select "Redhat.com", and click "New Project". Name
   your Project so that people can easily know what it does and who made it,
   e.g. `jrussell - Account Sync Tool`.
3. Navigate to "[Top left hamburger] -> APIs & Services -> Dashboard"
   This dashboard lists all enabled APIs. If the API you want is not enabled, click
   "Enable APIs and Services" at the top. This will take you to a page where you can search Google APIs
   such as Google Docs, Google Sheets, Google Drive, etc. Click the desired API, and then
   click the "Enable" button.

### Setup the client application's credentials

A client application's request must be associated with a Service Key within a Service Account. This section
describes how to create both.

#### About Service Accounts and Service Keys

A **Service Account** is a container for robot credentials. It's created once (typically manually), and is
typically named after the robot that you want to give access to, e.g. "Account Synchronizer Bot", which
should ideally describe its purpose. The permissions granted by the administrators are associated with
a specific Service Account.

A Service Account can contain 0-many **Service Keys**, which are specific credentials used by the robot.
The Service Account typically contains just a single Service Key, but it may contain more if (say) the
administrator is creating new Service Keys so it can retire old ones.

From the client application's point-of-view, a Service Key is a JSON file that contains information such
as the Service Key's ID, the private key used to sign requests, and the Service Account identifier.

The [Google IAM Console](https://console.developers.google.com/iam-admin/serviceaccounts) allows the Project admin
to create and destroy Service Accounts and Service Keys.

#### Creating a Service Account

1. Visit the [Google IAM Console](https://console.developers.google.com/iam-admin/serviceaccounts) or navigate to it
   via "[Hamburger] -> IAM & admin -> Service Accounts", and ensure the desired Project is selected at the very top.
   (If an appropriate Project doesn't exist, see instructions for creating one above).
2. Click "Create Service Account". Name your service account after the robot and/or purpose it will be used for.
3. Under "Role", select "Project > Editor" (for read/write access) or "Project > Viewer" (for
   read-only access).
4. Click "Create".
5. Skip the step "Grant users access to this service account (optional)".

#### Adding a Service Key to a Service Account

1. Visit the [Google IAM Console](https://console.developers.google.com/iam-admin/serviceaccounts) and ensure the desired
   Project is selected at the very top.
2. Find the Service Account you want to add to (if it doesn't exist, see above for instructions to create one).
   On the far right of the row (you may have to scroll), click the 'vertical ellipsis' (3 dots) menu and select "Create Key".
3. In the dialog, select "Key type : JSON" and click "Create". This will generate a new Service Key under the Service
   Account, and download a JSON file encapsulating the information to your local machine.
4. Store this file in a safe place. It will be used later by the API.

**Note** If you lose the JSON file containing the Service Key, you cannot download it again. Instead, just create a new
Service Key and use the UI to delete the old one.

## Setup the Google Sheet

In this section, we grant the Service Account access to our Google Sheet.

1. Visit the Google Sheet.
2. Click the "Share" button at the top right.
3. In the dialog box in the "People" field, enter the Service Account ID. This can be found on the
   [Google IAM Console](https://console.developers.google.com/iam-admin/serviceaccounts) page in the
   "Service Account ID" column, and looks like an email address, e.g.
   `<service-account-name>@<project-name>.iam.gserviceaccount.com`
4. Uncheck "Notify people".
4. Click "Done", and ignore the warning about not notifying people, and the warning about the Service
   Account's address not being in the company's G-Suite domain.

# Configuring the API for use

After all the setup above, you should have:

1. A Service Key, downloaded as a JSON file called (say) `some-service-account.json`.
2. A Google Sheet that you want the client application to access. The Sheet should have
   the Service Account's 'email address' in its "Share" list.
3. The document ID of the Google Sheet. This can be found in the URL, e.g. if the URL is
   `https://docs.google.com/spreadsheets/d/1gtXz1XtjsMlkDolh6RfHykS6RoJqQ7loBqz4riCVPNA/edit`
   then the document ID is `1gtXz1XtjsMlkDolh6RfHykS6RoJqQ7loBqz4riCVPNA`

Use this to configure the API, as shown in the following sample code.

# Sample code

Note: This imports the api.py file in this directory, which encapsulates a lot of the setup.

    import googledocsapi.api
    SPREADSHEET_ID = '1gtXz1XtjsMlkDolh6RfHykS6RoJqQ7loBqz4riCVPNA'
    SERVICE_ACCOUNT_FILE = '/path/to/some-service-account.json'
    
    service = googledocsapi.api.getSheetsService(
        service_account_file=SERVICE_ACCOUNT_FILE,
        read_only=True,
    )

    # Call the Sheets API
    result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A2:E2',
        ).execute()
    values = result.get('values', [])
    if not values:
        print('No data found.')
    else:
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            print('{}, {}'.format(row[0], row[4]))
