from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask import current_app, request, url_for,jsonify
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager
from sqlalchemy.orm import validates 
from sqlalchemy import CheckConstraint
import re
from sqlalchemy.ext.declarative import declarative_base
from . import db, login_manager
Base = declarative_base()

class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<{} Role {}>'.format(self.id,self.name)
    
    def to_json(self):
        json_role = {
            # 'url': url_for('api.', id=self.id),
            'id':self.id,
            'role name': self.name,
            'users count': len(Role.query.all())}
        return json_role


class State(db.Model):
    __tablename__ = 'states'
    id = db.Column(db.Integer, primary_key=True)
    statename = db.Column(db.String(25), unique=True, index=True)
    state_residents = db.relationship('User', backref='state', lazy='select')
    taxes = db.relationship('Standardtaxrecord', backref='state',lazy='dynamic',primaryjoin="Standardtaxrecord.state_id==State.id")
    # taxes
    def __repr__(self):
        return "<{} State {}>".format(self.id,self.statename)
    
    def to_json(self):
        json_state = {
            # 'url': url_for('api.', id=self.id),
            'id':self.id,
            'statename': self.statename,
            'residentscount':len(State.query.all())
        }
        return json_state


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    # __table_args__ = (CheckConstraint("REGEXP_LIKE(pancard, '^([a-zA-Z]){5}([0-9]){4}([a-zA-Z]){1}?$')"),)
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=True)
    pancard=db.Column(db.String(10),CheckConstraint("pancard ~ '^([a-zA-Z]){5}([0-9]){4}([a-zA-Z]){1}?$'"),unique=True,index=True)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'))
    taxbills = db.relationship('Taxbill', backref='payer', lazy='dynamic',primaryjoin="Taxbill.payer_id==User.id")
    created_bills = db.relationship('Taxbill', backref='creator', lazy='dynamic',primaryjoin="Taxbill.creator_id==User.id")

    # @validates('pancard', include_backrefs=False)
    # def validate_pancard(self, key, pancardNo):
    #     assert re.fullmatch("^([a-zA-Z]){5}([0-9]){4}([a-zA-Z]){1}?$",pancardNo)
    #     return pancardNo

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def __repr__(self):
        return '<{} User {} [{}] {}>'.format(self.id,self.username,self.pancard if self.pancard else "pancard:NA", self.state.statename if self.state else "state:NA")
    
    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id),
            'username': self.username,
            'email':self.email,
            'pancard':self.pancard,
            'role':self.role.name,
            'state':self.state.statename if self.state else "NA",
            'pending_bills': ([ bill.to_json() for bill in self.taxbills.filter(Taxbill.status<4).all() ]),
            'taxbills': ([ bill.to_json() for bill in self.taxbills ])
        }
        return json_user

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                        expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])



class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Standardtaxrecord(db.Model):
    __table_args__ = (
        db.UniqueConstraint('taxname', 'state_id', name='unique_taxname_state_id'),
    )
    __tablename__ = 'standardtaxrecords'
    id = db.Column(db.Integer, primary_key=True)
    taxname = db.Column(db.String(10))
    allrelatedrecords = db.relationship('Taxrecord', backref='standard', lazy='dynamic',
        primaryjoin="Taxrecord.standardtax_id==Standardtaxrecord.id")
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'))
    activechild= db.relationship('Taxrecord', backref='activeparent',  uselist=False,
        primaryjoin="Taxrecord.parent_id==Standardtaxrecord.id")


    def  __repr__(self):
        return "<{} StdTax {} {}>".format(self.id,\
            self.taxname if self.taxname else "taxname:NA",
            self.state.statename if self.state else "state:NA",
            )
    
    def to_json(self):
        json_stdtax={
            "id": self.id,
            "type":"standard",
            "taxname":self.taxname,
            "state":self.state.statename if self.state else "NA",
            "current_tax_rec_id":self.activechild.id  if (self.activechild and len(self.activechild)==1) else "NA",
            "current_tax_percent":self.activechild.percent if(self.activechild and len(self.activechild)==1) else "NA",
            "billscount":len(self.bills.all())}
        return json_stdtax

class Taxrecord(db.Model):
    __tablename__ = 'taxrecords'
    id = db.Column(db.Integer, primary_key=True)
    percent = db.Column(db.Float)

    standardtax_id = db.Column(db.Integer, db.ForeignKey('standardtaxrecords.id'))
    parent_id=db.Column(db.Integer, db.ForeignKey('standardtaxrecords.id'))
    # activeparent = db.relationship('Standardtaxrecord', backref='activechild',  uselist=False,
    #     primaryjoin="Taxrecord.parent_id==Standardtaxrecord.id")

    def __repr__(self):
        return "{} TaxRec @{} @{} {}%".format(self.id,
        self.standard.taxname if self.standard else "taxname:NA",
        self.standard.state.statename if self.standard and self.standard.state else "state:NA",
        self.percent if self.percent else "percent:NA")

    def to_json(self):
        json_taxrec={
            "id": self.id,
            "type":"record(version) of standard tax",
            "taxname":self.standard.taxname,
            "state":self.standard.state.statename if self.standard.state else "NA",
            "standard_tax_rec_id":self.standard.id,
            "requested_taxrec_tax_percent":self.percent,
            "paidbillscount":len(self.bills.all())}
        return json_taxrec

from sqlalchemy import UniqueConstraint
Taxbillstandardtaxrecordtaxes = db.Table(
    'taxbillsstandardtaxrecordtaxes',
    db.Column('taxbill_id', db.Integer, db.ForeignKey('taxbill.id'),primary_key=True),
    db.Column('standardtaxrecord_id', db.Integer, 
            db.ForeignKey('standardtaxrecords.id'),primary_key=True)
)

Taxbilltaxrecordpaidtaxes = db.Table(
    'taxbilltaxrecordpaidtaxes',
    db.Column('taxbill_id', db.Integer, db.ForeignKey('taxbill.id'),primary_key=True),
    db.Column('taxrecord_id', db.Integer, 
            db.ForeignKey('taxrecords.id'),primary_key=True)
)

Status={
    "NEW" : 1,
    "DELAYED" : 2,
    "PAID" : 4,
    "4":"PAID",
    "2":"DELAYED",
    "1":"NEW"
}

class Taxbill(db.Model):
    __tablename__ = 'taxbill'
    id = db.Column(db.Integer, primary_key=True)
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    billnumber = db.Column(db.Integer,unique=True,index=True)
    taxes = db.relationship("Standardtaxrecord",
                    secondary=Taxbillstandardtaxrecordtaxes,
                    # primaryjoin="Taxbill.id==Taxbillstandardtaxrecordtaxes.c.standardtaxrecord_id",
                    # secondaryjoin="Taxbill.id==Taxbillstandardtaxrecordtaxes.c.taxbill_id",
                    backref=db.backref('bills', lazy='dynamic'),
                    lazy="dynamic",
                    post_update=True
                    )
    paidtaxes = db.relationship("Taxrecord",
                    secondary=Taxbilltaxrecordpaidtaxes,
                    # primaryjoin="Taxbill.id==Taxbilltaxrecordpaidtaxes.c.taxrecord_id",
                    # secondaryjoin="Taxbill.id==Taxbilltaxrecordpaidtaxes.c.taxbill_id",
                    backref=db.backref('bills', lazy='dynamic'),
                    lazy="dynamic",
                    post_update=True
                    )
    taxable_value = db.Column(db.Integer,default=0)
    # enum status
    total_amount = db.Column(db.Integer)
    due_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Integer,default=1)

    def __init__(self,*args,**kwargs):
        super(Taxbill, self).__init__(*args,**kwargs)
        self.set_current_total_amount()
        
    def set_current_total_amount(self):
        if(self.status != 4 and self.taxable_value):
            total_amount =0
            taxable_value=self.taxable_value
            for tax in self.taxes.all():
                total_amount += taxable_value*tax.activechild.percent/100
                print(taxable_value*tax.activechild.percent/100)
            self.total_amount=total_amount

    @property
    def amount_to_be_paid(self):
        self.set_current_total_amount()
        return self.total_amount

    def is_paid(self):
        if(self.status == 4):
            return True

    def __repr__(self):
        return "< Bill No: {} to {}>".format(self.billnumber,self.creator)

    @property
    def status_msg(self):
        if(self.status!=4):
            if(datetime.utcnow()>self.due_date):
                self.status = 2
            else:
                self.status = 1
            db.session.add(self)
            db.session.commit()
        return Status[str(self.status)]

    def to_json(self):
        json_taxbill={
            "id": self.id,
            "type":"tax bill",
            "billnumber":self.billnumber,
            "payer":self.payer.username,
            "creator":self.creator.username,
            "pancard":self.payer.pancard if self.payer and self.payer.pancard else "NA",
            "taxable_value":self.taxable_value,
            "total_tax_amount":self.total_amount if self.total_amount else "NO ENTRY FOUND",
            "due_date(UTC)":self.due_date.strftime("%m/%d/%Y  %H:%M:%S"),
            "status":self.status_msg}
        if(self.paidtaxes and self.status==Status["PAID"]):
            json_taxbill["paid_taxes"]={
                i:{"taxname":bill.standard.taxname,"percent":bill.percent} for i,bill in enumerate(self.paidtaxes.all())
            }
        else:
            json_taxbill["taxes_to_be_paid"]={
                i:{"taxname":bill.taxname,"percent":bill.activechild.percent} for i,bill in enumerate(self.taxes.all())
            }
        return json_taxbill

    @staticmethod
    def on_status_set_change(target, value, oldvalue, initiator):
        if(value==4):#paid
            target.set_current_total_amount()
            for stdtax in target.taxes.all():
                if stdtax.activechild in target.paidtaxes.all():
                    continue
                target.paidtaxes.append(stdtax.activechild)
                print(target.paidtaxes.all())
            return
        else:
            target.set_current_total_amount()
        # if(value==2):
        #     #needs to add ta intrest feature
        #     if(oldvalue in [ 4 , "4" ]):
        #         target.status=4
        #         print("cannot convert paid bill to delayed")
        #         print(value,oldvalue)
        #     return
        # if(value==1):
        #     if(oldvalue in [ 4 , "4" ]):
        #         target.status=4
        #         print("cannot convert paid bill to new")
        #         print(value,oldvalue)
        #     return
    
    @staticmethod
    def set_total_value(target, value=None, oldvalue=None, initiator=None):
        if(target.status != 4): 
            #unpaid case attempt to change total amoun
            target.set_current_total_amount()
            return
        else:
            Taxbill.taxable_value=oldvalue
            return

    @staticmethod
    def on_taxes_modification(target, collection=None, collection_adapter=None):
        if(target.status!=4):
            target.set_current_total_amount()



db.event.listen(Taxbill.status, 'set', Taxbill.on_status_set_change)
db.event.listen(Taxbill.status, 'modified', Taxbill.on_status_set_change)

db.event.listen(Taxbill.taxable_value, 'set', Taxbill.set_total_value)
db.event.listen(Taxbill.taxable_value, 'modified', Taxbill.set_total_value)

db.event.listen(Taxbill.taxes,'init_collection', Taxbill.on_taxes_modification)
# db.event.listen(Taxbill.taxes,'append', Taxbill.on_taxes_modification)
# #
