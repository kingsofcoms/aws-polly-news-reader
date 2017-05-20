#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 19 15:42:54 2017

@author: stephenlizcano
"""


from boto3 import Session
from readability import Document
import requests, re, sys, time, os
from botocore.exceptions import BotoCoreError, ClientError
from bs4 import BeautifulSoup 
from contextlib import closing
import subprocess
from tempfile import gettempdir
from os.path import expanduser
from glob import *
from pydub import *



def news_parser(url):
    #Takes a url string, and returns a list of strings less than 1500 chars
    #to use for AWS polly
    #We are using readability.py to handle html backend
    response = requests.get(url)
    doc = Document(response.text)
    article_text = doc.summary()
    
    
    #Now we use a regex to clean the tags, and remove whitespace
    parsed = re.sub(r'<.*?>', " ", article_text)

    parsed = ' '.join(parsed.split())
    
    #now split strength by 1450 char length (max in AWS is 1500)
    n = 1450
    return [parsed[i:i+n] for i in range(0, len(parsed), n)], doc.title()
        
def speech_generator(text, index):
    
    index = str(index)
    #set the home directory below
    home = expanduser("~")
    try:
        # Request speech synthesis
        response = polly.synthesize_speech(Text=text, OutputFormat="mp3",
                                            VoiceId="Salli")
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)
        sys.exit(-1)
    
    # Access the audio stream from the response
    if "AudioStream" in response:
        # Note: Closing the stream is important as the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            output =  home + '/audio/incomplete/' + index + ".mp3"
            
            try:
                # Open a file for writing the output as a binary stream
                with open(output, "wb") as file:
                    file.write(stream.read())
            except IOError as error:
                # Could not write to file, exit gracefully
                print(error)
                sys.exit(-1)
    
    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")
        sys.exit(-1)
    
    # Play the audio using the platform's default player
    #if sys.platform == "win32":
    #    os.startfile(output)
    #else:
    #    # the following works on Mac and Linux. (Darwin = mac, xdg-open = linux).
    #    opener = "open" if sys.platform == "darwin" else "xdg-open"
    #subprocess.call([opener, output])


# Create a client using the credentials and region defined in the [adminuser]
# section of the AWS credentials file (~/.aws/credentials).
session = Session(profile_name="default")
polly = session.client("polly")

#This receives the URL, and sends it to the news parser
url = input("Please paste the url for processing:")
procd_text, title = news_parser(url)


#Pause to make sure that the information is read correctly
print(procd_text)
decision = input("Continue? [y/n]")
if decision == 'n':
	print('Goodbye')
	sys.exit()

#Parse lines, and generate speech
print("Generating speech from Polly...")
for line_index, line in enumerate(procd_text):
    speech_generator(line, line_index)

#Load temp files, then combine using ffmpeg
playlisst_songs = sorted(glob(expanduser("~")+'/audio/incomplete/*.mp3'), key=os.path.getmtime)
newlist = []
for el in playlisst_songs:
    newlist.append(AudioSegment.from_mp3(el))
    
#Generate a blank audio file, and concatenate the pieces of audio, and export
combined = AudioSegment.empty() 
for song in newlist:
    combined += song

print('Combining files, and removing trash...')
combined.export(expanduser("~")+"/audio/"+ title + ".mp3", bitrate='160k',format="mp3")

#Erase the temps
for el in playlisst_songs:
	os.remove(el)

print('Done!')

