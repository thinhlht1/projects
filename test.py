import os
key = 'key'
data = 'randomString'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(BASE_DIR, "storage")
listPath = os.path.join(path, "list")
pathToFile = os.path.join(listPath, "{}.txt".format(key))
os.system("echo {} >> {}".format(data, pathToFile))