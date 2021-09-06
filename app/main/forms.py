from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField , SelectField , IntegerField , SelectMultipleField , DateTimeField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User,Role,State,Taxbill,Standardtaxrecord,Taxrecord
import re
from flask_login import current_user
from datetime import datetime
from flask_admin.form.widgets import DateTimePickerWidget


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

class PayForm(FlaskForm):
    pay = SubmitField('Pay Bill')

class CreateBillForm(FlaskForm):
    billnumber = IntegerField('Bill Number', validators=[DataRequired()])
    pancardNo = StringField('Pan Card', validators=[DataRequired(), Length(10,10)])
    taxes = SelectMultipleField('taxes',choices=[], validators=[DataRequired(),])
    taxable_value = IntegerField('Taxable Value', validators=[DataRequired(),])
    duedateloc = DateTimeField('Due Date(local time)',widget=DateTimePickerWidget(), validators=[DataRequired(),])
    duedate = DateTimeField('Due Date(UTC time)',widget=DateTimePickerWidget(), validators=[DataRequired(),])
    create = SubmitField('Create')

    def __init__(self, *args, **kwargs):
        super(CreateBillForm, self).__init__(*args, **kwargs)
        self.taxes.choices.extend(
            [
                (str(item.id),item)
                for item in Standardtaxrecord.query.all()
            ]
        )

    def validate_duedate(self, field):
        currdate = datetime.utcnow()
        if(field.data<currdate):
            raise ValidationError("Selected Date should be future reference "+ currdate.strftime("%m/%d/%Y  %H:%M:%S"))

    def validate_taxes(self,field):
        user = User.query.filter_by(pancard=self.pancardNo.data).first()
        if (user):
            for item in field.data:
                stdrec=Standardtaxrecord.query.filter_by(id=int(item)).first()
                if (stdrec.state and user.state!=stdrec.state):
                    raise ValidationError("Payer's state and selected tax state did not match")

    def validate_pancardNo(self,field):
        if(not re.fullmatch("^([a-zA-Z]){5}([0-9]){4}([a-zA-Z]){1}?$",field.data)):
            raise ValidationError('Invalid Pancard Number !! please check the number.')
        if not User.query.filter_by(pancard=field.data).first():
            raise ValidationError('No related user Found !!!')
    
    def validate_billnumber(self, field):
        if Taxbill.query.filter_by(billnumber=field.data).first():
                raise ValidationError('Bill number already in use.')

class UpdateBillForm(FlaskForm):
    billnumber=None
    bill=None
    pancardNo = StringField('Pan Card', validators=[DataRequired(), Length(10,10)])
    taxes = SelectMultipleField('taxes',choices=[], validators=[DataRequired(),])
    taxable_value = IntegerField('Taxable Value', validators=[DataRequired(),])
    duedateloc = DateTimeField('Due Date(local time)',widget=DateTimePickerWidget(), validators=[])
    duedate = DateTimeField('Due Date(UTC time)',widget=DateTimePickerWidget(), validators=[DataRequired(),])
    update = SubmitField('Update')

    def __init__(self,billnumber:int, *args, **kwargs):
        self.billnumber=billnumber
        bill = Taxbill.query.filter_by(billnumber = self.billnumber).first()
        if(not bill):
            raise ValidationError("No related bills exist to create form")
        else:
            self.bill=bill
        super(UpdateBillForm, self).__init__(*args, **kwargs)
        self.taxes.choices.extend(
            [
                (str(item.id),item)
                for item in Standardtaxrecord.query.all()
            ]
        )

    def validate_duedate(self, field):
        if(self.bill.due_date==field.data):
            return
        currdate = datetime.utcnow()
        if(field.data<currdate):
            raise ValidationError("Selected Date should be future reference "+ currdate.strftime("%m/%d/%Y  %H:%M:%S"))

    def validate_taxes(self,field):
        user = User.query.filter_by(pancard=self.pancardNo.data).first()
        if (user):
            for item in field.data:
                stdrec=Standardtaxrecord.query.filter_by(id=int(item)).first()
                if (stdrec.state and user.state!=stdrec.state):
                    raise ValidationError("Payer's state and selected tax state did not match")

    def validate_pancardNo(self,field):
        if(not re.fullmatch("^([a-zA-Z]){5}([0-9]){4}([a-zA-Z]){1}?$",field.data)):
            raise ValidationError('Invalid Pancard Number !! please check the number.')
        if not User.query.filter_by(pancard=field.data).first():
            raise ValidationError('No related user Found !!!')

    def set_data(self):
        bill = Taxbill.query.filter_by(billnumber = self.billnumber).first()
        # pancardNo,taxes,taxable_value,duedate
        self.pancardNo.data = bill.payer.pancard
        self.taxes.data = [tax.id for tax in bill.taxes.all()]
        self.taxable_value.data = bill.taxable_value
        self.duedate.data = bill.due_date