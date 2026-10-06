import unittest
from werkzeug.security import generate_password_hash
from app import create_app, db
from models import User, Ticket

class TestEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed test manager user if not already existing
        self.manager = User.query.filter_by(username='manager').first()
        if not self.manager:
            self.manager = User(
                username='manager',
                password_hash=generate_password_hash('password'),
                role='manager',
                name='Manager'
            )
            db.session.add(self.manager)

        # Seed test student user for authorization checks
        self.student = User.query.filter_by(username='student').first()
        if not self.student:
            self.student = User(
                username='student',
                password_hash=generate_password_hash('password'),
                role='student',
                name='Student'
            )
            db.session.add(self.student)

        # Seed test ticket
        self.ticket = Ticket(zone_id=1, status='unassigned')
        db.session.add(self.ticket)

        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_assign_ticket_success(self):
        """Verify manager can assign a ticket cleanly without TypeError or syntax crashes."""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.manager.id)

        response = self.client.post('/assign_ticket', data={
            'ticket_id': str(self.ticket.id),
            'worker_id': '101'
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue('/manager' in response.headers.get('Location'))

        updated_ticket = Ticket.query.get(self.ticket.id)
        self.assertEqual(updated_ticket.assigned_worker_id, 101)
        self.assertEqual(updated_ticket.status, 'assigned')

    def test_auto_assign_authorization(self):
        """Verify unauthenticated or non-manager users are forbidden from auto_assign."""
        # 1. Unauthenticated request -> redirects to login (302)
        res_unauth = self.client.post('/auto_assign')
        self.assertEqual(res_unauth.status_code, 302)
        self.assertIn('/login', res_unauth.headers.get('Location'))

        # 2. Authenticated student request (non-manager) -> forbidden (403)
        self.student.password_hash = generate_password_hash('password')
        db.session.commit()

        login_res = self.client.post('/login', data={
            'username': self.student.username,
            'password': 'password'
        })
        self.assertEqual(login_res.status_code, 302)

        res_forbidden = self.client.post('/auto_assign')
        self.assertEqual(res_forbidden.status_code, 403)

if __name__ == '__main__':
    unittest.main()
