import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, UserEditForm, TokenValidationForm
from models import db, connect_db, User, Message, LikedMessage

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
database_url = os.environ.get('DATABASE_URL', 'postgresql:///warbler')
database_url = database_url.replace('postgres://', 'postgresql://')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError as exc:
            if 'users_email' in exc.orig.args[0]:
                flash("Please use a different email", 'danger')
            if 'username' in exc.orig.args[0]:
                flash("Please use a different username", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout', methods=["POST"])
def logout():
    """Handle logout of user."""

    form = TokenValidationForm()
    if form.validate_on_submit():

        do_logout()
        flash("logout successful", 'success')

    return redirect('/login')


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')
    form = TokenValidationForm()

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users, form=form)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)
    form = TokenValidationForm()
    return render_template('users/show.html', user=user, form=form)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = TokenValidationForm()
    user = User.query.get_or_404(user_id)

    return render_template('users/following.html', user=user, form=form)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = TokenValidationForm()
    user = User.query.get_or_404(user_id)

    return render_template('users/followers.html', user=user, form=form)


@app.route('/users/<int:user_id>/likes')
def users_likes(user_id):
    """Show a list of warbles this user liked"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = TokenValidationForm()
    user = User.query.get_or_404(user_id)

    return render_template('users/likes.html', user=user, form=form)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"]) # TODO: find more RESTful route name
def edit_profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():
        if User.authenticate(g.user.username, form.password.data):
            try:
                g.user.username = form.username.data
                g.user.email = form.email.data
                g.user.image_url = form.image_url.data
                g.user.header_image_url = form.header_image_url.data
                g.user.bio = form.bio.data

                db.session.commit()

            # TODO: catch this error at a higher level, in form or model
            except IntegrityError as exc:
                db.session.rollback()
                if 'users_email' in exc.orig.args[0]:
                    flash("Please use a different email", 'danger')
                if 'username' in exc.orig.args[0]:
                    flash("Please use a different username", 'danger')
                return render_template('users/edit.html', form=form)

            flash("Update successful!", "success")
            return redirect(f'/users/{g.user.id}')

        else:
            flash("Error: Incorrect Password", "danger")
            return redirect('/')

    return render_template("users/edit.html", form=form, user=g.user)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = TokenValidationForm()
    if form.validate_on_submit():

        Message.query.filter(Message.user_id == g.user.id).delete()

        do_logout()

        db.session.delete(g.user)
        db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
            msg = Message(text=form.text.data)
            g.user.messages.append(msg)
            db.session.commit()
            flash("New Message Added!", "success")

            return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    form = TokenValidationForm()
    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg, form=form)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()
    flash("Message Deleted!", "success")
    return redirect(f"/users/{g.user.id}")


@app.route('/messages/<int:message_id>/like', methods=["POST"])
def messages_like(message_id):
    """Like a message"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = TokenValidationForm()
    referrer = request.headers.get("Referer")

    if form.validate_on_submit():
        liked_message = LikedMessage(user_id=g.user.id, message_id=message_id)
        db.session.add(liked_message)
        db.session.commit()
        flash("Message liked!", "success")

    if referrer:
        return redirect(f'{referrer}')
    else:
        return redirect(f'/messages/{message_id}')


@app.route('/messages/<int:message_id>/unlike', methods=["POST"])
def messages_unlike(message_id):
    """Unlike a message and redirects"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = TokenValidationForm()
    referrer = request.headers.get("Referer")

    if form.validate_on_submit():

        liked_message = LikedMessage.query.filter(
                        LikedMessage.user_id == g.user.id,
                        LikedMessage.message_id == message_id).one()

        db.session.delete(liked_message)
        db.session.commit()
        flash("Message unliked!", "success")
    if referrer:
        return redirect(f'{referrer}')
    else:
        return redirect(f'/messages/{message_id}')

##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    form = TokenValidationForm()

    if g.user:
        following_user_ids = [u.id for u in g.user.following] + [g.user.id]
        messages = (Message
                    .query
                    .filter(Message.user_id.in_(following_user_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages, form=form)

    else:
        return render_template('home-anon.html', form=form)


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
