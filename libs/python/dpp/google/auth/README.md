# Understanding Google APIs, bots, & Oauth2

(See also: [official Google Docs](https://developers.google.com/api-client-library/python/auth/installed-app).)

There are 3 common ways that Google APIs interact with bots (Service Accounts):

1) The bot authenticates as the bot itself. (It is not impersonating someone else.)
   E.g. A bot needs access to the Google Sheets API so it can read a spreadsheet. It's doing
   this as the Service Account associated with that bot.

2) A bot needs to impersonate an arbitrary user in a G-Suite domain. E.g. it is an app that
   can read anyone's Gmail inbox to (say) search and destroy spam, or can create Calendar
   events for many users.

3) A bot needs to impersonate a _specific_ user in a G-Suite domain. E.g. it is an app that
   needs to send an email "from" a specific person.

These situations are handled in different ways:

## Service Accounts (no impersonation)

This is the simplest case. Say the account needs to access a Google Sheet. Then you:
1) Create the Service Account and generate private credentials for it. (see the README.md
   in the directory above this for instructions)
2) Use the Share button on the Google Sheet to add the "username" of the Service Account,
   which is a long ID that looks like an email address.
3) Your bot loads in the private credentials, does API discovery to get a client for
   Google Sheets, and starts making API calls. (Again, see ../README.md for details)

## Service Accounts (impersonate arbitrary user)

1) Create a Service Account as above, but enable the "G Suite Domain-wide Delegation" option.
2) The G-Suite admin (typically someone in IT) _must_ approve "G Suite Domain-wide Delegation"
   for that Service Account. (If this step wasn't necessary, then anyone could create a
   Service Account that could do anything to anyone else's account!)

After these steps are done, then the program using the Service Account can impersonate any
user using the Oauth2 API. There's like a `for_user(<email address>)` method in the API
to generate credentials that impersonate a specific user.

(I haven't actually done this because getting consent for a Domain-wide Delegate account
is nigh-on impossible)

## Service Accounts (impersonate specific user)

This is a little more complex, but does _not_ require approval from the G-suite admin. The
workflow is:

1) Program obtains static `client_id` & `client_secret` from Google. (This is not really
   secret, they can be embedded in the source code).
2) On first run, program sees it has no credentials and generates a URL to request some.
   It presents this URL to the user, and prompts for a verification code.
3) The user pastes the URL into their browser and goes through the login process, and
   approves generating credentials for this app. (They'll be shown what permissions the
   program wants to get). At the end, they'll be shown a verification code, which
   they enter at the prompt.
5) The program contacts Google using the verification code, and exchanges it for
   an Access Token and a Refresh Token. The Access Token is ephemeral and expires after
   1hr. The Refresh Token is permanent (until revoked) and can be used in the future
   to obtain new Access Tokens.
6) The program persists the Refresh Token somewhere. (This means that when the program
   is run again, it can use the Refresh Token to immediately obtain a new Access Token
   without the user having to paste the URL and enter another code).
7) The program uses the Access Token to perform requests on the service that it was
    granted access for.

The OAuth2TokenWorkflow class in this directory takes care of most of the above.


### GCP Project Setup

To set up your GCP project to support this kind of app, follow these instructions:

1) Navigate to your GCP Project --> APIs & Services --> Credentials
2) [If your project has never set up a consent screen before, click "OAuth consent screen"
   and do the following:]
   Set the "Application Type" to "Internal".
   Set the "Application Name" to something descriptive.
   Click "Save".
3) Click "Create Credentials --> OAuth Client ID"
4) From the Application types, click "Other" and enter a descriptive name for your client ID,
   like "Auto-thingfier client"
5) The credentials will be created, and you'll be presented with a modal pop-up showing the
   secrets. Click "Ok" to dismiss it.
6) Now you'll see the credentials with the name you gave in (4) listed. Click the download
   button to the right of it to receive a JSON file with the client ID + secret. (Which
   isn't really secret, because you can embed it in your app).

### App setup

The OAuth2TokenWorkflow class takes the following in its initializer:
* Path to the credentials JSON file above. (This is not a secret, and could actually be
  committed alongside the code)
* Path to a file to store the Refresh Token. This file allows the app to immediately
  request a new Access Token if the Refresh Token is present.
* A list of the Google Scopes that the program will request.

### App usage

The app initializes the OAuth2TokenWorkflow class as above, then calls `get_credentials()`.

If this is the first time the app was run (i.e. there is no Refresh Token stored), then
this will cause the program to display the authorization URL, prompt the user to navigate
to it, and to receive the verification code. It will then obtain an Access Token and
Refresh Token, and return a `google.oauth2.credentials.Credentials` object.

If the app has been run before (i.e. there's already a Refresh Token) then the program
will automatically try to retrieve a new Access Token. The program can continue without
user intervention, and will return a `google.oauth2.credentials.Credentials` object as
above.

The Credentials object is then used to by the Python API discovery libraries to build
a service client.


    CLIENT_SECRET_FILE = '/path/to/credentials.json'
	REFRESH_TOKEN_FILE = '/path/to/refresh_token_storage_file.txt'
	SCOPES = ['https://www.googleapis.com/auth/gmail.send']

	def get_authenticated_service():
		oauth2_token_workflow = OAuth2TokenWorkflow(
			client_secret_file=CLIENT_SECRET_FILE,
			refresh_token_file=REFRESH_TOKEN_FILE,
			scopes=SCOPES,
		)

		# On first run, this might prompt the user to paste a URL into their
        # browser and enter a verification code.
		credentials = oauth2_token_workflow.get_credentials()

		return build('gmail', 'v1', credentials=credentials)

    service = get_authenticated_service()
    service.users().messages().send(
		userId="some_target@example.com",
		body=message,
	).execute()
