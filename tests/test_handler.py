import unittest
import logging

from pymongo.connection import Connection

from mongolog.handlers import MongoHandler, MongoFormatter


class TestRootLoggerHandler(unittest.TestCase):
    """
    Test Handler attached to RootLogger
    """
    def setUp(self):
        """ Create an empty database that could be used for logging """
        self.db_name = '_mongolog_test'

        self.conn = Connection('localhost')
        self.conn.drop_database(self.db_name)

        self.db = self.conn[self.db_name]
        self.collection = self.db['log']

        self.log = logging.getLogger('')
        self.log.setLevel(logging.DEBUG)

        self.handler = MongoHandler(self.collection)
        self.log.addHandler(self.handler)
    

    def tearDown(self):
        """ Drop used database """
        self.conn.drop_database(self.db_name)
        self.log.removeHandler(self.handler)
        

    def testLogging(self):
        """ Simple logging example """
        self.log.debug('test')

        r = self.collection.find_one({'levelname':'DEBUG', 'msg':'test'})
        self.assertEquals(r['msg'], 'test')

    def testLoggingException(self):
        """ Logging example with exception """
        try:
            1/0
        except ZeroDivisionError:
            self.log.error('test zero division', exc_info=True)

        r = self.collection.find_one({'levelname':'ERROR', 'msg':'test zero division'})
        self.assertTrue(r['exc_info'].startswith('Traceback'))

    def testQueryableMessages(self):
        """ Logging example with dictionary """
        self.log.info({'address': '340 N 12th St', 'state': 'PA', 'country': 'US'})
        self.log.info({'address': '340 S 12th St', 'state': 'PA', 'country': 'US'})
        self.log.info({'address': '1234 Market St', 'state': 'PA', 'country': 'US'})
    
        cursor = self.collection.find({'levelname':'INFO', 'msg.address': '340 N 12th St'})
        self.assertEquals(cursor.count(), 1, "Expected query to return 1 "
            "message; it returned %d" % cursor.count())
        self.assertEquals(cursor[0]['msg']['address'], '340 N 12th St')

        cursor = self.collection.find({'levelname':'INFO', 'msg.state': 'PA'})

        self.assertEquals(cursor.count(), 3, "Didn't find all three documents")

    def testFormatter(self):
        formatString = '%(message)s from %(levelname)s'
        self.handler.setFormatter(MongoFormatter(formatString))

        self.log.info('%s within a message', 'message')
        document = self.collection.find_one()
        self.assertEquals(document['message'], 'message within a message from'
                                            ' INFO')
        

    def testNoneArgs(self):
        """ Logging example with "None" as logging args """
        self.log.info('This is a string %s with no args', None)
