from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.contrib import messages
from datetime import datetime, timedelta
from .models import TodoItem
import json
import fileinput
import glob
import os
import logging
import re
import copy
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

path = os.path.join(BASE_DIR, "storage")
metadata = os.path.join(BASE_DIR, "metadata")

stringPath = os.path.join(path, "string")
listPath = os.path.join(path, "list")
setPath = os.path.join(path, "set")

dataStructures = [stringPath, listPath, setPath]

if os.path.isdir(path) == False:
    os.mkdir(path)

if os.path.isdir(metadata) == False:
    os.mkdir(metadata)

if os.path.isdir(stringPath) == False:
    os.mkdir(stringPath)

if os.path.isdir(listPath) == False:
    os.mkdir(listPath)

if os.path.isdir(setPath) == False:
    os.mkdir(setPath)

keyTime = {}
keyExpire = {}

keyTimeName = "keyTime.txt"
keyExpireName = "keyExpire.txt"

validCommand = ['SET', 'GET', 'LLEN ', 'RPUSH ', 'LPOP ', 'RPOP ', 'LRANGE ', 'SADD', 
            'SCARD', 'SMEMBERS', 'SREM', 'SINTER', 'KEYS', 'DEL', 'FLUSHDB', 'EXPIRE', 
            'TTL', 'SAVE', 'RESTORE']
# Create your views here.

def myView(request):
    global keyTime
    global keyExpire
    if request.method == 'POST':
        content = request.POST['content']
        content = content.strip(" ")
        contentRemoveSpaces = " ".join(content.split())
        params = contentRemoveSpaces.split(" ")
        time = datetime.now()
        # SET 
        if params[0] == 'SET':
            try:
                key = params[1]
                startKey = content.find(key)
                endKey = startKey + len(key) # finding the end position of keyword
                val = content[endKey+1:] # consider the rest of the string as value
                if len(val) == 0: # avoid not passing any value
                    mess = 'value must not be empty'
                    return badRequest(mess)
            
                name = os.path.join(stringPath, "{}.txt".format(key)) # path to place for saving file
                data = "{}".format(val)
                writeData(name, data, "w", key, time) 

                return render(request, 'set.html')
            except Exception: # in case client do not pass any key
                mess = 'key must not be blank'
                return badRequest(mess)

        elif params[0] == 'GET':
            if len(params) != 2:
                mess = 'invalid input'
                return badRequest(mess)

            key = params[1]            
            keyExist = checkIfKeyExistInRAM(key, keyTime) # check if key exist

            if keyExist == False:
                mess = "key not found"
                return resourceNotFound(mess)
                        
            name = os.path.join(stringPath, "{}.txt".format(key)) # path to file, in this case string folder
            if checkFileExist(name) == False: # if value of key is set or list, this test fail
                mess = "value of {} is not a string".format(key)
                return resourceNotFound(mess)

            data = readData(name) # take data
            mess = data
            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'LLEN':
            if len(params) != 2:
                mess = 'invalid input'
                return badRequest(mess)

            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = 'key not found'
                return resourceNotFound(mess)
                
            name = os.path.join(listPath, "{}.txt".format(key))
            if checkFileExist(name) == False:
                mess = "value of {} is not a list".format(key)
                return resourceNotFound(mess)

            data = readData(name)
            lst = data.split(" ") # additional data transformation
            mess = len(lst) # additional data transformation

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'RPUSH': 
            key = params[1]
            values = params[2:]
            if len(values) == 0:
                mess = 'value must not be empty'
                return badRequest(mess)

            val = " ".join(values) # value from user 
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            name = os.path.join(listPath, "{}.txt".format(key))
            if keyExist == False: # if the key have not already existed, create new file
                data = "{}".format(val)
                writeData(name, data, "w", key, time)                         
                mess = 'new list created'
            else: # if the key have already existed
                if checkFileExist(name) == False: # check if is a list or not to avoid append data to set or string
                    mess = "value of {} is not a list".format(key)
                    return resourceNotFound(mess)

                val = " " + val
                data = "{}".format(val)
                writeData(name, data, "a", key, time)    # append to the file 
                mess = "appended data to existed list"

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'LPOP':
            if len(params) != 2:
                mess = 'invalid input'
                return badRequest(mess)

            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = "key not found"
                return resourceNotFound(mess)

            name = os.path.join(listPath, "{}.txt".format(key))
            if checkFileExist(name) == False:
                mess = "value of {} is not a list".format(key)
                return resourceNotFound(mess)

            # remove first element of list
            data = readData(name)
            data = "".join(data)
            lst = data.split(" ")
            mess = lst.pop(0)

            writeData(name, " ".join(lst), "w", key, time) # overwrite new list on old list

            if len(lst) == 0:
                os.remove(name)       
                del keyTime[key]                            

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'RPOP':            
            if len(params) != 2:
                mess = 'invalid input'
                return badRequest(mess)

            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = "key not found"
                return resourceNotFound( mess)
            
            name = os.path.join(listPath, "{}.txt".format(key))
            if checkFileExist(name) == False:
                mess = "value of {} is not a list".format(key)
                return resourceNotFound(mess)

            data = readData(name)
            data = "".join(data)
            lst = data.split(" ")
            mess = lst.pop()

            writeData(name, " ".join(lst), "w", key, time)

            # if client remove all element of list, delete file from folder, 
            # remove key from RAM
            if len(lst) == 0:
                os.remove(name)      
                del keyTime[key]                          

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)
    
        elif params[0] == 'LRANGE':
            try:
                if len(params) != 4:
                    mess = "invalid parameters"
                    return badRequest(mess)

                key = params[1]
                start, stop = int(params[2]), int(params[3])
                if start > stop or start < 0 or stop < 0:
                    mess = "invalid parameters"
                    return badRequest(mess)

                keyExist = checkIfKeyExistInRAM(key, keyTime)

                if keyExist == False:
                    mess = "key not found"
                    return resourceNotFound(mess)
            
                name = os.path.join(listPath, "{}.txt".format(key))
                if checkFileExist(name) == False:
                    mess = "value of {} is not a list".format(key)
                    return resourceNotFound(mess)

                data = readData(name)            
                lst = data.split(" ")
                if stop > len(lst):
                    mess = "index out of range"
                    return resourceNotFound(mess)

                mess = lst[start:stop]
                mess = " ".join(mess)

                context = {
                    'message': mess,
                }

                return render(request, 'get.html', context)
            except ValueError:
                mess = 'start and stop must be positive integers'
                return badRequest(mess)           
    
        elif params[0] == 'SADD':
            key = params[1]
            values = params[2:]
            if len(values) == 0:
                mess = 'value must not be empty'
                return badRequest(mess)

            val = set(values) # new data
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            name = os.path.join(setPath, "{}.txt".format(key))
            if keyExist == False:
                val = " ".join(list(val))                
                data = "{}".format(val)
                writeData(name, data, "w", key, time)
                mess = 'new set created'
            else: # if the set have already existed, if old data is 1 2 3, and new data is 2 3 4 then
                # value of the key is 1 2 3 4                           
                data = set(readData(name).split(" ")) # load existed data, convert those data into set             
                newData = " ".join(list(data.union(val))) # find union of old data with new data
                writeData(name, newData, "w", key, time) # overwrite result to existed file
                mess = "appended data to existed set"

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)
    
        elif params[0] == 'SCARD':            
            if len(params) != 2:
                mess = 'invalid input'
                return badRequest(mess)
            
            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = 'key not found'
                return resourceNotFound(mess)
                        
            name = os.path.join(setPath, "{}.txt".format(key))
            if checkFileExist(name) == False:
                mess = "value of {} is not a set".format(key)
                return resourceNotFound(mess)

            data = readData(name)
            mess = len(data.split(" "))

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'SMEMBERS':            
            if len(params) != 2:
                mess = 'invalid input'
                return badRequest(mess)

            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = 'key not found'
                return resourceNotFound(mess)
                                      
            name = os.path.join(setPath, "{}.txt".format(key)) 
            if checkFileExist(name) == False:
                mess = "value of {} is not a set".format(key)
                return resourceNotFound(mess)  

            data = readData(name)
            mess = data.split(" ")    

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'SREM':
            key = params[1]
            removeEles = params[2:]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = 'key not found'
                return resourceNotFound(mess)

            name = os.path.join(setPath, "{}.txt".format(key))  
            if checkFileExist(name) == False:
                mess = "value of {} is not a set".format(key)
                return resourceNotFound(mess)

            data = set(readData(name).split(" "))        

            mess = "{} removed from set".format(removeEles)
            for ele in removeEles: # remove element one by one
                # below could be run concurrently. In Golang, I could push data variable
                # to unbuffered channel and below code is executed by goroutines
                if ele not in data: # checking existence of ele ment could be run without lock
                    mess = "{} does not exist".format(ele)
                    return resourceNotFound(mess)
                else: # block data when removing ele
                    data.remove(ele) # use remove method of set 

            # if client remove all element of list, delete file from folder, 
            # remove key from RAM
            if len(data) == 0:
                os.remove(name)                    
                del keyTime[key]
            else:
                data = " ".join(list(data))
                writeData(name, data, "w", key, time)

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)    

        elif params[0] == 'SINTER':
            firstKey = params[1]
            firstKeyExist = checkIfKeyExistInRAM(firstKey, keyTime)
            if firstKeyExist == False:
                mess = '{} does not exist'.format(firstKey)
                return resourceNotFound(mess)                

            name = os.path.join(setPath, "{}.txt".format(firstKey))    
            if checkFileExist(name) == False:
                mess = "value of {} is not a set".format(key)
                return resourceNotFound(mess) 

            res = set(readData(name).split(" ")) # init result equal to value of first key   

            keys = params[2:]     
            for key in keys:
                # this block of code could be run concurrently by passing res to channel
                # and below code is executed by goroutines
                # checking existence of keys, loading data do not need to be locked
                # while finding intersection (res variable) is locked
                keyExist = checkIfKeyExistInRAM(key, keyTime) 
                if keyExist == False:
                    mess = '{} does not exist'.format(key)
                    return resourceNotFound(mess)            

                name = os.path.join(setPath, "{}.txt".format(key)) 
                if checkFileExist(name) == False:
                    mess = "value of {} is not a set".format(key)
                    return resourceNotFound(mess)    

                data = set(readData(name).split(" ")) # load data of next key and convert the data to set 
                res = res.intersection(data) # find intersection of the data with previous result

            if len(res) == 0:
                mess = "there is no intersection"
                context = {
                    'message': mess,
                }   

                return render(request, 'get.html', context)

            mess = " ".join(list(res))
            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'KEYS':
            if len(params) != 1:
                mess = 'invalid input'
                return badRequest(mess)

            res = []
            for key in keyTime:
                res.append(key)
            if len(res) == 0:
                mess = 'key not found'
                return resourceNotFound(mess)

            mess = " ".join(res)
            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)
        
        elif params[0] == 'DEL':            
            if len(params) != 2:
                mess = 'invalid input'
                return badRequest(mess)

            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = 'key not found'
                return resourceNotFound(mess)
            
            fileName = "{}.txt".format(key)
            for dataStructure in dataStructures:
                # this block of code could be run concurrently without locking                
                fileToBeRemoved = os.path.join(dataStructure, fileName) # check if key exist in each folder    
                if checkFileExist(fileToBeRemoved) == True:           
                    deleteDirContent(dataStructure, fileName)
                    break

            del keyTime[key]
            mess = '{} is deleted'.format(key)

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'FLUSHDB':
            if len(params) != 1:
                mess = 'invalid input'
                return badRequest(mess)

            for dataStructure in dataStructures: 
                deleteDirContent(dataStructure)

            keyTime = {}
            mess = 'all keys deleted'

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'EXPIRE':
            try:
                if len(params) != 3:
                    mess = 'invalid input'
                    return badRequest(mess)

                key = params[1]
                seconds = int(params[2])
                if int(seconds) != seconds or seconds <= 0:
                    mess = 'invalid seconds'
                    return badRequest(mess)

                keyExist = checkIfKeyExistInRAM(key, keyTime)
                if keyExist == False:
                    mess = 'key not found'
                    return resourceNotFound(mess)

                # save expire time of the key to keyExpire (by adding given seconds to 
                # the time of setting expire time)
                keyExpire[key] = time + timedelta(seconds=seconds)

                context = {
                    'message': seconds,
                }

                return render(request, 'get.html', context)
            except ValueError:
                mess = 'seconds must be integer'
                return badRequest(mess)  

        elif params[0] == 'TTL':
            key = params[1]
            if len(params) != 2:
                mess = 'key must not contain space'
                return badRequest(mess)
                
            if checkIfKeyExistInRAM(key, keyExpire) == False:
                mess = 'this key does not have time out'
                return resourceNotFound(mess)

            timeout = keyExpire[key] # get when key get expired
            now = datetime.now()
            existWithin = (timeout - now).total_seconds() # find difference between expire time and current
            # if the difference lesser than 0 this means key expired
            mess = existWithin
            if existWithin <= 0:
                mess = 'key expired'

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'SAVE':
            if len(params) != 1:
                mess = 'invalid input'
                return badRequest(mess)

            keyTimePath = os.path.join(metadata, keyTimeName)
            keyExpirePath = os.path.join(metadata, keyExpireName)

            # make deep copies of those hash tables so clients could sends SAVE 
            # method as many as they wants
            keyTimeToFile = copy.deepcopy(keyTime)
            keyExpireToFile = copy.deepcopy(keyExpire)

            # convert datetime object to string so system could save to
            # text file as json
            for key in keyTimeToFile:
                keyTimeToFile[key] = keyTimeToFile[key].strftime("%m %d %Y %H %M %S")

            for key in keyExpireToFile:
                keyExpireToFile[key] = keyExpireToFile[key].strftime("%m %d %Y %H %M %S")

            keyTimeData = json.dumps(keyTimeToFile)
            writeData(keyTimePath, keyTimeData, "w", 0, 0, appendToRAM=False)

            keyExpireData = json.dumps(keyExpireToFile)
            writeData(keyExpirePath, keyExpireData, "w", 0, 0, appendToRAM=False)

            mess = 'current state has been saved to {}'.format(keyTimePath)
            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'RESTORE':
            if len(params) != 1:
                mess = 'invalid input'
                return badRequest(mess)
                
            keyTimePath = os.path.join(metadata, keyTimeName)
            keyExpirePath = os.path.join(metadata, keyExpireName)

            keyTime = loadMetadata(keyTimePath)
            keyExpire = loadMetadata(keyExpirePath)

            mess = 'restore from the last snapshot'
            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)
        elif params[0] not in validCommand:
            mess = 'invalid method'
            return badRequest(mess)  
    else:
        return render(request, 'entry.html')

def checkFileExist(pathToFile):
    return os.path.isfile(pathToFile)

def deleteDirContent(path, fileName=""):
    if fileName == "":  # delete all files in given path   
        dir = os.path.join(path, "*")  
        files = glob.glob(dir)
        for file in files:
            os.remove(file)
    else: # delete specific file in given path
        name = os.path.join(path, fileName)
        os.remove(name)

def checkIfKeyExistInRAM(key, dic):
    return (key in dic)

# loadMetadata load json from text file and return hash table
def loadMetadata(fileName):
    expectDict = {}
    content = readData(fileName)
    content = content.rstrip('}').lstrip('{')    
    pairs = content.strip(" ").split(",")    
    for pair in pairs:
        if len(pair) == 0:
            continue

        key, val = pair.split(":")
        key = key.strip(' ').strip('"')
        val = val.strip(' ').strip('"')
        val = datetime.strptime(val, "%m %d %Y %H %M %S")
        expectDict[key] = val
    
    return expectDict
    
def badRequest(errorMessage):
    return HttpResponseBadRequest('<h1>{}</h1>'.format(errorMessage))

def resourceNotFound(errorMessage):
    return HttpResponseNotFound('<h1>{}</h1>'.format(errorMessage))

def readData(pathToFile):
    fh = open(pathToFile, 'r+')
    data = fh.read()
    fh.close()

    return data

# writeData has 2 options is appending to existed file or overwritting to existed file (creating new file)
def writeData(pathToFile, data, mode, key, time, appendToRAM = True):
    availableModes = ["a", "w"]
    try:
        availableModes.index(mode)

        fh = open(pathToFile, mode)
        data = fh.write(data)
        keyTime[key] = time
        fh.close()
        if appendToRAM == False: # if appendToRAM is False, system removes this key from keyTime
            del keyTime[key]

    except ValueError:
        logging.error("available actions are a and w")
