from sorm.orm import ORM
SETTINGS = {
            'type': 'SQLITE',
            'databaseURI': 'dev.sqlite',
            'isolation_level': 'DEFERRED'
        }  
db = ORM(SETTINGS)
