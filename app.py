from flask import Flask, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Setup MongoDB connection
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['twitter_database']
collection = db['coronavirus_tweets']

@app.route('/tweets', methods=['GET'])
def get_tweets():
    # You may want to limit the number of tweets or implement pagination in a real-world scenario
    tweets = list(collection.find({}, {'_id': 0}).limit(100))  # Omit the MongoDB ID from the response
    return jsonify(tweets)

if __name__ == '__main__':
    app.run(debug=True)
