"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


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

#TODO: Add a test for liking own posts

class MessageModelTestCase(TestCase):
    """Message Model Tests"""

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

        db.session.add(test_u1)
        db.session.commit()

        self.test_1 = test_u1

        test_msg = Message(
            text="Hello World!",
            user_id=self.test_1.id
        )

        db.session.add(test_msg)
        db.session.commit()

        self.test_msg = test_msg

        self.client = app.test_client()

    def tearDown(self):
        """ clean test database for next test """
        db.session.rollback()

    def test_message_model(self):
        """Can we make a new message with the model?"""

        new_msg = Message(
            text="New Message Made!",
            user_id=self.test_1.id
        )
        db.session.add(new_msg)
        db.session.commit()

        self.assertEqual(new_msg.text, "New Message Made!")

        fail_msg = Message(
            user_id=self.test_1.id
        )
        db.session.add(fail_msg)

        self.assertRaises(IntegrityError, db.session.commit)

    def test_message_user_id(self):
        """Does the message have the correct user_id?"""

        test_u2 = User(
            email="test_u2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(test_u2)
        db.session.commit()

        new_msg = Message(
            text="New Message Made!",
            user_id=self.test_1.id
        )

        self.assertEqual(new_msg.user_id, self.test_1.id)
        self.assertNotEqual(new_msg.user_id, test_u2.id)

    def test_liked_messages(self):
        """Is there a relationship between the correct users and LikedMessages?"""

        test_u2 = User(
            email="test_u2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(test_u2)
        db.session.commit()

        liked_message = LikedMessage(
            user_id=test_u2.id,
            message_id=self.test_msg.id
            )

        db.session.add(liked_message)
        db.session.commit()

        self.assertIn(test_u2, self.test_msg.liked_by)
        self.assertIn(self.test_msg, test_u2.liked_messages)

    def test_user_created_messages_list(self):
        """Test that user instance.messages has correct list of user's own messages"""

        msg2 = Message(
            text="Hello World Again!",
            user_id=self.test_1.id
        )

        db.session.add(msg2)
        db.session.commit()

        self.assertEqual(len(self.test_1.messages), 2)

    def test_message_delete(self):
        """Test that message is successfully deleted."""

        db.session.delete(self.test_msg)
        db.session.commit()

        self.assertEqual(len(self.test_1.messages), 0)
        self.assertIsNone(Message.query.get(self.test_msg.id))
