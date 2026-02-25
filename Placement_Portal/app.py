from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import render_template, request,redirect,url_for,session

app=Flask(__name__)

#database configuration

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.secret_key='123'

db=SQLAlchemy(app)