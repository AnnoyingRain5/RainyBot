import json
import os


class Database():
    '''
    Simple JSON database manager.
    JSON files will be stored in `db/`

    If a modification is considered not important enough to save to disk, simpily modify the `.db` property with the new `dict`.
    The modification will be saved to disk next time either `.save()` or `.update()` are called.

    To get the current state of the database without refreshing it from disk (recommended in most cases), use the `.db` property.

    ## Usage:

    ```py
    from DatabaseManager import Database
    db = Database("example")
    foo = ["bar": "foobar"]
    db.write(foo)
    print(db.db)
    ```
    Alternatively, the `.read()` method can be implimented, it just returns `.db`, for example: `print(db.read())`.
    The `.refresh()` method can also be implimented to refresh the json from disk, if it is known that it has been modified.
    '''

    def __init__(self, name: str):
        self.path = f"db/{name}.json"
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                f.write("{}")  # Init empty db
        with open(self.path) as f:
            self.db = json.load(f)

    def reload(self):
        '''
        Reload the database using the copy stored on disk. Useful if it is known that the JSON has been modified using an external program.
        Opposite of `.save()`.
        '''
        with open(self.path) as f:
            self.db = json.load(f)
        return self.db

    def save(self):
        '''
        Update the database stored on disk using the `.db` property stored in memory.
        Opposite of `.reload()`.
        '''
        with open(self.path, "w") as f:
            json.dump(self.db, f, indent=4)

    def write(self, newdb: dict):
        '''
        Overwrite the database stored on disk with the new `dict` supplied as an argument.
        '''
        self.db = newdb
        self.save()

    def update(self, records):
        '''
        Update the database using the records supplied as an argument
        '''
        self.db.update(records)
        self.save()
        # This line shouldn't be needed, but it crashes without it.
        self.reload()

    def read(self):
        '''
        Read the database from memory, returns the `.db` property.
        '''
        return self.db
