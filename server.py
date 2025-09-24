from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
from requests_oauthlib import OAuth2Session
import os

app = Flask(__name__)
app.secret_key = b'F\xf5\xe5\xc0\xbe\tg\x7f\xac\x89\x87e\xc24\xe8m\x1c\xd9\xda\x96G,\x90i'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
authorization_base_url = "https://oauth.onshape.com/oauth/authorize"
token_url = "https://oauth.onshape.com/oauth/token"
redirect_url = "https://better-part-manager.onrender.com/token"

@app.route('/')
def home():
    onshape = OAuth2Session(client_id, redirect_uri=redirect_url)
    auth_url, state = onshape.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    return redirect(auth_url)

@app.route('/token', methods=["GET"])
def token():
    onshape = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri=redirect_url)
    token = onshape.fetch_token(token_url, client_secret=client_secret, authorization_response=request.url)
    session['oauth_token'] = token
    return redirect(url_for('.documents'))

@app.route('/documents', methods=["GET"])
def documents():
    extra = {
        'client_id': client_id,
        'client_secret': client_secret,
    }
    onshape = OAuth2Session(client_id, token=session['oauth_token'], redirect_uri=redirect_url)
    session['oauth_token'] = onshape.refresh_token(token_url, **extra)
    return jsonify(onshape.get('https://cad.onshape.com/api/v6/documents?q=Untitled&ownerType=1&sortColumn=createdAt&sortOrder=desc&offset=0&limit=20').json())

if __name__ == "__main__":
    app.run()