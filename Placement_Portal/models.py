from sqlalchemy import Integer
from app import db
import datetime

class User(db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True,nullable=False,unique=True)
    email=db.Column(db.String(150),unique=True,nullable=False,index=True)
    password=db.Column(db.String(150),nullable=False)
    role=db.Column(db.String(150),nullable=False)
    is_active=db.Column(db.Boolean,default=True)
    is_approved=db.Column(db.Boolean,default=True,nullable=True)
    created_at=db.Column(db.DateTime,default=datetime.datetime.utcnow())
    #Making connection with student profiles and company profiles
    student_profiles=db.relationship('Student_Profiles',backref='user',uselist=False)
    company_profiles=db.relationship('Company_Profiles',backref='user',uselist=False)

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
    company_name=db.Column(db.String(150),nullable=False,unique=True,index=True)
    hr_name=db.Column(db.String(150))
    website_url = db.Column(db.String(300), nullable=True)
    approval_status=db.Column(db.String(100),nullable=True)
    #Relationship between comapny_profiles and placement drives (in simple ForeignKey attribute we use the table name and in the relationship we use the class name)
    drives=db.relationship('Placement_Drives',backref='company',lazy=True)

class Placement_Drives(db.Model):
    __tablename__='placement_drives'
    id=db.Column(db.Integer,primary_key=True,unique=True)
    job_title=db.Column(db.String(100),nullable=True)
    company_id=db.Column(db.Integer,db.ForeignKey('company_profiles.user_id'),nullable=False)
    description=db.Column(db.String(150),nullable=True)
    ctc_package=db.Column(db.Float,nullable=False)
    application_deadline=db.Column(db.DateTime)
    status=db.Column(db.String(150))

    rules=db.relationship('Drive_Eligibility_Rules',backref='drive',uselist='False')
    applications = db.relationship('Applications_Table',backref='drive',lazy=True)
    
class Drive_Eligibility_Rules(db.Model):
    __tablename__='drive_eligibility_rules'
    drive_id=db.Column(db.Integer,db.ForeignKey('placement_drives.id'),primary_key=True)
    min_cgpa=db.Column(db.Float,nullable=False)
    allowed_departments=db.Column(db.String(150))
    #make relationships

class Applications_Table(db.Model):
    __tablename__='applications_table'
    id=db.Column(db.Integer,primary_key=True)
    student_id=db.Column(db.Integer,db.ForeignKey('student_profiles.user_id'))
    drive_id=db.Column(db.Integer,db.ForeignKey('placement_drives.id'))
    applied_at=db.Column(db.DateTime,default=datetime.datetime.utcnow)
    status=db.Column(db.String(150))

#Done with the models now, establish relations