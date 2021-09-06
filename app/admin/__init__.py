from flask import abort,redirect,url_for
from flask_admin.contrib import sqla
from flask_login import  current_user #,login_user, logout_user, login_required 
from flask_admin import Admin , AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin import helpers, expose
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
import sqlalchemy

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        from ..models import Role
        if current_user.is_authenticated and \
            current_user.role.name != "User":
            # current_user.role==Role.query.filter_by(name='Administrator').first():
            return super(MyAdminIndexView, self).index()
        return abort(404)

class MyModelView(sqla.ModelView):
    # column_filters = ('id')
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     from ..models import User,Role
    #     self.column_filters = [ isinstance(eval("{}.{}".format(self.model.__name__,i) ),sqlalchemy.orm.attributes.InstrumentedAttribute) for i in dir(self.model)]

    def is_accessible(self):
        from ..models import Role
        return current_user.is_authenticated and \
            current_user.role==Role.query.filter_by(name='Administrator').first()
        # current_user.role.name!="User"
    
    def inaccessible_callback(self, name, **kwargs):
        abort(404)

class AccntntModelView(sqla.ModelView):

    def is_accessible(self):
        from ..models import Role
        return current_user.is_authenticated and \
            current_user.role.name!="User"
    
    def inaccessible_callback(self, name, **kwargs):
        abort(404)


def addModelstoAdmin(admin,models,db):
    """add Models to Admin
    
    Keyword arguments:
    admin -- Admin instance
    models -- [(db.Model object)*]
    db -- Sqlite database instance
    Return: return_description
    """
    
    for table in models:
        admin.add_view(MyModelView(table, db.session))

def addModelstoAccntnt(admin,models,db):
    """add Models to Admin
    
    Keyword arguments:
    admin -- Admin instance
    models -- [(db.Model object)*]
    db -- Sqlite database instance
    Return: return_description
    """
    
    for table in models:
        admin.add_view(AccntntModelView(table, db.session))