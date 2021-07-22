"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase
from sqlalchemy.exc import NoResultFound
from models import db, connect_db, Message, User, Follows

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

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


#TODO: make more tests for user views

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        testuser1 = User.signup(username="testuser",
                                email="test@test.com",
                                password="testuser",
                                image_url=None)

        testuser2 = User.signup(username="testuser2",
                                email="test2@test.com",
                                password="testuser2",
                                image_url=None)

        db.session.commit()
        self.test_user_id1 = testuser1.id
        self.test_user_id2 = testuser2.id


    def tearDown(self):
        """ Clean test database for next test """
        db.session.rollback()


    def test_see_other_users_follows(self):
        """When a user is logged in, can they see other users'
        followers and following?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_user_id1

            follow_rlshp = Follows(
                user_being_followed_id=self.test_user_id1,
                user_following_id=self.test_user_id2)

            db.session.add(follow_rlshp)
            db.session.commit()

            resp = c.get(f'/users/{self.test_user_id2}/following')

            html = resp.get_data(as_text=True)

            testuser1 = User.query.get(self.test_user_id1)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(testuser1.username, html)
