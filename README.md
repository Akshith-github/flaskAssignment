# flaskAssignment for RedCarpetUp

to Run sample testcases change the FLASK_CONFIG environment variable value in dockerfile to "testing" and run.

Features developed:
  1 taxpayer can list view , filter taxes and pay tax bills.
  2 tax accountant an create tax like CGST, SGST,state taxes managemnt and tax bills to all users.
    Also : i) create tax bills
            ii) edit unpaid tax bills
  3 admin can access each detials and modify each details through flask admin feature.

Major Flask extensions used:
  1) FLask Sqlalchmey-alembic-migrate features are used to handle database migration and rollbacks.
  2) For user details api HTTPAuth is used, normal login is managed with flask login extension that creates sessions.
  3) To keep the paid bills not modified on modification of taxes , database is designed such paid taxbills are mapped to old tax record that arre assoc iated to it.
  
