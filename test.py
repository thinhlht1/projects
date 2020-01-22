import os
key = 'key'
data = 'randomString'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(BASE_DIR, "storage")
listPath = os.path.join(path, "list")
os.system('cd listPath')
os.system('echo {} > {}.txt'.format(data, key))
os.system('cd {}'.format(BASE_DIR))