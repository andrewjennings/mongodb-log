import logging
import getpass
from datetime import datetime
from socket import gethostname
from pymongo.connection import Connection
from bson import InvalidDocument


class MongoFormatter(logging.Formatter):
    def format(self, record):
        """Format the LogRecord as a dictionary so it's suitable for
        insertion into a Mongo record.
        If the msg given in the LogRecord is a dict, it will remain
        unformatted so that it's queryable in Mongo.  If the msg
        is a string, it'll be formatted into "message" and put
        into Mongo as a string attribute called message."""
        data = record.__dict__.copy()

        if type(record.msg) is dict:
            data['message'] = record.msg
        else:
            try: 
                data['message'] = record.msg % record.args
            except:
                data['message'] = '' 
                pass
            # If the formatter is given a string, format our
            # 'message' using it.
            data['message'] = self._fmt % data

        data.update(
            username=getpass.getuser(),
            time=datetime.now(),
            host=gethostname(),
        )


        if 'exc_info' in data and data['exc_info']:
            data['exc_info'] = self.formatException(data['exc_info'])
        return data
    

class MongoHandler(logging.Handler):
    """ Custom log handler

    Logs all messages to a mongo collection. This  handler is 
    designed to be used with the standard python logging mechanism.
    """

    @classmethod
    def to(cls, db, collection, host='localhost', port=None, level=logging.NOTSET):
        """ Create a handler for a given  """
        return cls(Connection(host, port)[db][collection], level)
        
    def __init__(self, collection, db='mongolog', host='localhost', port=None, level=logging.NOTSET):
        """ Init log handler and store the collection handle """
        logging.Handler.__init__(self, level)
        if (type(collection) == str):
            self.collection = Connection(host, port)[db][collection]
        else:
            self.collection = collection
        self.formatter = MongoFormatter()

    def emit(self,record):
        """ Store the record to the collection. Async insert """
        try:
            self.collection.save(self.format(record))
        except InvalidDocument, e:
            logging.error("Unable to save log record: %s", e.message ,exc_info=True)

