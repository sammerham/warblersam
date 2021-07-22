"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows, LikedMessage

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

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        test_u1 = User(
            email="test_u1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        test_u2 = User(
            email="test_u2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(test_u1)
        db.session.add(test_u2)
        db.session.commit()

        self.test_1 = test_u1
        self.test_2 = test_u2

        self.client = app.test_client()

    def tearDown(self):
        """ clean test database for next test """
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does the repr method work as expected?"""

        new_user = User(
            email="repr@test.com",
            username="testuser_repr",
            password="HASHED_PASSWORD"
        )
        db.session.add(new_user)
        db.session.commit()

        self.assertEqual(f"{new_user}", f"<User #{new_user.id}: {new_user.username}, {new_user.email}>")

    def test_is_following(self):
        """Does is_following() successfully detect when 'user1' is following 'user2'?
        and does is_following() successfully detect if 'user1' is not following 'not_followed'"""

        follow_rlshp = Follows(
            user_being_followed_id=self.test_2.id,
            user_following_id=self.test_1.id)

        db.session.add(follow_rlshp)
        db.session.commit()

        self.assertEqual(self.test_1.is_following(self.test_2), True)
        self.assertEqual(self.test_2.is_following(self.test_1), False)

    def test_is_followed_by(self):
        """Does is_followed_by detect when 'user2' is followed by 'user1'
        and does it detect that 'user1' is not followed by 'user2'"""

        follow_rlshp = Follows(
            user_being_followed_id=self.test_2.id,
            user_following_id=self.test_1.id)

        db.session.add(follow_rlshp)
        db.session.commit()

        self.assertEqual(self.test_2.is_followed_by(self.test_1), True)
        self.assertEqual(self.test_1.is_followed_by(self.test_2), False)

    def test_signup(self):
        """Does signup successfully create a new user given valid credentials
        and fail to create a new user if any of the validations 
        (e.g. uniqueness, non-nullable fields) fail?"""

        signed_up = User.signup("signupTest", "signUp@gmail.com", "mypassw", "")
        db.session.commit()
        
        self.assertEqual(signed_up.username, "signupTest")

        failed_sign = User.signup("failSignUp", "test_u1@test.com", "mypassw", "")

        self.assertRaises(IntegrityError, db.session.commit)

    def test_authenticate(self):
        """Does authenticate:
        successfully return a user when given a valid username and password?
        and return false when password or username is invalid?"""

        authen_user = User.signup("authenTest", "authen@gmail.com", "mypassw", "")
        db.session.commit()

        #correct credentials
        self.assertEqual(User.authenticate("authenTest", "mypassw"), authen_user)
        #wrong password, right username
        self.assertEqual(User.authenticate("authenTest", "notmypassw"), False)
        #wrong username, right password
        self.assertEqual(User.authenticate("notAuthenTest", "mypassw"), False)

