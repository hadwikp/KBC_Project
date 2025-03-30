import unittest
import json
from unittest.mock import MagicMock, patch
from app import app

# A dummy cursor to simulate MySQL responses
class DummyCursor:
    def execute(self, query, params=None):
        self.query = query
        self.params = params

    def fetchone(self):
        # Default dummy response; can be overridden in tests
        return {'status': 'waiting', 'correct_answer': 'Test Answer'}

    def fetchall(self):
        # Dummy response for admin_page listing waiting users
        return [{'uid': 'dummy_uid', 'status': 'waiting'}]

    def close(self):
        pass

class TestApp(unittest.TestCase):
    def setUp(self):
        # Enable testing mode and create a test client
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    @patch('app.mysql')
    def test_user_login_missing_fields(self, mock_mysql):
        # Test for missing fields (e.g., missing email)
        data = {'name': 'Test', 'dob': '2000-01-01', 'qualification': 'Bachelor'}
        response = self.client.post('/user_login', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing fields", response.data)

    @patch('app.mysql')
    def test_user_login_success(self, mock_mysql):
        # Set up a dummy cursor that will simulate the DB insert
        dummy_cursor = DummyCursor()
        mock_mysql.connection.cursor.return_value = dummy_cursor

        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'dob': '2000-01-01',
            'qualification': 'Bachelor'
        }
        # Clear session before testing login
        with self.client.session_transaction() as sess:
            sess.clear()
        response = self.client.post('/user_login', data=data, follow_redirects=False)
        # Expect a redirect to a waiting page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/waiting/', response.location)

    def test_admin_login_success(self):
        # Test valid admin credentials
        data = {'admin_id': 'admin', 'admin_password': 'password'}
        response = self.client.post('/admin_login', data=data, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin_page', response.location)

    def test_admin_login_failure(self):
        # Test invalid admin credentials
        data = {'admin_id': 'admin', 'admin_password': 'wrongpassword'}
        response = self.client.post('/admin_login', data=data)
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Invalid admin credentials", response.data)

    @patch('app.mysql')
    def test_check_game_status(self, mock_mysql):
        dummy_cursor = DummyCursor()
        # Simulate that the DB returns a status of 'accepted'
        dummy_cursor.fetchone = MagicMock(return_value={'status': 'accepted'})
        mock_mysql.connection.cursor.return_value = dummy_cursor

        # Set a dummy uid in session
        with self.client.session_transaction() as sess:
            sess['uid'] = 'dummy_uid'
        response = self.client.get('/check_game_status/dummy_uid')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get('status'), 'accepted')

    @patch('app.mysql')
    def test_submit_answer_correct(self, mock_mysql):
        dummy_cursor = DummyCursor()
        # Simulate the correct answer from the database
        dummy_cursor.fetchone = MagicMock(return_value={'correct_answer': 'Test Answer'})
        mock_mysql.connection.cursor.return_value = dummy_cursor

        payload = {
            'question_id': 1,
            'selected_answer': 'Test Answer'
        }
        response = self.client.post('/submit_answer', data=json.dumps(payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('correct'))

    @patch('app.mysql')
    def test_submit_answer_incorrect(self, mock_mysql):
        dummy_cursor = DummyCursor()
        # Simulate a DB response with a different correct answer
        dummy_cursor.fetchone = MagicMock(return_value={'correct_answer': 'Correct Answer'})
        mock_mysql.connection.cursor.return_value = dummy_cursor

        payload = {
            'question_id': 1,
            'selected_answer': 'Wrong Answer'
        }
        response = self.client.post('/submit_answer', data=json.dumps(payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data.get('correct'))

if __name__ == '__main__':
    unittest.main()
