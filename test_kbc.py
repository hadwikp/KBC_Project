import unittest
import json
from unittest.mock import patch, MagicMock, mock_open

with patch('mysql.connector.connect', return_value=MagicMock()) as mock_connect, \
     patch('builtins.open', mock_open(read_data='{"results": []}')):
    import questions

from app import app, accepted_uid

# Tests for the Flask app endpoints
class KbcAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    @patch('app.mysql')
    def test_user_login_success(self, mock_mysql):
        mock_cursor = MagicMock()
        mock_mysql.connection.cursor.return_value = mock_cursor

        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'dob': '2000-01-01',
            'qualification': 'Bachelor'
        }
        response = self.client.post('/user_login', data=form_data, follow_redirects=False)
        self.assertEqual(response.status_code, 302)  
        self.assertIn('waiting', response.headers['Location'])
        mock_cursor.execute.assert_called()

    def test_user_login_missing_fields(self):
        # All fields missing should return a 400 error
        response = self.client.post('/user_login', data={})
        self.assertEqual(response.status_code, 400)

    def test_admin_login_success(self):
        response = self.client.post('/admin_login', data={
            'admin_id': 'admin',
            'admin_password': 'password'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('admin_page', response.headers['Location'])

    def test_admin_login_failure(self):
        response = self.client.post('/admin_login', data={
            'admin_id': 'wrong',
            'admin_password': 'wrong'
        })
        self.assertEqual(response.status_code, 401)

    def test_waiting(self):
        uid = 'testuid'
        response = self.client.get(f'/waiting/{uid}')
        self.assertEqual(response.status_code, 200)

    @patch('app.mysql')
    def test_admin_page(self, mock_mysql):
        # Set session admin flag
        with self.client.session_transaction() as sess:
            sess['admin'] = True

        # Simulate a query that returns a waiting user
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'uid': 'user1', 'status': 'waiting'}]
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.get('/admin_page')
        self.assertEqual(response.status_code, 200)

    def test_admin_page_unauthorized(self):
        response = self.client.get('/admin_page', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.headers['Location'])

    @patch('app.mysql')
    def test_select_user_success(self, mock_mysql):
        with self.client.session_transaction() as sess:
            sess['admin'] = True
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'uid': 'testuid'}
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.post('/select_user', data={'selected_uid': 'testuid'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        from app import accepted_uid as global_accepted_uid
        self.assertEqual(global_accepted_uid, 'testuid')

    def test_select_user_unauthorized(self):
        # Without admin session, the /select_user endpoint should return Unauthorized.
        response = self.client.post('/select_user', data={'selected_uid': 'testuid'})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Unauthorized", response.get_data(as_text=True))

    @patch('app.mysql')
    def test_select_user_no_selected_uid(self, mock_mysql):
        with self.client.session_transaction() as sess:
            sess['admin'] = True

        response = self.client.post('/select_user', data={}, follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("No user selected", response.get_data(as_text=True))

    @patch('app.mysql')
    def test_select_user_not_found(self, mock_mysql):
        # Ensure admin session is set for select_user
        with self.client.session_transaction() as sess:
            sess['admin'] = True

        # Simulate not finding the user in the database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.post('/select_user', data={'selected_uid': 'nonexistent'}, follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("User not found", response.get_data(as_text=True))

    @patch('app.mysql')
    def test_check_game_status_found(self, mock_mysql):
        # Simulate a user with status 'accepted'
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'status': 'accepted'}
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.get('/check_game_status/testuid')
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'accepted')

    @patch('app.mysql')
    def test_check_game_status_not_found(self, mock_mysql):
        # Simulate no record found; should return 'waiting'
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.get('/check_game_status/testuid')
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'waiting')

    @patch('app.mysql')
    def test_game_accepted(self, mock_mysql):
        # Simulate user with status 'accepted'
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'status': 'accepted'}
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.get('/game/testuid')
        self.assertEqual(response.status_code, 200)

    @patch('app.mysql')
    def test_game_not_accepted(self, mock_mysql):
        # Simulate user not accepted; should redirect to not_selected
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'status': 'waiting'}
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.get('/game/testuid', follow_redirects=True)
        self.assertEqual(response.request.path, '/not_selected')

    def test_not_selected(self):
        response = self.client.get('/not_selected')
        self.assertEqual(response.status_code, 200)

    @patch('app.mysql')
    def test_get_questions_accepted(self, mock_mysql):
        # Simulate accepted user and question queries for each difficulty
        mock_cursor = MagicMock()
        # For the status check, return accepted.
        mock_cursor.fetchone.side_effect = [{'status': 'accepted'}]
        questions_list = [{
            'id': 1,
            'question': 'Question',
            'difficulty': 'easy',
            'category': 'General',
            'correct_answer': 'A',
            'incorrect_answers': 'B,C,D'
        }] * 5
        mock_cursor.fetchall.side_effect = [questions_list, questions_list, questions_list]
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.get('/get_questions/testuid')
        data = json.loads(response.data)
        self.assertEqual(len(data['questions']), 15)

    @patch('app.mysql')
    def test_get_questions_not_accepted(self, mock_mysql):
        # Simulate a user with non-accepted status
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'status': 'waiting'}
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.get('/get_questions/testuid')
        self.assertEqual(response.status_code, 403)

    @patch('app.mysql')
    def test_submit_answer_correct(self, mock_mysql):
        # Simulate question with correct answer "Answer"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'correct_answer': 'Answer'}
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.post('/submit_answer', json={
            'question_id': 1,
            'selected_answer': ' Answer '  # Testing extra spaces
        })
        data = json.loads(response.data)
        self.assertTrue(data.get('correct'))

    @patch('app.mysql')
    def test_submit_answer_incorrect(self, mock_mysql):
        # Simulate question with correct answer "Answer"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'correct_answer': 'Answer'}
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.post('/submit_answer', json={
            'question_id': 1,
            'selected_answer': 'Wrong'
        })
        data = json.loads(response.data)
        self.assertFalse(data.get('correct'))

    @patch('app.mysql')
    def test_submit_answer_invalid_question(self, mock_mysql):
        # Simulate question id not found; should return error and 400
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_mysql.connection.cursor.return_value = mock_cursor

        response = self.client.post('/submit_answer', json={
            'question_id': 999,
            'selected_answer': 'Anything'
        })
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(response.status_code, 400)

    def test_logout(self):
        # Set a session value, then logout should clear it and redirect to index.
        with self.client.session_transaction() as sess:
            sess['uid'] = 'testuid'
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.request.path, '/')

    def test_exit_page(self):
        response = self.client.get('/exit?result=win&earnings=1000')
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('win', text)
        self.assertIn('1000', text)

class KbcQuestionsTestCase(unittest.TestCase):
    @patch('questions.cnx')
    @patch('builtins.open', new_callable=mock_open, read_data='''
        {
            "results": [
                {
                    "question": "When someone is inexperienced they are said to be what color?",
                    "difficulty": "easy",
                    "category": "General Knowledge",
                    "correct_answer": "Green",
                    "incorrect_answers": ["Red", "Blue", "Yellow"]
                }
            ]
        }
    ''')
    def test_insert_questions(self, mock_file, mock_cnx):
        dummy_cursor = MagicMock()
        dummy_connection = MagicMock()
        dummy_connection.cursor.return_value = dummy_cursor
        dummy_connection.commit = MagicMock()
        import questions as q
        q.cnx = dummy_connection
        q.cursor = dummy_cursor

        # Call the function to insert questions
        q.insert_questions('dummy.json')
        mock_file.assert_called_with('dummy.json', 'r')
        self.assertEqual(dummy_cursor.execute.call_count, 1)
        args, _ = dummy_cursor.execute.call_args
        query_executed, params = args
        self.assertIn("INSERT INTO questions", query_executed)
        expected_params = (
            "When someone is inexperienced they are said to be what color?",
            "easy",
            "General Knowledge",
            "Green",
            json.dumps(["Red", "Blue", "Yellow"])
        )
        self.assertEqual(params, expected_params)
        dummy_connection.commit.assert_called_once()

    @patch('questions.cnx')
    @patch('builtins.open', new_callable=mock_open, read_data='{"results": []}')
    def test_insert_questions_empty(self, mock_file, mock_cnx):
        dummy_cursor = MagicMock()
        dummy_connection = MagicMock()
        dummy_connection.cursor.return_value = dummy_cursor
        dummy_connection.commit = MagicMock()
        import questions as q
        q.cnx = dummy_connection
        q.cursor = dummy_cursor
        q.insert_questions('dummy.json')
        mock_file.assert_called_with('dummy.json', 'r')
        # No INSERT queries should be executed.
        dummy_cursor.execute.assert_not_called()
        # Commit should still be called.
        dummy_connection.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
