from django.shortcuts import render, redirect
from django.http import HttpResponse
from requests import session
from spotipy import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from dotenv import load_dotenv
import os
from .models import *

load_dotenv()

# Spotify auth
spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

spotify_oauth = SpotifyOAuth(
    client_id=spotify_client_id,
    client_secret=spotify_client_secret,
    redirect_uri="http://127.0.0.1:8000/callback",
    scope="user-modify-playback-state user-read-playback-state"
)

spotify_client_auth = SpotifyClientCredentials(
    client_id=spotify_client_id,
    client_secret=spotify_client_secret
)

def spotify_get_auth_token(user):
    # Get the user's access token
    if user.spotify_token_expires < timezone.now().timestamp():
        # Refresh the token
        token_info = spotify_oauth.refresh_access_token(user.spotify_refresh_token)
        user.spotify_access_token = token_info["access_token"]
        user.spotify_refresh_token = token_info["refresh_token"]
        user.spotify_token_expires = token_info["expires_at"]
        user.save()
    spotify_token = user.spotify_access_token
    return spotify_token

def spotify_add_to_queue(track_id, jam):
    # Add a track to the Spotify queue
    # Get the jam object
    user = jam.user
    spotify_token = spotify_get_auth_token(user)
    sp = spotipy.Spotify(auth=spotify_token)
    # Add the track to the queue
    sp.add_to_queue(track_id)
    # Update the jam's queue
    jam.queue += f"{track_id},"

def spotify_get_playback(jam):
    # Get the current queue for the jam
    # Get the jam object
    user = jam.user
    spotify_token = spotify_get_auth_token(user)
    sp = spotipy.Spotify(auth=spotify_token)
    # Get the current queue
    current = sp.current_playback()
    queue = sp.queue()
    return queue, current

def spotify_get_current_playback(user):
    # Get the current playback for the user
    spotify_token = spotify_get_auth_token(user)
    sp = spotipy.Spotify(auth=spotify_token)
    current_playback = sp.current_playback()
    return current_playback

def landingpage(request):
    # Check if user is logged in
    if "user_id" in request.session:
        return redirect("/home")

    # If not logged in, redirect to Spotify login
    return render(request, 'landingpage.html')


def login_spotify(request):
    if "user_id" in request.session:
        return redirect("/home")
    # Redirect user to Spotify authorization URL
    auth_url = spotify_oauth.get_authorize_url()
    return redirect(auth_url)


def callback_spotify(request):
    # Handle callback from Spotify authorization
    code = request.GET.get("code")
    token_info = spotify_oauth.get_access_token(code)
    print(token_info)

    # Store access token in session
    request.session["spotify_token"] = token_info["access_token"]

    spotify_token = token_info["access_token"]
    sp = spotipy.Spotify(auth=spotify_token)
    user_info = sp.current_user()
    print(user_info)
    user_id = user_info["id"]
    user = User.objects.filter(spotify_id=user_id).first()
    if user is None:
        user = User(spotify_id=user_id)
    user.spotify_username = user_info["display_name"]
    user.spotify_access_token = token_info["access_token"]
    user.spotify_refresh_token = token_info["refresh_token"]
    user.spotify_token_expires = token_info["expires_at"]
    user.save()

    request.session["user_id"] = user_id
    request.session["spotify_username"] = user_info["display_name"]

    return redirect('/home')

def logout(request):
    # Clear the session
    if request.method == "POST":
        request.session.flush()
        return redirect('/')

def home(request):
    if "user_id" not in request.session:
        return redirect('/login')

    user_id = request.session["user_id"]
    user = User.objects.get(spotify_id=user_id)
    user_name = user.spotify_username

    jams = Jam.objects.filter(user=user)
    current = spotify_get_current_playback(user)
    active = jams.filter(is_active=True).first()
    if active is not None:
        current["jam_code"] = active.code
    else:
        active = False

    # Bereite die Künstlernamen vor
    if current and "item" in current:
        current["item"]["artists"] = ", ".join(artist["name"] for artist in current["item"]["artists"])

    return render(request, 'home.html', {
        'user_name': user_name,
        'jams': jams,
        'current': current,
        'active': active,
    })

def create_jam(request):
    # Check if user is logged in
    if "user_id" not in request.session:
        return redirect('/login')

    if request.method == "POST":
        # Get user info from session
        user_id = request.session["user_id"]
        user = User.objects.get(spotify_id=user_id)

        new_code = os.urandom(4).hex()
        # Check if the code is unique
        while Jam.objects.filter(code=new_code).exists():
            new_code = os.urandom(4).hex()

        # Set market to user's market!

        # Create a new jam
        new_jam = Jam(
            code = new_code,
            user=user,
        )
        new_jam.save()

        print("New jam created:", new_jam.name())

    return redirect('/jam/' + new_code)

def join_jam(request):
    if request.method == "POST":
        jam_code = request.POST.get("jam_code")
        jam = Jam.objects.filter(code=jam_code).first()
        if jam is None:
            return HttpResponse("Jam not found", status=404)
        return redirect('/jam/' + jam_code)
    return render(request, 'join_jam.html')

def jam_details(request, jam_code):
    # Überprüfen, ob der Jam existiert
    jam = Jam.objects.filter(code=jam_code).first()
    if jam is None:
        return HttpResponse("Jam not found", status=404)

    # Überprüfen, ob der Jam dem Benutzer gehört
    owner = False
    user_id = request.session.get("user_id")
    if user_id is not None:
        user = User.objects.get(spotify_id=user_id)
        if jam.user == user:
            owner = True

    # Hole die aktuellen Wiedergabedaten und die Warteschlange
    queue, current = spotify_get_playback(jam)

    # Verarbeite die Warteschlange
    formatted_queue = []
    for track in queue["queue"]:
        formatted_queue.append({
            "name": track["name"],
            "artists": ", ".join(artist["name"] for artist in track["artists"])
        })

    # Verarbeite die aktuellen Wiedergabedaten
    if current and "item" in current:
        current["item"]["artists"] = ", ".join(artist["name"] for artist in current["item"]["artists"])

    # Jam-Details
    jam_name = jam.name()
    jam_code = jam.code
    active = jam.is_active

    # Render die `jam_details.html`
    return render(request, 'jam_details.html', {
        'jam_name': jam_name,
        'jam_code': jam_code,
        'queue': formatted_queue,
        'current': current,
        'active': active,
        'owner': owner
    })

def search_song(request):
    if request.method == "POST":
        jam_code = request.POST.get("jam_code")
        # Check if jam is valid
        jam = Jam.objects.filter(code=jam_code).first()
        if jam is None:
            return HttpResponse("Jam not found", status=404)
        if not jam.is_active:
            return HttpResponse("Jam not found", status=400)
        query = request.POST.get("query")
        sp = spotipy.Spotify(auth_manager=spotify_client_auth)
        results = sp.search(q=query, type='track', limit=15, market=jam.market)
        tracks = results['tracks']['items']
        return render(request, 'search_results.html', {'tracks': tracks, 'jam_code': jam_code})
    return HttpResponse("Invalid request", status=400)

def add_song_to_queue(request):
    if request.method == "POST":
        jam_code = request.POST.get("jam_code")
        track_id = request.POST.get("track_id")
        # Check if jam is valid
        jam = Jam.objects.filter(code=jam_code).first()
        if jam is None:
            return HttpResponse("Jam not found", status=404)
        if not jam.is_active:
            return HttpResponse("Jam not found", status=400)
        # Add song to queue
        spotify_add_to_queue(track_id, jam)

        return redirect('/jam/' + jam_code)
    return HttpResponse("Invalid request", status=400)

def deactivate_jam(request):
    if request.method == "POST":
        jam_code = request.POST.get("jam_code")
        # Check if jam is valid
        jam = Jam.objects.filter(code=jam_code).first()
        if jam is None:
            return HttpResponse("Jam not found", status=404)
        # Check if user is the owner
        user_id = request.session.get("user_id")
        if user_id is None:
            return HttpResponse("User not found", status=404)
        user = User.objects.get(spotify_id=user_id)
        if jam.user != user:
            return HttpResponse("You are not the owner of this jam", status=403)
        # Deactivate the jam
        jam.is_active = False
        jam.save()
        return redirect('/home')
    return HttpResponse("Invalid request", status=400)