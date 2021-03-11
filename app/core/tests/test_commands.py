# This file is used to ensure that django service will run after the execution of our database service so that django won't face any issue while starting
from unittest.mock import patch

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase

class CommandTests(TestCase):

    def test_wait_for_db_ready(self):
        """Test waiting for db when db is available"""

        # Here __getitem__ is used to retrieve the default connection object in django which is available in ConnectionHandlers
        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            # This means that whenever __getitem__ is called before performing whatever behavior __getitem__ in django it will override and just returns True
            # That means we can ensure that __getitem__ is called successfully
            gi.return_value = True
            call_command('wait_for_db')
            self.assertEqual(gi.call_count, 1)
        
    @patch('time.sleep', return_value=True)
    # wait for db command is available at core/management/commands
    def test_wait_for_db(self, ts):
        """Test waiting for db"""

        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            # It means first 5 times it raise an OperationalError and at 6th time it returns True
            gi.side_effect = [OperationalError]*5 + [True]
            call_command('wait_for_db')
            self.assertEqual(gi.call_count, 6)