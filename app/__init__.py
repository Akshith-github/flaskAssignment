from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from .admin import Admin,MyAdminIndexView,MyModelView,addModelstoAdmin,addModelstoAccntnt

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    admin = Admin(app,index_view=MyAdminIndexView())
    from .models import User,Role,State,Taxbill,Standardtaxrecord,Taxrecord
    # Role
    # State
    # Taxbill
    # Standardtaxrecord
    # Taxrecord
    addModelstoAdmin(admin,[User,Role,Taxbill],db)
    addModelstoAccntnt(admin,[State,Standardtaxrecord,Taxrecord],db)


    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    from .main.forms import ProfileForm
    app.jinja_env.globals.update(ProfileForm=ProfileForm)
    app.jinja_env.globals.update(enumerate=enumerate)
    # print(dir(app.jinja_env.globals),type(app.jinja_env.globals))
    app.jinja_env.globals.update({"User":User,"Role":Role,"State":State,"Taxbill":Taxbill,"Standardtaxrecord":Standardtaxrecord,"Taxrecord":Taxrecord})
    return app
