from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager
from sqlalchemy.orm import validates 
from sqlalchemy import CheckConstraint
import re
from sqlalchemy.ext.declarative import declarative_base
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
        return '<Role %r>' % self.name


class State(db.Model):
    __tablename__ = 'states'
    id = db.Column(db.Integer, primary_key=True)
    statename = db.Column(db.String(25), unique=True, index=True)
    state_residents = db.relationship('User', backref='state', lazy='dynamic')
    taxes = db.relationship('Standardtaxrecord', backref='state',lazy='dynamic',primaryjoin="Standardtaxrecord.state_id==State.id")
    # taxes
    def __repr__(self):
        return "<State {}>".format(self.statename)
    
    def to_json(self):
        json_state = {
            # 'url': url_for('api.', id=self.id),
            'id':self.id,
            'statename': self.statename
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
    confirmed = db.Column(db.Boolean, default=False)
    pancard=db.Column(db.String(10),CheckConstraint("pancard ~ '^([a-zA-Z]){5}([0-9]){4}([a-zA-Z]){1}?$'"),unique=True,index=True,)
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
        return '<User %r>' % self.username
    
    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id),
            'username': self.username,
            'email':self.email,
            'pan':self.pancard,
            'role':self.role.name,
            'state':self.state.statename
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

Status={
    "UNPAID" : 1,
    "DUE" : 2,
    "PAID" : 4,
    "4":"PAID",
    "2":"DUE",
    "1":"UNPAID"
}

Taxbillstandardtaxrecordtaxes = db.Table(
    'taxbillsstandardtaxrecordtaxes',
    # Base.metadata,
    db.Column('taxbill_id', db.Integer, db.ForeignKey('taxbill.id')),
    db.Column('standardtaxrecord_id', db.Integer, 
            db.ForeignKey('standardtaxrecords.id'))
)
class Taxbill(db.Model):
    __tablename__ = 'taxbill'
    id = db.Column(db.Integer, primary_key=True)
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)
    billnumber = db.Column(db.Integer,unique=True,index=True,nullable=False)
    taxes = db.relationship("Standardtaxrecord",
                    secondary=Taxbillstandardtaxrecordtaxes,
                    # primaryjoin="Taxbill.id==Taxbillstandardtaxrecordtaxes.c.standardtaxrecord_id",
                    # secondaryjoin="Taxbill.id==Taxbillstandardtaxrecordtaxes.c.taxbill_id",
                    backref=db.backref('bills', lazy='dynamic'),
                    lazy="dynamic"
                    )
    # taxable_value
    # paid_taxes
    # othertaxespaid
    # enum status
    total_amount = db.Column(db.Integer)
    due_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Integer,default=1,nullable=False)

    def __repr__(self):
        return "< Bill No: {} to {}>".format(self.billnumber,self.creator)

class Standardtaxrecord(db.Model):
    __tablename__ = 'standardtaxrecords'
    id = db.Column(db.Integer, primary_key=True)
    taxname = db.Column(db.String(10), index=True)

    allrecords = db.relationship('Taxrecord', backref='standard', lazy='dynamic',
        primaryjoin="Taxrecord.standardtax_id==Standardtaxrecord.id")
    activerecord_id=db.Column(db.Integer, db.ForeignKey('taxrecords.id'))
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'))

class Taxrecord(db.Model):
    __tablename__ = 'taxrecords'
    id = db.Column(db.Integer, primary_key=True)
    percent = db.Column(db.Float)

    standardtax_id = db.Column(db.Integer, db.ForeignKey('standardtaxrecords.id'))
    parent = db.relationship('Standardtaxrecord', backref='activerecord',  uselist=False,
        primaryjoin="Taxrecord.id==Standardtaxrecord.activerecord_id")