# ETSY-API-Auto-Authenticator

This is your replacement for the horrible 'Quick Start Tutorial' and because this one is completely automated with no knowledge of coding or struggling needed.

It doesn't make you jump through hoops as the tutorial has you do.

There are no folders to create.
There are no HBS files to make.
You don't have to copy and paste anything any longer.
To get this scripts working, you'll need to do a few things in the .env file first. This file is where important information is stored to help the scripts connect to your Etsy account. There are more direct instructions within the .env file to help you if you've never done this before.

Getting Your API Key:
CLIENT_ID: You'll need an API key, which is a unique identifier for your Etsy app. You can get one by going to the Etsy developer portal and creating a new app.
Finding Your Shop ID:
ETSY_SHOP_ID: Each Etsy shop has a unique identifier called the Shop ID. You can find yours by viewing the HTML source of your shop’s page or contacting Etsy support.
Deciding What to Do After Login:
RUN_SCRIPT_AFTER_AUTH: Decide if you want to run another script after logging in. Set this to 'true' to automate tasks like updating listings.

RETURN_TO_PROCESSES: Enter the name of the script file that will run after logging in, like ProcessUploadListings.py.
Callback URL:

REDIRECT_URI: Use http://localhost:3003/oauth/redirect and update the Callback URL in your Etsy app settings to match.

Here is what you don't have to do any longer: These fill in within the .env file automatically.
CODE_CHALLENGE=
CLIENT_VERIFIER=
ETSY_OAUTH_TOKEN=
ETSY_OAUTH_TOKEN_EXPIRY=
STATE_ID=

You will need to start the GetNewToken.py file with the StartAuthenticator.bat file, so you can see the output of what is happening.
That's it!!

At any point in code you make yourself for creating, updating or removing listings and your token expires you can have your code call GetNewToken.py and then have a return to the file it left by adding to the .env file where RETURN_TO_PROCESSES is located, so there is nothing to do manually to slow you down.
