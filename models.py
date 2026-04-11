from sqlalchemy import Integer
from extensions import db
import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash

class User(db.Model,UserMixin):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True,nullable=False,unique=True)
    email=db.Column(db.String(150),unique=True,nullable=False,index=True)
    password=db.Column(db.String(150),nullable=False)
    role=db.Column(db.String(150),nullable=False)
    is_active=db.Column(db.Boolean,default=True)
    is_approved=db.Column(db.Boolean,default=True,nullable=True)
    is_blacklisted=db.Column(db.Boolean,default=False,nullable=True)
    created_at=db.Column(db.DateTime,default=datetime.datetime.utcnow)
    #Making connection with student profiles and company profiles
    student_profiles=db.relationship('Student_Profiles',backref='user',uselist=False)
    company_profiles=db.relationship('Company_Profiles',backref='user',uselist=False)
    #making the hashing part of the model for initialising the password and making it 
    def set_password(self,password):
        self.password=generate_password_hash(password)
    def check_password(self,password):
        return check_password_hash(self.password,password)

class Student_Profiles(db.Model):
    __tablename__='student_profiles'
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True,nullable=False,unique=True)
    first_name=db.Column(db.String(150),nullable=False)
    last_name=db.Column(db.String(150),nullable=False)
    cgpa=db.Column(db.Float,nullable=False)
    department_name=db.Column(db.String(150),nullable=False)
    graduation_year=db.Column(db.Integer,nullable=False)
    resume_path = db.Column(db.String(300), nullable=True)
    applications = db.relationship('Applications_Table',backref='student',lazy=True)
    #should have a relationship with Users

class Company_Profiles(db.Model):
    __tablename__='company_profiles'
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True,nullable=False,unique=True)
    description=db.Column(db.Text,nullable=False)
    company_name=db.Column(db.String(150),nullable=False,unique=True,index=True)
    hr_number=db.Column(db.String(150),nullable=False)
    website_url = db.Column(db.String(300), nullable=True)
    approval_status=db.Column(db.Enum('pending','approved','rejected',name="approval_status"),nullable=False,default='pending')
    #Relationship between comapny_profiles and placement drives (in simple ForeignKey attribute we use the table name and in the relationship we use the class name)
    drives=db.relationship('Placement_Drives',backref='company',lazy=True)

class Placement_Drives(db.Model):
    __tablename__='placement_drives'
    #columns taken by form
    drive_name=db.Column(db.String(150),unique=False,nullable=False)
    job_title=db.Column(db.String(100),nullable=False)
    job_type=db.Column(db.Enum("Internship","Fulltime","Apprenticeship",name="job_type"),nullable=False)
    cgpa=db.Column(db.Float,nullable=False)
    description=db.Column(db.Text,nullable=False)
    application_deadline=db.Column(db.Date,nullable=False,index=True)
    location=db.Column(db.String(100))
    ctc=db.Column(db.Float,nullable=False)
    id=db.Column(db.Integer,primary_key=True,unique=True)
    #managed by backend
    company_id=db.Column(db.Integer,db.ForeignKey('company_profiles.user_id'),nullable=False,index=True)
    drive_status=db.Column(db.Enum('pending','active','closed','rejected',name="drive_status"),nullable=False,default='pending',index=True)
    applications = db.relationship('Applications_Table',backref='drive',lazy="dynamic")
    

class Applications_Table(db.Model):
    __tablename__='applications_table'
    id=db.Column(db.Integer,primary_key=True)
    student_id=db.Column(db.Integer,db.ForeignKey('student_profiles.user_id'))
    drive_id=db.Column(db.Integer,db.ForeignKey('placement_drives.id'))
    applied_at=db.Column(db.DateTime,default=datetime.datetime.utcnow)
    status=db.Column(db.Enum('applied','shortlisted','selected','rejected',name='status'),nullable=False,default="applied")
    #Constraint to ensure a student can apply only once to a particular drive
    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id'),)

#Done with the models now, establish relations