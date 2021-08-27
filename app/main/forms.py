from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField , SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User , State
import re
from flask_login import current_user


class ProfileForm(FlaskForm):
    username = StringField('User name', validators=[DataRequired()])
    # email = StringField('Email', validators=[DataRequired(), Length(1, 64),Email()])
    # confirmed = BooleanField('Confirmed')
    pancard = StringField('Pan Card', validators=[DataRequired(), Length(10,10)])
    state = SelectField('State',choices=[],validators=[DataRequired()])
    submit = SubmitField('Update details')

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.state.choices.extend(
            [
                (stateitem.statename,stateitem.statename)
                for stateitem in State.query.all()
            ]
        )

    def configure_to_current_user(self):
        if(current_user.is_authenticated):
            self.username.data = current_user.username
            # self.email.data = current_user.email
            # self.confirmed.data = current_user.confirmed
            self.pancard.data = current_user.pancard
            self.state.data = current_user.state
        return self

    def validate_username(self, field):
        if(current_user.username != field.data):
            if User.query.filter_by(username=field.data).first():
                raise ValidationError('Username already in use.')
    
    def validate_pancard(self,field):
        if User.query.filter_by(pancard=field.data).first():
            raise ValidationError('Pancard already in use.')
        if(not re.fullmatch("^([a-zA-Z]){5}([0-9]){4}([a-zA-Z]){1}?$",field.data)):
            raise ValidationError('Invalid Pancard Number !! please check the number.')
        
    def validate_state(self, field):
        if not State.query.filter_by(statename=field.data):
            raise ValidationError('Invalid State selection !!')