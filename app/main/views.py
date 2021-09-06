from flask import render_template,redirect,url_for,flash,abort,request,session
from . import main
from .forms import ProfileForm,PayForm,CreateBillForm,UpdateBillForm
from flask_login import current_user,login_required
from ..models import User,Role,State,Taxbill,Standardtaxrecord,Taxrecord
from .. import db
from ..models import Permission
from ..decorators import permission_required
from datetime import datetime

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

@main.get("/bill/<int:billno>")
@login_required
def bill(billno):
    PayFormObj = PayForm()
    req_bill = current_user.taxbills.filter_by(billnumber=billno).first()
    if(req_bill):
        return render_template('tax_basic.html',req_bill=req_bill,PayFormObj=PayFormObj)
    else:
        flash("requested bill is not found in our records")
        abort(404)

@main.post("/paybill/<int:billno>")
@login_required
def pay_bill(billno):
    PayFormObj = PayForm()
    req_bill = current_user.taxbills.filter_by(billnumber=billno).first()
    if(req_bill):
        if(PayFormObj.validate_on_submit()):
            req_bill.status=4
            db.session.add(req_bill)
            db.session.commit()
            flash("succesfully paid bill number {}".format(req_bill.billnumber))
        else:
            flash("failed to pay bill number {}".format(req_bill.billnumber))
        return redirect(url_for('main.bill',billno=billno))
    else:
        flash("payment failed due to unknown billnumber or not in your records")
        abort(404)

@main.route("/manage")
@login_required
@permission_required(Permission.MODERATE)
def accntnt_view(CreateBillFormObjdata=None):
    CreateBillFormObj=CreateBillForm()
    if(session.get('newbilldata')):
        CreateBillFormObj.billnumber.data=session['newbilldata'].get('billnumber')
        CreateBillFormObj.duedate.data=session['newbilldata'].get('duedate')
        CreateBillFormObj.duedateloc.data=session['newbilldata'].get('duedateloc')
        CreateBillFormObj.pancardNo.data=session['newbilldata'].get('pancardNo')
        CreateBillFormObj.taxable_value.data=session['newbilldata'].get('taxable_value')
        CreateBillFormObj.taxes.data=session['newbilldata'].get('taxes')
        session.pop('newbilldata',None)
    else:
        CreateBillFormObj.duedate.data=datetime.utcnow()
    return render_template("index.html",accntnt_view=True,CreateBillFormObj=CreateBillFormObj)

@main.post('/createbill')
@login_required
@permission_required(Permission.MODERATE)
def create_bill():
    CreateBillFormObj=CreateBillForm()
    if(CreateBillFormObj.validate_on_submit()):
        payer= User.query.filter_by(pancard=CreateBillFormObj.pancardNo.data).first()
        creator = User.query.filter_by(id = current_user.id).first()
        billnumber= CreateBillFormObj.billnumber.data
        taxes = CreateBillFormObj.taxes.data
        taxable_value =  CreateBillFormObj.taxable_value.data
        due_date = CreateBillFormObj.duedate.data
        newbill = Taxbill(payer=payer,creator=creator,billnumber=billnumber,taxable_value=taxable_value,due_date=due_date,status=1)
        for tax in taxes:
            newbill.taxes.append(Standardtaxrecord.query.filter_by(id=int(tax)).first())
        db.session.add(newbill)
        db.session.commit()
        flash("successfully created bill")
    else:
        for i in CreateBillFormObj.errors:
            flash("failed updating due to : " + str(i)\
                +str("   ".join(CreateBillFormObj.errors[i])))
    session['newbilldata']=CreateBillFormObj.data
    return redirect(url_for('main.accntnt_view'))

@main.get('/editbill/<int:billnumber>')
@login_required
@permission_required(Permission.MODERATE)
def edit_bill(billnumber):
    bill = Taxbill.query.filter_by(billnumber = billnumber).first()
    if(bill):
        UpdateBillFormObj = UpdateBillForm(billnumber=billnumber)
        if(session.get("editbillformdata")):
            UpdateBillFormObj.pancardNo.data=session['editbillformdata'].get('pancardNo')
            UpdateBillFormObj.taxes.data=session['editbillformdata'].get('taxes')
            UpdateBillFormObj.taxable_value.data=session['editbillformdata'].get('taxable_value')
            UpdateBillFormObj.duedateloc.data=session['editbillformdata'].get('duedateloc')
            UpdateBillFormObj.duedate.data=session['editbillformdata'].get('duedate')
            session.pop('editbillformdata',None)
        else:
            UpdateBillFormObj.set_data()
        return render_template('tax_basic.html',accntnt_view=True,req_bill=bill,UpdateBillFormObj=UpdateBillFormObj)
    else:
        flash("requested billnumber does nto exist in records")
        abort(404)

@main.post('/updatebill/<int:billnumber>')
@login_required
@permission_required(Permission.MODERATE)
def update_bill(billnumber):
    bill = Taxbill.query.filter_by(billnumber = billnumber).first()
    if(bill):
        if(bill.status==4):
            flash("Cannot update paid bills")
        else:
            UpdateBillFormObj = UpdateBillForm(billnumber=billnumber)
            if(UpdateBillFormObj.validate_on_submit()):
                bill.payer= User.query.filter_by(pancard=UpdateBillFormObj.pancardNo.data).first()
                bill.creator = User.query.filter_by(id = current_user.id).first()
                taxes = UpdateBillFormObj.taxes.data
                bill.taxable_value =  UpdateBillFormObj.taxable_value.data
                bill.due_date = UpdateBillFormObj.duedate.data
                old_taxes = bill.taxes.all()
                for tax in taxes:
                    taxrec=Standardtaxrecord.query.filter_by(id=int(tax)).first()
                    if(taxrec not in old_taxes):
                        bill.taxes.append(taxrec)
                db.session.add(bill)
                db.session.commit()
                flash("updated sucessfully")
            session['editbillformdata']=UpdateBillFormObj.data
        return redirect(url_for('main.edit_bill',billnumber=billnumber))
    else:
        flash("requested billnumber does nto exist in records")
        abort(404)