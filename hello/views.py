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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join("storage")) == False:
    os.mkdir('storage')

if os.path.isdir(os.path.join("metadata")) == False:
    os.mkdir('metadata')

path = os.path.join(BASE_DIR, "storage")
metadata = os.path.join(BASE_DIR, "metadata")

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
        params = content.split(" ")
        time = datetime.now()
        if params[0] == 'SET':
            key = params[1]
            val = params[2]
            
            name = os.path.join(path, "{}.txt".format(key))
            data = "{}".format(val)
            writeData(name, data, "w", key, time)

            if key in keyExpire:
                del keyExpire[key]   

            return render(request, 'set.html')

        elif params[0] == 'GET':
            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)

            if keyExist == False:
                mess = "key not found"
                return resourceNotFound(mess)
            
            name = os.path.join(path, "{}.txt".format(key))
            data = readData(name)
            mess = "".join(data)

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'LLEN':
            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = 'key not found'
                return resourceNotFound(mess)
                
            name = os.path.join(path, "{}.txt".format(key))
            data = readData(name)
            lst = data.split(" ")
            mess = len(lst)

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'RPUSH': # handle case empty list
            key = params[1]
            values = params[2:]
            val = " ".join(values)
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                name = os.path.join(path, "{}.txt".format(key))
                data = "{}".format(val)
                writeData(name, data, "w", key, time)
                         
                mess = 'new list created'
            else:
                val = " " + val
                name = os.path.join(path, "{}.txt".format(key))
                data = "{}".format(val)
                writeData(name, data, "a", key, time)       

                mess = "appended data to existed list"

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'LPOP':
            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = "key not found"
                return resourceNotFound(mess)

            name = os.path.join(path, "{}.txt".format(key))
            data = readData(name)
            data = "".join(data)
            lst = data.split(" ")
            mess = lst.pop(0)

            writeData(name, " ".join(lst), "w", key, time)

            if len(lst) == 0:
                os.remove(name)       
                del keyTime[key]                            

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'RPOP':
            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = "key not found"
                return resourceNotFound( mess)
            
            name = os.path.join(path, "{}.txt".format(key))
            data = readData(name)

            data = "".join(data)
            lst = data.split(" ")
            mess = lst.pop()

            writeData(name, " ".join(lst), "w", key, time)

            if len(lst) == 0:
                os.remove(name)      
                del keyTime[key]                          

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)
    
        elif params[0] == 'LRANGE':
            try:
                key = params[1]
                start, stop = int(params[2]), int(params[3])
                if start > stop or start < 0 or stop < 0:
                    mess = "invalid parameters"
                    return badRequest(mess)

                keyExist = checkIfKeyExistInRAM(key, keyTime)

                if keyExist == False:
                    mess = "key not found"
                    return resourceNotFound(mess)
            
                name = os.path.join(path, "{}.txt".format(key))
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
            val = set(values)
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                val = " ".join(list(val))

                name = os.path.join(path, "{}.txt".format(key))
                data = "{}".format(val)
                writeData(name, data, "w", key, time)

                mess = 'new set created'
            else:                            
                name = os.path.join(path, "{}.txt".format(key))
                data = set(readData(name).split(" "))
                
                newData = " ".join(list(data.union(val)))
                writeData(name, newData, "w", key, time)

                mess = "appended data to existed set"

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)
    
        elif params[0] == 'SCARD':
            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = 'key not found'
                return resourceNotFound(mess)
                        
            name = os.path.join(path, "{}.txt".format(key))
            data = readData(name)
            mess = len(data.split(" "))

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'SMEMBERS':
            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = 'key not found'
                return resourceNotFound(mess)
                                      
            name = os.path.join(path, "{}.txt".format(key))   
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

            name = os.path.join(path, "{}.txt".format(key))  
            data = set(readData(name).split(" "))        

            mess = "{} removed from set".format(removeEles)
            for ele in removeEles:
                if ele not in data:
                    mess = "{} does not exist".format(ele)
                    return resourceNotFound(mess)
                else:
                    data.remove(ele)

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

            name = os.path.join(path, "{}.txt".format(firstKey))     
            res = set(readData(name).split(" "))   

            keys = params[2:]     
            for key in keys:
                keyExist = checkIfKeyExistInRAM(key, keyTime)
                if keyExist == False:
                    mess = '{} does not exist'.format(key)
                    return resourceNotFound(mess)                 

                name = os.path.join(path, "{}.txt".format(key))    
                data = set(readData(name).split(" "))   
                res = res.intersection(data)

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
            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                mess = 'key not found'
                return resourceNotFound(mess)
            
            fileName = '{}.txt'.format(key)                  
            deleteDirContent(path, fileName=fileName)
            del keyTime[key]
            mess = '{} is deleted'.format(key)

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'FLUSHDB':
            deleteDirContent(path)
            keyTime = {}
            mess = 'all keys deleted'

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'EXPIRE':
            try:
                key = params[1]
                seconds = int(params[2])
                if int(seconds) != seconds or seconds <= 0:
                    mess = 'invalid seconds'
                    return badRequest(mess)

                keyExist = checkIfKeyExistInRAM(key, keyTime)
                if keyExist == False:
                    mess = 'key not found'
                    return resourceNotFound(mess)

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
            if checkIfKeyExistInRAM(key, keyExpire) == False:
                mess = 'this key does not have time out'
                return resourceNotFound(mess)

            timeout = keyExpire[key] 
            now = datetime.now()
            existWithin = (timeout - now).total_seconds()
            mess = existWithin

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'SAVE':
            keyTimePath = os.path.join(metadata, keyTimeName)
            keyExpirePath = os.path.join(metadata, keyExpireName)

            keyTimeToFile = copy.deepcopy(keyTime)
            keyExpireToFile = copy.deepcopy(keyExpire)

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
            keyTimePath = os.path.join(metadata, keyTimeName)
            keyExpirePath = os.path.join(metadata, keyExpireName)

            keyTime = loadMetadata(keyTimePath)
            keyExpire = loadMetadata(keyExpirePath)

            mess = 'restore from the last snapshot'
            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)
    else:
        return render(request, 'entry.html')

def deleteDirContent(path, fileName=""):
    if fileName == "":
        files = glob.glob(path + '*.txt')
        for f in files:
            os.remove(f)
        stringMeta = open(path + 'METADATA.txt', 'w')
        stringMeta.close()
    else:
        name = os.path.join(path, fileName)
        os.remove(name)

def checkIfKeyExistInRAM(key, dic):
    return (key in dic)

def loadMetadata(fileName):
    expectDict = {}
    content = readData(fileName)
    # fh = open(fileName, 'r+')    
    # content = fh.read()
    # fh.close()    
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

def writeData(pathToFile, data, mode, key, time, appendToRAM = True):
    availableModes = ["a", "w"]
    try:
        availableModes.index(mode)

        fh = open(pathToFile, mode)
        data = fh.write(data)
        keyTime[key] = time
        fh.close()
        if appendToRAM == False:
            del keyTime[key]

    except ValueError:
        logging.error("available actions are a and w")
