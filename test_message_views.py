"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py
#    FLASK_DEBUG=False python3 -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.drop_all()
    db.create_all()

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        self.client = app.test_client()
        # Don't have WTForms use CSRF at all, since it's a pain to test
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_ECHO": False,
            "SQLALCHEMY_DATABASE_URI": os.environ.get('DATABASE_URL', 'postgresql:///warbler-test'),
            "DEBUG_TB_HOSTS": ["dont-show-debug-toolbar"],
            "WTF_CSRF_ENABLED": False
            })
        with app.app_context():
            User.query.delete()
            Message.query.delete()

            testuser = User.signup(username="testuser",
                                        email="test@test.com",
                                        password="testuser",
                                        image_url=None)
            
            db.session.commit()
            # bound to session
            self.testuser_id = testuser.id

    def tearDown(self):
        """Clean up any fouled transaction."""
        with app.app_context():
            db.session.rollback()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")


    def test_remove_message(self):
        """ Test for removing message """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            with app.app_context():
                user = User.query.filter(User.id==sess[CURR_USER_KEY]).first()
                msg = Message(text='testing')
                msg2 = Message(text='testing2')
                user.messages.append(msg)
                user.messages.append(msg2)
                db.session.commit()
                # user should have 2 messages added
                self.assertEqual(len(user.messages), 2)
                self.assertEqual(msg.text, 'testing')
                self.assertEqual(msg2.text, 'testing2')
                # should remove message from user
                url = f'/messages/{msg.id}/delete'
                resp = c.post(url, follow_redirects=True)
                html = resp.get_data(as_text=True)
                self.assertEqual(resp.status_code, 200)
                # removed message should be one less
                self.assertEqual(len(user.messages), 1)