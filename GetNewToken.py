from dotenv import load_dotenv, set_key
from flask import Flask, render_template_string, request, redirect
from threading import Timer, Thread
import os, requests, webbrowser, time, subprocess, hashlib, base64, secrets, random, string


app = Flask(__name__)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Load or generate necessary environment variables
clientID = os.getenv('CLIENT_ID')
redirectUri = os.getenv('REDIRECT_URI')

# Generate a secure code verifier and code challenge
def generate_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').replace('=', '')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').replace('=', '')
    return code_verifier, code_challenge
    
    
def generate_and_store_state():
    state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
    set_key(dotenv_path, 'STATE_ID', state)
    return state

# Check if code_challenge and client_verifier exist, if not create them
clientVerifier = os.getenv('CLIENT_VERIFIER')
codeChallenge = os.getenv('CODE_CHALLENGE')

if not clientVerifier or not codeChallenge:
    clientVerifier, codeChallenge = generate_code_verifier_and_challenge()
    set_key(dotenv_path, "CLIENT_VERIFIER", clientVerifier)
    set_key(dotenv_path, "CODE_CHALLENGE", codeChallenge)
    
state = generate_and_store_state()

def open_browser():
    """Function to open the browser to the root URL of the Flask app."""
    webbrowser.open("http://127.0.0.1:3003/")

@app.route('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Etsy OAuth Authentication</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #ecf0f1;
            }
            .container {
                max-width: 600px;
                text-align: center;
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            header, section, footer {
                margin-bottom: 20px;
                text-align: center;
            }
            h1, h2 {
                color: #2c3e50;
            }
            p {
                color: #34495e;
            }
            .auth-button {
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-size: 16px;
            }
            .auth-button:hover {
                background-color: #2980b9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Welcome to Our Etsy App</h1>
                <p>This application uses Etsy's OAuth 2.0 authentication to access your shop data.</p>
            </header>
            <section>
                <h2>Authenticate Now</h2>
                <p>Click the button below to start the authentication process.</p>
                <a class="auth-button" href="https://www.etsy.com/oauth/connect?response_type=code&redirect_uri={{redirectUri}}&scope=listings_w%20email_r&client_id={{clientId}}&state={{state}}&code_challenge={{codeChallenge}}&code_challenge_method=S256">
                    Authenticate with Etsy
                </a>
            </section>
            <footer>
                <p>If you have any questions, please refer to the Etsy <a href="https://developer.etsy.com/documentation/essentials/authentication">Authentication Essentials</a> page.</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_content, clientId=clientID, redirectUri=redirectUri, state=state, codeChallenge=codeChallenge)



@app.route('/ping')
def ping():
    """Route to demonstrate an API call to a service."""
    headers = {'x-api-key': clientID}
    response = requests.get('https://api.etsy.com/v3/application/openapi-ping', headers=headers)
    if response.ok:
        return response.json()
    else:
        return "oops"

@app.route('/oauth/redirect')
def oauth_redirect():
    """Handle OAuth redirect and token exchange."""
    authCode = request.args.get('code')
    tokenUrl = 'https://api.etsy.com/v3/public/oauth/token'
    payload = {
        'grant_type': 'authorization_code',
        'client_id': clientID,
        'redirect_uri': redirectUri,
        'code': authCode,
        'code_verifier': clientVerifier,
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(tokenUrl, json=payload, headers=headers)
    if response.ok:
        tokenData = response.json()
        access_token = tokenData['access_token']
        
        # Update the .env file with the new access token
        set_key(dotenv_path, "ETSY_OAUTH_TOKEN", access_token)
        time.sleep(1)  # Add delay to ensure .env file is updated
        
        # Calculate and save the expiry time
        expires_in = tokenData.get('expires_in')  # Ensure you use get() for safety
        expiry_time = time.time() + expires_in
        set_key(dotenv_path, "ETSY_OAUTH_TOKEN_EXPIRY", str(expiry_time))
        time.sleep(1)  # Add delay to ensure .env file is updated
        
        return redirect(f"/welcome?access_token={access_token}")
    else:
        return "oops"

@app.route('/welcome')
def welcome():
    access_token = request.args.get('access_token')
    user_id = access_token.split('.')[0]
    headers = {
        'x-api-key': clientID,
        'Authorization': f'Bearer {access_token}',
    }
    url = f'https://api.etsy.com/v3/application/users/{user_id}'
    response = requests.get(url, headers=headers)
    if response.ok:
        userData = response.json()
        # Check if the upload script should be executed
        run_upload = os.getenv('RUN_SCRIPT_AFTER_AUTH', 'true').lower() == 'true'

        if run_upload:
            # Run the upload script in a separate thread
            thread = Thread(target=run_upload_script)
            thread.start()
        # Return response immediately while the script runs in the background
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Welcome to Our App</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    background-color: #f0f2f5;
                }
                .container {
                    max-width: 600px;
                    background-color: white;
                    border-radius: 8px;
                    padding: 30px;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    color: #2c3e50;
                }
                p {
                    color: #34495e;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome, {{ first_name }}!</h1>
                <p>Authentication was succesful. Enjoy!</p>
            </div>
        </body>
        </html>
        """, first_name=userData.get('first_name', 'Unknown'))
    else:
        print(f"Failed to fetch user data: {response.status_code} {response.text}")
        return "oops"

def run_upload_script():
    """Function to run a script specified in the .env file."""
    script_name = os.getenv('RETURN_TO_PROCESSES', 'ProcessUploadListings.py')  # Default to 'ProcessUploadListings.py' if not set
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), script_name)
    try:
        # Execute the specified script using Python
        subprocess.run(['python', script_path], check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError(
            f"Failed to run the script '{script_name}'. Please ensure that the script exists. "
            "To resolve this issue, please add or update the 'RETURN_TO_PROCESSES' variable "
            "in the .env file with the correct file name of the script to be run after authentication completes."
        )
    
if __name__ == '__main__':
    # Ensure the server starts first before opening the browser
    Timer(1, open_browser).start()
    app.run(port=3003, debug=False)
