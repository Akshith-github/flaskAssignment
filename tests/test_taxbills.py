import unittest
import json
import re
from base64 import b64encode
from app import create_app, db
from app.models import User, Role , State,Taxbill,Standardtaxrecord,Taxrecord
from datetime import datetime, timedelta

class TaxBillTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_api_headers(self, username, password):
        return {
            'Authorization': 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_taxbill_total(self):
        # add two users
        r = Role.query.filter_by(name='User').first()
        m = Role.query.filter_by(name='Moderator').first()
        ts = State(statename="Telangana")
        db.session.add(ts)
        db.session.commit()
        self.assertIsNotNone(r)
        u1 = User(email='john1@example.com', username='john1',
                  password='cat', confirmed=True, role=r,state=ts)
        m1 = User(email='susan1@example.com', username='susan1',
                  password='dog', confirmed=True, role=m)
        db.session.add_all([u1, m1])
        db.session.commit()
        self.assertEqual(User.query.filter_by(email='john1@example.com').first().username, 'john1')
        #create stdtaxrecord
        cgst = Standardtaxrecord(taxname="CGST")
        db.session.add(cgst)
        db.session.commit()
        cgstv1 = Taxrecord(standard=cgst,activeparent=cgst,percent=10)

        db.session.add(cgstv1)
        db.session.commit()

        #create taxbills
        tb = Taxbill(payer=u1,creator=m1,billnumber=1,taxable_value=100,due_date=datetime.utcnow()+timedelta(days=4),taxes=[cgst])
        db.session.add(tb)
        db.session.commit()
        self.assertEqual(tb.amount_to_be_paid , 10)
        response = self.client.get(
            '/api/v1/users/{}'.format(u1.id),
            headers=self.get_api_headers('john1@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['pending_bills'][0]['total_tax_amount'], 10)

    def test_taxbill_paid(self):
        # add two users
        r = Role.query.filter_by(name='User').first()
        m = Role.query.filter_by(name='Moderator').first()
        ts = State(statename="Telangana")
        db.session.add(ts);db.session.commit()
        self.assertIsNotNone(r)
        u1 = User(email='john1@example.com', username='john1',password='cat', confirmed=True, role=r,state=ts)
        m1 = User(email='susan1@example.com', username='susan1',password='dog', confirmed=True, role=m)
        db.session.add_all([u1, m1]);db.session.commit()
        self.assertEqual(User.query.filter_by(email='john1@example.com').first().username, 'john1')
        #create stdtaxrecord
        cgst = Standardtaxrecord(taxname="CGST")
        db.session.add(cgst);db.session.commit()
        cgstv1 = Taxrecord(standard=cgst,activeparent=cgst,percent=10)

        db.session.add(cgstv1);db.session.commit()
        #create taxbills
        tb = Taxbill(payer=u1,creator=m1,billnumber=1,taxable_value=100,due_date=datetime.utcnow()+timedelta(days=4),taxes=[cgst]);db.session.add(tb);db.session.commit()
        cgstv2 = Taxrecord(standard=cgst,activeparent=cgst,percent=12)
        db.session.add(cgstv2);db.session.commit()
        #paid tax bill
        tb.status=4
        db.session.add(tb)
        db.session.commit()
        self.assertEqual(tb.amount_to_be_paid , 12)
        cgstv3 = Taxrecord(standard=cgst,activeparent=cgst,percent=8)
        db.session.add(cgstv2);db.session.commit()
        response = self.client.get(
            '/api/v1/users/{}'.format(u1.id),
            headers=self.get_api_headers('john1@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        # print(tb.to_json())
        # print(u1.to_json())
        self.assertEqual(len(json_response['pending_bills']), 0)
        self.assertEqual(json_response['taxbills'][0]['paid_taxes']['0']['taxname'], 'CGST')
        self.assertEqual(json_response['taxbills'][0]['paid_taxes']['0']['percent'], 12)
