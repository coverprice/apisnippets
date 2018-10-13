# AWS account creation

This python script (and sub-modules) creates AWS IAM accounts. It is designed around a specific
use-case: to provision Red Hat employees (members of the OpenShift organization) with credentials
to an AWS account designated for development purposes.

This script works in 2 modes:
* `user` mode: Info about the user-to-create is provided on the command line.
* `spreadsheet` mode: Info about 1-many users-to-create is provided within a Google Sheet.

When running in `user` mode, the script only needs to talk to:
* Red Hat LDAP to verify the user's information
* AWS API to create the account

When running in `spreadsheet` mode, the script *also* talks to:
* Google Sheets API to retrieve the list of users and update their status.

## How it's supposed to work

### Summary
1) User signs up for account via Google Form
2) Dev Productivity team administrator periodically checks the form's spreadsheet
   and approves/denies requests.
3) Administrator runs the `create.py` script, which pulls data from the spreadsheet,
   provisions the account, and encrypts the new credentials.
4) Administrator emails the encrypted credentials to the user.

### Details

1) Users sign up for an account by filling in a Google Form: https://goo.gl/forms/9zrAZ0pERWSdrLrR2
    This form collects information about the requestor, such as their name, email address (provided
    automatically via Google SSO / Form integration), and their GPG key so that we can send them
    encrypted credentials.

2) Submitting the form inserts a new line in a [spreadsheet](https://docs.google.com/spreadsheets/d/1TxlsWyV970ct9EYaPrnSU5Ag7eTKw3Yfi2zfLsfqgxM/edit).
    Each row in the spreadsheet has a "Status" column that indicates where the account is in the
    approval workflow:

    * "In Review" (or blank): Awaiting admin approval
    * "Approved-but-not-created": Admin has approved the account, but it does not exist yet.
    * "Denied": Admin has denied the request.
    * "Account created": Admin has created the account and sent the user their credentials.

3) Administrators are expected to regularly check the spreadsheet (there's no notification) and examine
    each "In Review" request. (New submissions will have a blank status because Google Forms doesn't know
    that there's a default for that column).

    The administrator will set the status to "Approved-but-not-created" for users that need an account.

4) The administrator will run the `create.py` script in this directory, using `spreadsheet` mode. This
    will:
    * retrieve any users that need accounts from the spreadsheet.
    * verify that:
       * the user exists in LDAP
       * the user has supplied a valid GPG key
       * an AWS account for this user doesn't already exist.
    * create the AWS account
    * generate some credentials (username = Kerberos ID, generated password) and
      encrypt them with the user's GPG key.
    * output the encrypted credentials to a file (`<user_email_address>.gpg`)

5) The administrator gathers up the generated files and emails them to the users.
   (*TODO* - the script should email users directly)

## Setup

To use this script, you must have the following:

* Be on the internal Red Hat network OR be connected to the Red Hat network via the VPN. This is necessary to
  query LDAP.
* AWS API key credentials for the `openshift-dev` account, with sufficient permissions to create users (i.e. Admin).
  These credentials *must* be added to your local `~/.aws/credentials` file under the profile `[openshift-dev]`.
  (The script will attempt to automatically use the credentials under this profile name, there's no affordance
  to supply another profile name).
  To get an admin account and these API keys, see the instructions below.
* (In `spreadsheet` mode) Google Sheets API credentials for the script to read/write from the user sign-up
  spreadsheet. To obtain credentials, see the instructions below.
* Read/write access to the [spreadsheet](https://docs.google.com/spreadsheets/d/1TxlsWyV970ct9EYaPrnSU5Ag7eTKw3Yfi2zfLsfqgxM/edit).
  used by the Google Form. To obtain this, ask one of the DPP team to use the "Share" button to add access
  for your account.

### Editing the Google Form

The Google Form's definition is [here](https://docs.google.com/forms/d/1VUHzSYKK4tfGD5l2i1NgXZkDws4zD2fcZC1WRpwIjQc/edit).
You shouldn't need to edit it.

Be careful about editing the form! The columns used are hard-coded into the script, so adding/removing/moving fields
will break the script.

### Obtaining AWS API key credentials

First, obtain an `openshift-dev` IAM account. One of the DPP team members can provision that for you. If they
don't already have an IAM account with admin permissions, they can obtain root account credentials from
Bitwarden.

Once you have an IAM account, log in and navigate to `Services -> IAM -> Users -> (your name)`. Click
the "Security Credentials" tab and generate a new API key. Download the credentials, and run:

    $ aws configure --profile=openshift-dev

Answer the question prompts with the credentials info you just downloaded to set up a new profile
`openshift-dev`. For "Default region" use `us-west-1`, and "Default output format" use `text`.

### Obtaining Google Sheets service account credentials

The script performs read/writes using a GCP Service Account called "OpenShift DPP Google Docs Bot" which
lives in the "OpenShift DPP team" GCP project. The bot already has read/write permissions for the Google
Sheets API, and should already have explicit access to the form-data spreadsheet. (If it doesn't, see the
instructions below).

Each DPP team member should generate their own individual key under the OpenShift DPP Google Docs Bot
service account. To generate a key:

1) A DPP team member visits the [OpenShift DPP team](https://console.developers.google.com/iam-admin/iam?organizationId=54643501348&project=openshift-devproducti)
   project. That page should list all users, including service accounts.
2) Click the "Service Accounts" link in the left navbar.
3) Click the Service Account "OpenShift DPP Google Docs Bot" to see details.
4) Click the "+Edit" button. This will activate the "+Create Key" button under the "Keys" heading.
5) Choose the "JSON" format and click "Create". This will generate the key and automatically download
   it.
6) Place this key into `~/.secrets/gcp_service_accounts/openshift-devproductivity-bot.json`. (There is
   a command line option to specify a different location).

### Granting the Service Account permission to access the form spreadsheet

The OpenShift DPP Google Docs Bot service account needs Edit access on the spreadsheet itself. This
should already be set up, but if it isn't:

1) Open the page for the [OpenShift DPP Google Docs Bot](https://console.developers.google.com/iam-admin/serviceaccounts/details/108644291258280548223?organizationId=54643501348&project=openshift-devproducti)
   service account.
2) In the "Email" section, copy/paste the email address:

    openshift-dpp-google-docs-bot@openshift-devproducti.iam.gserviceaccount.com

3) Visit the [spreadsheet](https://docs.google.com/spreadsheets/d/1TxlsWyV970ct9EYaPrnSU5Ag7eTKw3Yfi2zfLsfqgxM/edit).
4) Click the "Share" button.
5) Add the email address from above and give it Edit access.
6) Click "Done".

## Usage

### Global options

* `--dry-run` - Perform all actions, but don't actually create the AWS account, update the spreadsheet, write to any files,
  or send any emails. The generated user credentials will have the correct username, but the password/API keys are
  static unusable dummies.
* `--debug` - Log debugging information to stderr.

### `spreadsheet` mode

    $ ./create.py [global options] spreadsheet [local options]

* `--gcp-credentials-file PATH` - path to the Google Sheets service account key file.

Example:

    $ ./create.py spreadsheet --gcp-credentials-file ~/.secrets/some_secret_file.json

### `user` mode

    $ ./create.py [global options] user USERNAME [--keyfile KEYFILE] [--outfile OUTFILE]

* `USERNAME` - *(Required)* either the user's Kerberos ID, or their `@redhat.com` email address.
* `-k KEYFILE`, `--keyfile KEYFILE` - (Optional) path to the user's GPG key. If not specified, the credentials
  are not encrypted.
* `-o OUTFILE`, `--outfile OUTFILE` - (Optional) path to output the (possibly encrypted) credentials. If not
  specified, defaults to stdout.

Example:

    $ ./create.py user jsmith@redhat.com -k /path/to/jsmith.public.key --outfile /path/to/jsmith.credentials.gpg
