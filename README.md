# projects
Type this line to terminal to start the server:
```
pip install Django

python manage.py runserver
```

## commands

# String
 ```
SET key value: set a string value, always overwriting what is  saved under key

GET key: get a string value at key already
 ```

# List: List is an ordered collection (duplicates allowed) of string values

```
LLEN key: return length of a list

RPUSH key value1 [value2...]: append 1 or more values to the list, create list if not exists, return length of list after operation

LPOP key: remove and return  the first item of the list

RPOP key: remove and return the last item of the list

LRANGE key start stop: return a range of element from the list (zero-based, inclusive of start and stop), start and stop are non-negative integers
```

# Set: Set is a unordered collection of unique string values (duplicates not allowed)

```
SADD key value1 [value2...]: add values to set stored at key

SCARD key: return the number of elements of the set stored at key

SMEMBERS key: return array of all members of set

SREM key value1 [value2...]: remove values from set

SINTER [key1] [key2] [key3] ...: set intersection among all set stored in specified keys. Return array of members of the result set
```

# Data Expiration

```
KEYS: List all available keys

DEL key: delete a key

FLUSHDB: clear all keys

EXPIRE key seconds: set a timeout on a key, seconds is a positive integer. Return the number of seconds if the timeout is set

TTL key: query the timeout of a key
```

# Snapshot

```
SAVE: save current state in a snapshot

RESTORE: restore from the last snapshot
```

