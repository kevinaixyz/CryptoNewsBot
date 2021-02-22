import os
from flask import Flask
import flask
import requests

from datetime import datetime, date
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from config import config

from googleapi import GoogleSheet, GoogleStorage
from newsapi.cointelegraph import Cointelegraph
from newsapi.cryptopanic import CryptoPanic
from newsapi.theblock import TheBlock
from newsapi import tools
from datetime import datetime, date

import ast

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid',
          'https://www.googleapis.com/auth/devstorage.read_write',
          'https://www.googleapis.com/auth/spreadsheets'
          ]
# ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/devstorage.read_write']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v2'

app = Flask(__name__)
app.secret_key = 'password'


@app.route('/', methods=['GET', 'POST'])
def index():
    return flask.render_template('index.html')


@app.route('/authorize')
def authorize():
    # Use the client_secret.json file to identify the application requesting
    # authorization. The client ID (from that file) and access scopes are required.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES)

    # Indicate where the API server will redirect the user after the user completes
    # the authorization flow. The redirect URI is required. The value must exactly
    # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
    # configured in the API Console. If this value doesn't match an authorized URI,
    # you will get a 'redirect_uri_mismatch' error.
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Generate URL for request to Google's OAuth 2.0 server.
    # Use kwargs to set optional request parameters.
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    flask.session['state'] = state
    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)
    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)
    return flask.redirect(flask.url_for('userinfo_request'))


@app.route('/userinfo')
def userinfo_request():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    userinfo = googleapiclient.discovery.build(
        'oauth2', 'v2', credentials=credentials)
    user = userinfo.userinfo().get().execute()

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    next_url = flask.url_for('index', user=user["name"])

    return flask.redirect(next_url)


@app.route('/search', methods=["POST"])
def search_news():
    if flask.request.method == 'POST':
        from_date = flask.request.form['from_date']
        to_date = flask.request.form['to_date']
        news_type = flask.request.form['news_type']
        if from_date and to_date:
            print(from_date)
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        if news_type == 'crypto_news':
            block_news = TheBlock.extract_theblock_news(from_date, to_date)
            cointelegraph_news = Cointelegraph.extract_cointelegraph_news(from_date, to_date)
            data = tools.aggregate([block_news, cointelegraph_news])
            return data

        context = {
            'from_date': from_date,
            'to_date': to_date,
            'news_type': news_type,
        }
    else:
        context = {}
    return {}


@app.route('/download', methods=["POST"])
def download_token_news():
    from_date = flask.request.form['from_date']
    to_date = flask.request.form['to_date']
    news_type = flask.request.form['news_type']
    if from_date and to_date:
        print(from_date)
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
    if news_type == 'token_news':
        tokens = ast.literal_eval(flask.request.form['tokens'])
        if tokens is None or len(tokens) == 0:
            tokens = config.tokens
        b = CryptoPanic.extract_cryptopanic_news(from_date, to_date, tokens)
        return flask.Response(b, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=test.csv"})


@app.route('/upload-to-google-sheet', methods=['POST'])
def upload2googlesheet():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    data = flask.request.form['data']
    response = GoogleSheet.insert_to_google_sheet(data, credentials)

    return response


@app.route('/upload', methods=['POST'])
def upload():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    data = flask.request.form['data']
    try:
        # insert to google sheet
        r1 = GoogleSheet.insert_to_google_sheet(data, credentials)
        # insert to google storage
        file_name = flask.request.form['filename']
        r2 = GoogleStorage.upload_google_storage(file_name, data, credentials)
        if r1 is not None and r2[0] == 200:
            return "Success"
        else:
            return [r1, r2]
    except Exception as e:
        print(e)
        return str(e)


@app.route('/crypto_news.csv')
def download_crypto_news():
    fd = flask.request.form["from_date"]
    td = flask.request.form["to_date"]
    news_df = CryptoPanic.extract_cryptopanic_news(fd, td)

    def generate():
        for i, row in news_df.iterrows():
            yield ",".join(row.tolist()) + "\n"

    return flask.Response(generate(), mimetype='text/csv')


@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return ('Credentials successfully revoked.')
    else:
        return ('An error occurred.')


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(config.ip, config.port, debug=True)
