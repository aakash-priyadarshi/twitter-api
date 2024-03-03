from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Setup MongoDB connection
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['twitter_database']
tweets_collection = db['coronavirus_tweets']
geocode_cache = db['geocode_cache']  # Collection for caching geocode results

def geocode_address(address):
    # Check cache first
    cached_result = geocode_cache.find_one({"address": address})
    if cached_result:
        return cached_result['latitude'], cached_result['longitude']
    
    # Not cached, call Google Geocoding API
    google_api_key = os.getenv('GOOGLE_API_KEY')
    response = requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={google_api_key}")
    geocode_data = response.json()
    
    if geocode_data['status'] == 'OK':
        geocode_result = geocode_data['results'][0]['geometry']['location']
        latitude = geocode_result['lat']
        longitude = geocode_result['lng']
        
        # Cache this geocode result
        geocode_cache.insert_one({"address": address, "latitude": latitude, "longitude": longitude})
        return latitude, longitude
    else:
        # Return None or a default location if geocoding fails
        return None, None

@app.route('/tweets', methods=['GET'])
def get_tweets():
    tweets = list(tweets_collection.find({}, {'_id': 0}).limit(100))
    enriched_tweets = []
    
    for tweet in tweets:
        user_location = tweet.get('user_location', '')
        if user_location:  # Skip geocoding if user_location is empty
            lat, lng = geocode_address(user_location)
            if lat is not None and lng is not None:
                tweet['latitude'] = lat
                tweet['longitude'] = lng
        enriched_tweets.append(tweet)
        
    return jsonify(enriched_tweets)

# New endpoint to fetch geocode cache results
@app.route('/geocode-cache', methods=['GET'])
def get_geocode_cache():
    cache_results = list(geocode_cache.find({}, {'_id': 0}))  # Omit the MongoDB ID from the response
    return jsonify(cache_results)

if __name__ == '__main__':
    app.run(debug=True)
