from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.contrib import messages
from datetime import datetime, timedelta
from .models import TodoItem
import json
import fileinput
import glob
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(BASE_DIR, "storage")
metadata = os.path.join(BASE_DIR, "metadata")

keyTime = {}
keyExpire = {}

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
            
            name = path + "{}.txt".format(key)
            fh = open(name, 'w+')
            fh.write("{}".format(val))
            fh.close()

            keyTime[key] = time      
            if key in keyExpire:
                del keyExpire[key]   

            return render(request, 'set.html')

        elif params[0] == 'GET':
            key = params[1]
            keyExist = checkIfKeyExistInRAM(key, keyTime)

            if keyExist == False:
                mess = "key not found"
                return resourceNotFound(mess)
            
            name = path + '{}.txt'.format(key)
            val = open(name)
            mess = "".join(val.readlines())
            val.close()

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
                
            val = open(path + '{}.txt'.format(key))
            data = val.read()
            lst = data.split(" ")
            mess = len(lst)
            val.close()

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'RPUSH':
            key = params[1]
            values = params[2:]
            val = " ".join(values)
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                name = path + "{}.txt".format(key)
                fh = open(name, 'w+')                
                fh.write("{}".format(val))
                keyTime[key] = time
                fh.close()            
                mess = 'new list created'
            else:
                val = " " + val
                name = path + "{}.txt".format(key)
                fh = open(name, 'a+')
                fh.write("{}".format(val))
                keyTime[key] = time
                fh.close()

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

            name = path + "{}.txt".format(key)
            fh = open(name, 'r+')
            data = fh.readlines()
            fh.close()

            data = "".join(data)
            lst = data.split(" ")
            mess = lst.pop(0)
            f = open(name, 'w+')    
            keyTime[key] = time                          
            f.write(" ".join(lst))
            f.close()

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
            
            name = path + "{}.txt".format(key)
            fh = open(name, 'r+')
            data = fh.readlines()
            fh.close()

            data = "".join(data)
            lst = data.split(" ")
            mess = lst.pop()

            f = open(name, 'w+')                               
            f.write(" ".join(lst))
            keyTime[key] = time
            f.close()

            if len(lst) == 0:
                os.remove(name)      
                del keyTime[key]                          

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)
    
        elif params[0] == 'LRANGE':
            key = params[1]
            start, stop = int(params[2]), int(params[3])
            if start > stop or start < 0 or stop < 0:
                mess = "invalid parameters"
                return badRequest(mess)

            keyExist = checkIfKeyExistInRAM(key, keyTime)

            if keyExist == False:
                mess = "key not found"
                return resourceNotFound(mess)
            
            val = open(path + '{}.txt'.format(key))
            data = val.read()
            lst = data.split(" ")
            mess = lst[start:stop]
            mess = " ".join(mess)
            val.close()

            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)
    
        elif params[0] == 'SADD':
            key = params[1]
            values = params[2:]
            val = set(values)
            keyExist = checkIfKeyExistInRAM(key, keyTime)
            if keyExist == False:
                val = " ".join(list(val))
                name = path + "{}.txt".format(key)
                fh = open(name, 'w+')
                keyTime[key] = time
                fh.write("{}".format(val))
                fh.close()

                mess = 'new set created'
            else:                            
                name = path + "{}.txt".format(key)
                fh = open(name, 'r+')
                data = set(fh.read().split(" "))
                fh.close()
                
                newData = " ".join(list(data.union(val)))

                fh = open(name, 'w+')
                fh.write("{}".format(newData))
                keyTime[key] = time
                fh.close()

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
                        
            name = path + "{}.txt".format(key)
            fh = open(name, 'r+')
            mess = len(fh.read().split(" "))
            fh.close()

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
                                      
            name = path + "{}.txt".format(key)
            fh = open(name, 'r+')
            mess = set(fh.read().split(" "))
            fh.close()

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
                                   
            name = path + "{}.txt".format(key)
            fh = open(name, 'r+')
            data = set(fh.read().split(" "))
            fh.close()

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
                fh = open(name, 'w+')
                fh.write(" ".join(list(data)))
                fh.close()
                keyTime[key] = time

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
                        
            name = path + "{}.txt".format(firstKey)
            fh = open(name, 'r+')
            res = set(fh.read().split(" "))

            keys = params[2:]     
            for key in keys:
                keyExist = checkIfKeyExistInRAM(key, keyTime)
                if keyExist == False:
                    mess = '{} does not exist'.format(key)
                    return resourceNotFound(mess)                 
                        
                name = path + "{}.txt".format(key)
                fh = open(name, 'r+')
                data = set(fh.read().split(" "))
                fh.close()
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
            key = params[1]
            seconds = int(params[2])
            if int(seconds) != seconds or seconds <= 0:
                mess = 'invalid seconds'
                return badRequest(mess)

            keyExpire[key] = time + timedelta(seconds=seconds)

            context = {
                'message': seconds,
            }

            return render(request, 'get.html', context)

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
            keyTimePath = metadata + keyTimeName
            keyExpirePath = metadata + keyExpireName

            for key in keyTime:
                keyTime[key] = keyTime[key].strftime("%m %d %Y %H %M %S")

            for key in keyExpire:
                keyExpire[key] = keyExpire[key].strftime("%m %d %Y %H %M %S")

            keyTimeSave = open(keyTimePath, 'w+')
            keyTimeSave.write(json.dumps(keyTime))
            keyTimeSave.close()

            keyExpireSave = open(keyExpirePath, 'w+')
            keyExpireSave.write(json.dumps(keyExpire))
            keyExpireSave.close()

            mess = 'current state has been saved'
            context = {
                'message': mess,
            }

            return render(request, 'get.html', context)

        elif params[0] == 'RESTORE':
            keyTimePath = metadata + keyTimeName
            keyExpirePath = metadata + keyExpireName
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
        name = path + fileName
        os.remove(name)

def checkIfKeyExistInRAM(key, dic):
    return (key in dic)

def loadMetadata(fileName):
    fh = open(fileName, 'r+')
    expectDict = {}
    content = fh.read()
    fh.close()
    content = content.rstrip('}').lstrip('{')
    pairs = content.strip(" ").split(",")
    print(pairs)
    for pair in pairs:
        key, val = pair.split(":")
        key = key.strip(' ').strip('"')
        val = val.strip(' ').strip('"')
        val = datetime.strptime(val, '%m %d %Y %H %M %S')
        expectDict[key] = val
    
    return expectDict
    
def badRequest(errorMessage):
    return HttpResponseBadRequest('<h1>{}</h1>'.format(errorMessage))

def resourceNotFound(errorMessage):
    return HttpResponseNotFound('<h1>{}</h1>'.format(errorMessage))