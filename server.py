# ========================= Refer to requirements.txt =================================================================================================================

import requests
import simplejson as json
import urllib
import wordcloud
import csv
import flask
import time
import os
from wordcloud import WordCloud
from flask import Flask, render_template, request, url_for
from datetime import datetime
from requests_oauthlib import OAuth1

try:
  from SimpleHTTPServer import SimpleHTTPRequestHandler as Handler
  from SocketServer import TCPServer as Server
except ImportError:
  from http.server import SimpleHTTPRequestHandler as Handler
  from http.server import HTTPServer as Server



# ========================= Port & App initialization ================================================================================================================

#Use the PORT environment variable in BlueMix environment; default to 8000
PORT = int(os.getenv('PORT', 8000))

app = Flask(__name__)



# ========================= Function to handle requests to home page==================================================================================================

#Handle all requests to the home page via this function
@app.route('/')
def form():
    #Serve the index.html web page; Caching of CSS, data prevented by using the nocache parameter in HTML
    return render_template('index.html')



# ========================= Function to process requests & return results ============================================================================================

#Process the input and serve the results as http://twitter-sentiment-analyser.mybluemix.net/results
@app.route('/results', methods=['POST'])
def results():
    #Grab the user input, sent to the server via POST
    twitter_hashtag = request.form['q']

    #Handle variations in input: #Harvard vs Harvard
    if(twitter_hashtag[0:1] == "#"):
      twitter_hashtag=twitter_hashtag[1:len(twitter_hashtag)]
    print(twitter_hashtag)

    #Initialize counters & variables
    texty = ""
    ts = str(time.time())
    
    #Log the twitter hashtag we are going to make API calls on
    k = open("static/InputLog.txt", "r+")
    #Set file pointer at the end of the file
    k.seek(1, 2)
    #Log the timestamp and the twitter hashtag on a new line
    twit_log = "\n" + str(datetime.now()) + " | " + twitter_hashtag
    k.write(twit_log)
    k.close()



    # ========================= Initialize & Call Alchemy & Watson API ================================================================================================

    #Using Alchemy Emotion Analysis API service. Refer to http://www.alchemyapi.com/api/api-calls-emotion-analysis
    #Using Alchemy Keyword/Term Extraction API service. Refer to http://www.alchemyapi.com/api/keyword/urls.html
    #Using Twitter hashtag page as the source URL. Example, refer to https://twitter.com/hashtag/harvard for tweets related to #Harvard
    twitter_url="https://twitter.com/hashtag/" + twitter_hashtag
    alchemy_api_key=""                                                                                                               #Replace with your Alchemy API key
    alchemy_emotion_url="http://gateway-a.watsonplatform.net/calls/url/URLGetEmotion?apikey=" + alchemy_api_key + \
                     "&url=" + twitter_url + "&outputMode=json&showSourceText=0"
    alchemy_keyword_url="http://gateway-a.watsonplatform.net/calls/url/URLGetRankedKeywords?apikey=" + alchemy_api_key + \
                     "&url=" + twitter_url + "&outputMode=json&maxRetrieve=100&keywordExtractModstrict&showSourceText=0"

    alchemy_emotion_results=requests.post(alchemy_emotion_url)
    parsed_emotion_results = alchemy_emotion_results.json()

    alchemy_keyword_results=requests.post(alchemy_keyword_url)
    parsed_keyword_results = alchemy_keyword_results.json()

    #Extract the emotion scores from the Alchemy Emotion Analysis API results & normalize them to 100
    anger = round(float(parsed_emotion_results["docEmotions"]["anger"])*100, 2)
    fear = round(float(parsed_emotion_results["docEmotions"]["fear"])*100, 2)
    disgust = round(float(parsed_emotion_results["docEmotions"]["disgust"])*100, 2)
    sadness = round(float(parsed_emotion_results["docEmotions"]["sadness"])*100, 2)
    joy = round(float(parsed_emotion_results["docEmotions"]["joy"])*100, 2)



    # ========================= WordCloud Image Generator =============================================================================================================

    #Remove all URLs, by excluding all texts containing "."
    #Assign higher weightage to those words that have a higher relevance score, by repeating them
    #For example, if a word "Campus" has a relevance score of 0.5, we first normalize it to 100 (i.e. 50)
    #We then repeat the word "Campus" 50 times, to assign the appropriate weightage to this word
    for i in range(0,len(parsed_keyword_results["keywords"])):
      if "." not in parsed_keyword_results["keywords"][i]["text"]:
        for j in range(int(float(parsed_keyword_results["keywords"][i]["relevance"])*100)):
          texty = texty + " " + parsed_keyword_results["keywords"][i]["text"]

    #Assign black as the background color & save result to local directory
    #Image caching disabled via no-cache paramter in HTML
    wc = WordCloud(background_color="black", max_words=200000)
    wc.generate(texty)
    wc.to_file("static/images/wordcloud.png")



    #Send over the final.html file as the output
    #Pass the twitter hashtag & main scores for the emotional results as parameters
    #These will be used to update the web page dynamically
    return render_template('final.html', twit=twitter_hashtag, anger=anger, fear=fear, disgust=disgust, sadness=sadness, joy=joy, timey=ts)



# ========================= Main Function to fire up the server =======================================================================================================

if __name__ == '__main__':
  #Start up the application on the localhost (i.e. on the BlueMix environment)
  app.run(host='0.0.0.0', port=int(PORT))
