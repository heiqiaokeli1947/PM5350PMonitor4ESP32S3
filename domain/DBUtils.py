import btree

# First, we need to open a stream which holds a database
# This is usually a file, but can be in-memory database
# using uio.BytesIO, a raw flash partition, etc.
# Oftentimes, you want to create a database file if it doesn't
# exist and open if it exists. Idiom below takes care of this.
# DO NOT open database with "a+b" access mode.
db=None
dbFile=None

def openDB():
    global db
    global dbFile
    if dbFile == None:
        try:
            dbFile = open("mydb", "r+b")
        except OSError:
            dbFile = open("mydb", "w+b")

    if db == None:
        # Now open a database itself
        db = btree.open(dbFile)

def closeDB():
    global db
    global dbFile
    if db != None:
        db.close()
        db = None

    if dbFile != None:
        dbFile.close()
        dbFile = None


# The keys you add will be sorted internally in the database

def testDB(prefix,count):
    global db
    print("+++start insert. prefix:{},count:{}".format(prefix,count))
    openDB()

    for i in range(count):
        db[str(i)] = prefix+":"+str(i)

    closeDB()
    print("insert finish.")

    print("---start query.")
    openDB()
    for key in db:
        print("key:{},value:{}".format(key,db[key]))
    closeDB()
    print("test db finish.")

def save(kv):
    try:
        if None == kv or len(kv) == 0:
            return
        global db
        openDB()
        for k,v in kv.items():
            db[k] = v
    except OSError:
        print("save error")
    finally:
        closeDB()

def delete(keys):
    try:
        if None == keys or len(keys) == 0:
            return
        global db
        openDB()
        for key in keys:
            if key in db:
                del db[key]
    except OSError:
        print("delete error")
    finally:
        closeDB()

def get(k):
    try:
        global db
        openDB()
        res = None
        if k in db:
            res = db[k]
        
    except OSError:
        print("get error")
    finally:  
        closeDB()
    return res
def multiGet(keys):
    try:
        global db
        openDB()
        res = {}
        for k in keys:
            if k in db:
                res[k] = db[k]
            else:
                res[k] = None 
    except OSError:
        print("multiGet error")
    finally: 
        closeDB()
    return res






# # Assume that any changes are cached in memory unless
# # explicitly flushed (or database closed). Flush database
# # at the end of each "transaction".
# db.flush()

# # Prints b'two'
# print(db[b"2"])

# # Iterate over sorted keys in the database, starting from b"2"
# # until the end of the database, returning only values.
# # Mind that arguments passed to values() method are *key* values.
# # Prints:
# #   b'two'
# #   b'three'
# for word in db.values(b"2"):
#     print(word)

# del db[b"2"]

# # No longer true, prints False
# print(b"2" in db)

# # Prints:
# #  b"1"
# #  b"3"
# for key in db:
#     print(key)

# db.close()

# # Don't forget to close the underlying stream!
# dbFile.close()