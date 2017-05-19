#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 19 15:42:54 2017

@author: stephenlizcano
"""


from boto3 import Session
from readability import Document
import requests, re
from botocore.exceptions import BotoCoreError, ClientError
from bs4 import BeautifulSoup 
from contextlib import closing
import os
import sys
import subprocess
from tempfile import gettempdir


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
    return [parsed[i:i+n] for i in range(0, len(parsed), n)]
        
def speech_generator(text, index):
    
    index = str(index)
    try:
        # Request speech synthesis
        response = polly.synthesize_speech(Text=text, OutputFormat="mp3",
                                            VoiceId="Joanna")
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
            output =  os.getcwd() + '/audio/' + "speech" + index + ".mp3"
    
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
    if sys.platform == "win32":
        os.startfile(output)
    else:
        # the following works on Mac and Linux. (Darwin = mac, xdg-open = linux).
        opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.call([opener, output])


# Create a client using the credentials and region defined in the [adminuser]
# section of the AWS credentials file (~/.aws/credentials).
session = Session(profile_name="default")
polly = session.client("polly")

procd_text = news_parser('http://www.newyorker.com/magazine/2013/08/26/whats-wrong-with-me')

print(procd_text)
for line_index, line in enumerate(procd_text):
    speech_generator(line, line_index)
