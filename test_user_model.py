"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from models import db, User, Message, Follows
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.drop_all()
    db.create_all()

class UserModelTestCase(TestCase):
    """Test User model."""

    def setUp(self):
        """Create test client, add sample data."""
        self.client = app.test_client()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_ECHO": False,
            "SQLALCHEMY_DATABASE_URI": os.environ.get('DATABASE_URL', 'postgresql:///blogly_test'),
            "DEBUG_TB_HOSTS": ["dont-show-debug-toolbar"]
            })

        with app.app_context():
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )
            u2 = User(
                email="test2@test2.com",
                username="testuser2",
                password="HASHED_PASSWORD"
            )
            u3 = User(
                email="test3@test3.com",
                username="testuser3",
                password="HASHED_PASSWORD"
            )
            db.session.add_all([u,u2,u3])
            db.session.commit()


    def tearDown(self):
        """Clean up any fouled transaction."""
        with app.app_context():
            db.session.rollback()
            
    def test_user_model(self):
        """Does basic model work?"""
        with self.client:
            with app.app_context():
                u = User.query.first()
                # User should have no messages & no followers
                self.assertEqual(len(u.messages), 0)
                self.assertEqual(len(u.followers), 0)
                # User __repr__  displays correct information about User
                self.assertEqual(u.__repr__(), f"<User #{u.id}: {u.username}, {u.email}>")

    def test_is_followed_by(self):
        """ Test for method is_followed_by """
        with app.app_context():
            users = User.query.all()
            u = users[0]
            u2 = users[1]
            u3 = users[2]
            u.following.append(u2)
            db.session.commit()
            # is user being followed by other user
            self.assertTrue(u2.is_followed_by(u))
            self.assertEqual(len(u.following), 1)
            self.assertFalse(u2.is_followed_by(u3))

    def test_is_following(self):
        """ Test for method is_following """
        with app.app_context():
            users = User.query.all()
            u = users[0]
            u2 = users[1]
            u3 = users[2]
            u.following.append(u2)
            db.session.commit()
            # is user following other user
            self.assertTrue(u.is_following(u2))
            self.assertEqual(len(u2.followers), 1)
            self.assertFalse(u.is_following(u3))

    def test_signup(self):
        """ Test signup of user """
        with app.app_context():
            users_orig = User.query.all()
            # get length of orig users in db to be used to compare later
            orig_users_len = len(users_orig)
            User.signup(
                    username="signupusertest",
                    email="signup@test.com",
                    password="SIGNUPUSERTEST",
                    image_url=''
                    )
            db.session.commit()
            users = User.query.all()
            # get updated users length to compare old users length
            users_len = len(users)
            self.assertEqual(users_len, orig_users_len+1)
            
            # test integrityError same email
            with self.assertRaises(exc.IntegrityError):
                User.signup(
                    email="signup@test.com",
                    username="wontwork",
                    password="WONTWORK",
                    image_url=''
                    )
                db.session.commit()
            db.session.rollback()

            # test integrityError with username
            with self.assertRaises(exc.IntegrityError):
                User.signup(
                    email="tester4@test.com",
                    username="testuser",
                    password="WONTWORK",
                    image_url=''
                    )
                db.session.commit()
            db.session.rollback()

    def test_authenticate(self):
        """ Test authenticating user """

        with app.app_context():
            user = User.signup(
                    username="signupusertest",
                    email="signup@test.com",
                    password="SIGNUPUSERTEST",
                    image_url=''
                    )
            db.session.commit()
            # Wrong password
            self.assertFalse(User.authenticate(user.username, 'SIGNUPUSERTESt'))
            # Wrong username
            self.assertFalse(User.authenticate('wronguser', 'SIGNUPUSERTEST'))
            # Correct credentials
            self.assertTrue(User.authenticate(user.username, 'SIGNUPUSERTEST'))
                