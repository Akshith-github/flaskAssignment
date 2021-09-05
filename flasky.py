import os
import click
from flask_migrate import Migrate , upgrade
from app import create_app, db
from app.models import User, Role, Permission , State , Taxbillstandardtaxrecordtaxes , Taxbilltaxrecordpaidtaxes , Taxbill , Standardtaxrecord , Taxrecord
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Permission=Permission,
    State=State, 
    Taxbillstandardtaxrecordtaxes=Taxbillstandardtaxrecordtaxes,
    Taxbilltaxrecordpaidtaxes=Taxbilltaxrecordpaidtaxes,
    Taxbill=Taxbill,
    Standardtaxrecord=Standardtaxrecord,
    Taxrecord=Taxrecord
    )


@app.cli.command()
@click.argument('test_names', nargs=-1)
def test(test_names):
    """Run the unit tests."""
    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # migrate database to latest revision
    upgrade()
    # create or update user roles
    Role.insert_roles()
