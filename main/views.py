from django.shortcuts import render, redirect
from django.http import HttpResponse
from spotipy import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()

# Spotify auth
spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

spotify_oauth = SpotifyOAuth(
    client_id=spotify_client_id,
    client_secret=spotify_client_secret,
    redirect_uri="http://127.0.0.1:8000/callback",
    scope="user-modify-playback-state"
)

def start_auth_spotify(request):
    # Check if user is logged in
    if "spotify_token" in request.session:
        return HttpResponse(f"Logged in as {request.session['spotify_token']}")

    # If not logged in, redirect to Spotify login
    return redirect('/login')


def login_spotify(request):
    # Redirect user to Spotify authorization URL
    auth_url = spotify_oauth.get_authorize_url()
    return redirect(auth_url)


def callback_spotify(request):
    # Handle callback from Spotify authorization
    code = request.GET.get("code")
    token_info = spotify_oauth.get_access_token(code)

    # Store access token in session
    request.session["spotify_token"] = token_info["access_token"]

    return redirect('/')