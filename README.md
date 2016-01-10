# TickTock
TickTock is an app that counts down to the upcoming events that you care 
about.  The Endpoints API lives here.

## Installing Requirements
Run `pip install -t lib -r requirements.txt` from the project root to install
all required libraries.

## Running
Run `dev_appserver.py . --log_level debug --appidentity_email_address 
calendar-service-account@dhsdev-ticktock.iam.gserviceaccount.com
--appidentity_private_key_path service-account-secret-key.pem`.  You will need
a secret key file, but it's a secret, so keep it secret if I send one to 
you.  Secrecy is paramount!

## Setting Up a .pem File.
If you do not have access to the club email account, just ask Zander for a 
.pem file on slack.  Rename it to `service-account-secret-key.pem` and put it
in the project root.  It will be .gitignored, because it must be kept secret.
Never upload it to github.

### Getting a .p12 File
Go to <https://console.developers.google.com/permissions/serviceaccounts>, 
sign in as <drakedevelopersclub@gmail.com>, and choose the TickTock project. 
Find the service account titled "Calendar Service Account".  Click the three 
vertical dots on the right side of the entry, then click "Create key."  Choose 
P12, and download the file to the project root.

### Making a .pem File From a .p12 File
Run `openssl pkcs12 -in path/to/p12/file.p12 -out 
service-account-secret-key.pem -nodes` from project root, replacing 
`path/to/p12/file.p12` with the correct path.  Note, *.p12 files are 
.gitignored, so it is okay to put them in the project root, to keep 
everything together.
