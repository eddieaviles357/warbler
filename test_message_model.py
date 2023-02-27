"""User model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from models import db, User, Message, Follows
from sqlalchemy import exc

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.drop_all()
    db.create_all()

class MessageModelTestCase(TestCase):
    """Test Messages model."""

    def setUp(self):
        """Create test client, add sample data."""
        self.client = app.test_client()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_ECHO": False,
            "SQLALCHEMY_DATABASE_URI": os.environ.get('DATABASE_URL', 'postgresql:///warbler-test'),
            "DEBUG_TB_HOSTS": ["dont-show-debug-toolbar"]
            })

        with app.app_context():
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            u = User.signup(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD",
                image_url=''
            )
            u2 = User.signup(
                email="test2@test2.com",
                username="testuser2",
                password="HASHED_PASSWORD",
                image_url=''
            )
            db.session.add_all([u,u2])
            db.session.commit()

            m = Message(
                text="testmessage",
                user_id=u.id
            )
            m2 = Message(
                text="testmessage2",
                user_id=u2.id
            )
            db.session.add(m)
            db.session.commit()

            self.u_id = u.id

    def tearDown(self):
        """Clean up any fouled transaction."""
        with app.app_context():
            db.session.rollback()
            
    def test_message_model(self):
        """Does basic model work?"""
        with self.client:
            with app.app_context():
                u = User.query.first()
                m = len(u.messages)
                # User should have no messages & no followers
                self.assertEqual(len(u.messages), m)
                self.assertEqual(len(u.followers), 0)
    
    def test_message_max_title_characters(self):
        """ Test for max characters for model Message """
        with app.app_context():
            with self.assertRaises(exc.DataError):
                m = Message(
                    text="Hello this is a test to check for exceeding amount of characters that the message model can add to the database. This is going to be more than the max amount allowed for the model which is 140 characters Hello this is a test to check for exceeding amount of characters that the message model can add to the database. This is going to be more than the max amount allowed for the model which is 140 characters Hello this is a test to check for exceeding amount of characters that the message model can add to the database. This is going to be more than the max amount allowed for the model which is 140 characters",
                    user_id=self.u_id
                )
                db.session.add(m)
                db.session.commit()
                db.session.rollback()
    
    def test_message_no_user_id(self):
        """ Test for no valid user_id in db """
        with app.app_context():
            with self.assertRaises(exc.IntegrityError):
                m = Message(
                    text="Test for message",
                    user_id=8
                )
                db.session.add(m)
                db.session.commit()
                db.session.rollback()