"""User views tests."""

# run these tests like:
#
#    python -m unittest test_user_views.py

from flask import session
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

class UserViewsTestCase(TestCase):
    """Test User views."""

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
            # db.session.add_all([u,u2])
            db.session.commit()

            m = Message(
                text="testmessage",
                user_id=u.id
            )
            m2 = Message(
                text="testmessage2",
                user_id=u2.id
            )
            db.session.add_all([m, m2])
            db.session.commit()
            u.following.append(u2)
            u2.following.append(u)
            db.session.commit()
            
            self.u_id = u.id
            self.u_username = u.username
            self.u2_id = u2.id
            self.u2_username = u2.username

            

    def tearDown(self):
        """Clean up any fouled transaction."""
        with app.app_context():
            db.session.rollback()
    
    def test_basic_view(self):
        """ Test for basic view views """
        url = '/'
        with self.client:
            resp = self.client.get(url)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h1>What's Happening?</h1>", html)

    def test_signup_get(self):
        """ Test signup GET """
        url = '/signup'
        with self.client:
            resp = self.client.get(url)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)
            self.assertIn('<form action="/signup" method="POST" id="user_form">', html)

    def test_users(self):
        """ Test users route """
        url = '/users'
        with self.client:
            resp = self.client.get(url)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<p>@{self.u_username}</p>' , html)
            self.assertIn(f'<p>@{self.u2_username}</p>' , html)

    def test_user_details(self):
        """ Test users detail page profile """
        url = f'/users/{self.u_id}'
        with self.client:
            resp = self.client.get(url)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<a href="/users/{self.u_id}">@testuser</a>', html)

    def test_user_following(self):
        """ Test following page """
        url = f'/users/{self.u_id}/following'
        with self.client as c:
            with c.session_transaction() as session:
                # set session like if user is already logged in
                session["curr_user"] = self.u_id
            resp = c.get(url)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<p>@{self.u2_username}</p>', html)

    def test_user_followers(self):
        """ Test followers page """
        url = f'/users/{self.u_id}/following'
        with self.client as c:
            with c.session_transaction() as session:
                # set session like if user is already logged in
                session["curr_user"] = self.u_id
            resp = c.get(url)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<p>@{self.u2_username}</p>', html)

            