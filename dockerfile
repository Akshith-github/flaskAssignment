FROM python:slim

#add user
RUN useradd  flaskassignment
#create directory 
WORKDIR /home/FlaskAssignment
COPY flasky.py config.py boot.sh postgress200.sh ./
# RUN chmod a+x postgress200.sh
# RUN apk add build-base
#copy source files
COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip3 install -r requirements.txt
RUN venv/bin/pip3 install gunicorn pymysql 
# cryptography

COPY app app
COPY migrations migrations

RUN chmod a+x boot.sh

# set environmentvariables
ENV FLASK_APP flasky.py
ENV FLASK_CONFIG docker

RUN chown -R flaskassignment:flaskassignment ./
USER flaskassignment

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
