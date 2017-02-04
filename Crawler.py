import json
import extraction
import requests
import urllib
import urllib2
import re
from terminaltables import AsciiTable
import os
import time
from nltk.corpus import wordnet as wn
import random
import extraction
from PIL import Image
from PIL import ImageChops
import shutil

#List of structure:
#[[[[str, float, str(link)], goal], [[str, float, str(link)], goal]...]], [[[str, float, str], goal], [[str, float, str], goal]...]
RESULTS = []
ITINERARY = []

userinput = raw_input("[Reaver]# Please, enter a topic: ")
repeat = int(raw_input("[Reaver]# Please, enter the number of network hops: "))

print "[Reaver]# Routing to " + userinput + ", please, wait..."
goal = ''

for l in userinput:
    if l != ' ':
        goal = goal + l
    else:
        goal = goal + '_'

initgoal = goal
#############################
newgoal = ''

for l in goal:
    if l != '_' and l != '%':
        newgoal = newgoal + l
    else:
        newgoal = newgoal + ' '

#ITINERARY.append(newgoal)
#############################

def getlinks(url):
    '''getlinks(str) --> list of lists [[str, str(link], [str, str(link)]...]'''

    #connect to a URL
    website = urllib2.urlopen(url)

    #read html code
    html = website.read()

    #use re.findall to get all the links
    links = re.findall('"(/wiki/.*?)"', html)

    link_strings = []
    registry = []

    for item in links:
        link_word = item[6:]

        clean = ''
        for l in link_word:
            if l != '_' and l != '%':
                clean = clean + l
            else:
                clean = clean + ' '

        
        if ':' not in item \
           and 'Main_Page' not in item \
           and len(item) < 35 \
           and item[6:] != goal.strip('\n')\
           and clean not in ITINERARY:

            newstring = ''

            for l in item:
                if l != '_' and l != '%':
                    newstring = newstring + l
                else:
                    newstring = newstring + ' '

            if newstring[6:] not in registry:                      
                link_strings.append([newstring[6:], link_word])
                registry.append(newstring[6:])

##    for link in link_strings:
##        print link

    return link_strings


def evaluate(links, ref):
    '''evaluate(list of lists [[str, str(link)], [str, str(link)]...]) -->
    --> list of lists [[str, float, str (link)], [str, float, str(link)], ...]'''

    evaluated_links = []
    protoreference = wn.synsets(ref.split()[0])

    if protoreference != []:
        reference = wn.synsets(ref.split()[0])[0]
    else:
        i = 0
        while wn.synsets(ref.split()[0]) == []:
            ref = links[i][0]
            i += 1
        reference = wn.synsets(ref.split()[0])[0]
    

    for link in links:

        #Get values for every word in a string
        stringlist = link[0].split()

        score_dict = {}
        
        for word in stringlist:
            eva = wn.synsets(word)

            if eva != []:
                sim = wn.path_similarity(eva[0], reference)

                if sim != None:
                    score_dict[word] = sim
                else:
                    score_dict[word] = 0

            else:
                score_dict[word] = 0


        #Determine string sum
        score = 0
        for key in score_dict:
            score += score_dict[key]

        #Append to evaluated_links
        evaluated_links.append([link[0], score, link[1]])


    return evaluated_links
        

def sortlist(link_triples):
    '''sortlist(list of lists [[str, float, str(link)], [str, float, str(link)], ...]) -->
    --> [sorted list of lists[0:40], winner]'''
    
    sorted_list = sorted(link_triples, key=lambda links: float(-links[1]))

##    for element in sorted_list[0:40]:
##        print element

    if len(sorted_list) > 40:
        return [sorted_list[0:40], sorted_list[0]]
    else:
        return [sorted_list, sorted_list[0]]


def table(RESULTS):
    #Global header dump
    headers = []
    lines = [] #[line1A, line1B, line1C, line1D, line1E]
    
    #Iterating over page dumps to extract headers:
    for p in range(len(RESULTS)):
        page_header = 'PAGE ' + str(p + 1) + ': ' + ITINERARY[p]
        headers.append(page_header)

    #Ierating over page dumps to determine the longest dataset:
    length = 0
    for dataset in RESULTS:
        sorted_list = dataset[0]
        if len(sorted_list) > length:
            length = len(sorted_list)

    
    #Range iteration to extract lines:
    for i in range(length):
        line = []
        for page in RESULTS:
            if len(page[0]) > i + 1:
                fl = str(round(float(page[0][i][1]), 4))
                while len(fl) < 6:
                    fl += '0'
                
                line.append('[' + str(fl) + '] ' + page[0][i][0])
            else:
                line.append('')
        lines.append(line)

    formatted_data = []
    formatted_data.append(headers)
    formatted_data.extend(lines)

    table = AsciiTable(formatted_data)

    print table.table



## IMAGE REAPER

def reap(url):
    html = requests.get(url).text
    extracted = extraction.Extractor().extract(html, source_url=url)

    a = extracted.images
    file_num = 0
    
    for image_url in a:
        urllib.urlretrieve(image_url, ".../Desktop/dump/{0}.{1}".format(file_num, image_url[-3:]))
        file_num += 1

    sizelist = []
    filelist = os.listdir('.../Desktop/dump/')
    
    for f in filelist:
        size = os.path.getsize(".../Desktop/dump/" + f)
        sizelist.append(size)


    old = 0
    largest = 0

    for i in range(len(sizelist)):
        new = sizelist[i]
        if new > sizelist[largest]:
            largest = i
        old = new

    img = filelist[largest]
    image = Image.open(".../Desktop/dump/" + img)

    selectlist = os.listdir(".../Desktop/selected/")
    if img not in selectlist:
        shutil.copy(".../Desktop/dump/" + img, ".../Desktop/selected/" + img)
    else:
        shutil.copy(".../Desktop/dump/" + img, ".../Desktop/selected/" + img[:-4] + str(random.randrange(0, 50, 1)) + img[-3:])
    image.show()

    for f in filelist:
        os.remove(".../Desktop/dump/" + f)

def blend(goal):
    filedir = ".../Desktop/selected/"

    allfiles = os.listdir(filedir)

    startfile = Image.open(filedir + allfiles[0])    

    for i in range(1, len(allfiles)):
        add = Image.open(filedir + allfiles[i])
        if add.size[0] > startfile.size[0]:
            startfile = startfile.resize((add.size[0], startfile.size[1]))
        else:
            add = add.resize((startfile.size[0], add.size[1]))


        if add.size[1] > startfile.size[1]:
            startfile = startfile.resize((startfile.size[0], add.size[1]))
        else:
            add = add.resize((add.size[0], startfile.size[1]))

        startfile = ImageChops.darker(startfile.convert('RGBA'), add.convert('RGBA'))
    startfile.show()

    startfile.save("/home/hamilcar/Desktop/Blends/" + goal + ".jpg")


while repeat > 0:            
    #RUNTIME 1
    #############################
    newgoal = ''
    for l in goal:
        if l != '_' and l != '%':
            newgoal = newgoal + l
        else:
            newgoal = newgoal + ' '

    ITINERARY.append(newgoal)
    #############################
    reap("https://wikipedia.org/wiki/" + goal)
    dataset = sortlist(evaluate(getlinks("https://en.wikipedia.org/w/index.php?title=Special:WhatLinksHere/" + goal +"&limit=500"), newgoal))
    RESULTS.append(dataset)
    goal = dataset[1][2]

    os.system('clear')
    table(RESULTS)

    repeat -= 1


blend(initgoal)
