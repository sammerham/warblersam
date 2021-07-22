"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from sqlalchemy.exc import NoResultFound
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

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        testuser = User.signup(username="testuser",
                                email="test@test.com",
                                password="testuser",
                                image_url=None)

        db.session.commit()
        self.test_user_id = testuser.id

        test_msg = Message(text="Hello World!", user_id=self.test_user_id)

        db.session.add(test_msg)
        db.session.commit()

        self.test_msg_id = test_msg.id

    def tearDown(self):
        """ Clean test database for next test """
        db.session.rollback()


    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_user_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", 
                            data={
                            "text": "Hello",
                            "user_id": self.test_user_id}
                            )

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msgs = Message.query.all()
            self.assertEqual(len(msgs), 2)
            msgs_text = [m.text for m in Message.query
                                        .filter(Message.user_id==self.test_user_id)
                                        .all()]
            self.assertIn("Hello", msgs_text)


    def test_add_message_logged_out(self):
        """If user is not logged out, does attempting to add new message
        get a redirect response to redirect location and fail to add message"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

            test_msg = Message.query.get(self.test_msg_id)

            self.assertEqual(Message.query.one(), test_msg)


    def test_add_message_logged_out_redirect_followed(self):
        """If user is not logged out, does attempting to add new message
        redirect and add flash message"""

        with self.client as c:
            resp = c.post("/messages/new",
                          data={"text": "Hello"},
                          follow_redirects=True
                          )

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn('Access unauthorized.', html)


    def test_delete_message(self):
        """Can user delete a message when logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_user_id

            resp = c.post(f"/messages/{self.test_msg_id}/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f'http://localhost/users/{sess[CURR_USER_KEY]}')

            self.assertRaises(NoResultFound, Message.query.one)

    def test_delete_message_redirect_followed(self):
        """If user is logged in and attempts to delete message should
        redirect and flash message 'Message Deleted!'"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_user_id

            resp = c.post(f"/messages/{self.test_msg_id}/delete",
                            follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn('Message Deleted!', html)

    def test_delete_message_logged_out(self):
        """If user is not logged in, does attempting to delete a message
        get a redirect response to redirect location and fail to delete message?"""

        with self.client as c:
            resp = c.post(f"/messages/{self.test_msg_id}/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

            test_msg = Message.query.get(self.test_msg_id)

            self.assertEqual(Message.query.one(), test_msg)   

    def test_delete_message_logged_out_redirect_followed(self):
        """If user is not logged in, does attempting to delete a message
        redirect and add flash message?"""

        with self.client as c:
            resp = c.post(f"/messages/{self.test_msg_id}/delete",
                          follow_redirects=True
                          )

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn('Access unauthorized.', html)                 
           