# flaskAssignment for RedCarpetUp #

## Building DOcker Image ##
Run the below command to build the Docker image corresponding this repo.
> docker build -t flaskassgn .


## Running test cases ##
To run sample testcasespass FLASK_CONFIG environment variable value as "testing" in docker run command.
> docker run --rm -it -e FLASK_CONFIG=testing flaskassgn

## Running production environment
To run in production mode , pass the following environment variables:
  1. *FLASK_CONFIG====>"docker"
  2. *FLASK_ADMIN====> adminmailid (e.g admin@gmail.com) [for admin account]
  3. *SECRET_KEY   ====>  some random 
  4. MAIL_USERNAME===> mail used to send login related mails to users
  5. MAIL_PASSWORD ==> password related to MAIL_USERNAME account.
>docker run --rm -it -p 8000:5000 -e SECRET_KEY=57d40f677aff4d8d96df97223c74d217 -e MAIL_USERNAME=mail@gmail.com -e MAIL_PASSWORD=mailpassword flaskassgn -e FLASK_ADMIN=admin@me.com -e FLASK_CONFIG=docker

**open http://localhost:8000/**
---
## Features developed: ##
  1) taxpayer can list view , filter taxes and pay tax bills with taxes related to only their states.
  2) tax accountant an create tax like CGST, SGST,state taxes managemnt and tax bills to all users.
    Also : 
      1) create tax bills
      2) edit unpaid tax bills
  3) admin can access each detials and modify each details through flask admin feature.
----------
## Major Flask extensions used:
  1) **_FLask Sqlalchmey_-_alembic_-_flask-migrate_** features are used to handle database migration and rollbacks.
  2) For user details api **_HTTPAuth_** is used, normal login is managed with flask login extension that creates sessions.
  3) To keep the paid bills not modified on modification of taxes , database is designed such paid taxbills are mapped to old tax record that arre assoc iated to it.
  4) FlaskWtfforms and Flask-Moment are major in rendering point of view.
  ----------
