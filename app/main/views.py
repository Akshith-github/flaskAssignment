from flask import render_template,redirect,url_for,flash
from . import main
from .forms import ProfileForm
from flask_login import current_user
from ..models import User,State
from .. import db

@main.route('/')
def index():
    if(current_user.is_authenticated):
        ProfileFormObj = ProfileForm()
        ProfileFormObj.configure_to_current_user()
        return render_template('index.html',ProfileFormObj=ProfileFormObj)
    return render_template('index.html')

@main.post("/profileform")
def profileform():
    ProfileFormObj = ProfileForm()
    if(ProfileFormObj.validate_on_submit()):
        user = User.query.filter_by(id=current_user.id).first()
        user.username = ProfileFormObj.username.data
        user.pancard = ProfileFormObj.pancard.data
        user.state = State.query.filter_by(statename=ProfileFormObj.state.data).first()
        db.session.add(user)
        db.session.commit()
        flash("updated details successfully")
    else:
        for i in ProfileFormObj.errors:
            flash("failed updating due to : " + str(i)\
                +str("   ".join(ProfileFormObj.errors[i])))
    return redirect(url_for("main.index"))