from flask import Flask,render_template,request,redirect,make_response
from flask_restful import Resource,Api,fields,marshal_with,reqparse
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException
import json

from Lab_assignments.Week5.app import enrollments, student

#-------Configurations----------------

app= Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
db= SQLAlchemy()
db.init_app(app)
app.init_app(app)
app.app_context().push()
api= Api(app)



#------Models----------------------



class Student(db.Model):
    __tablename__= 'student'
    student_id= db.Column(db.Integer,primary_key=True)
    roll_number= db.Column(db.String(100),unique=True,nullable=False)
    first_name= db.Column(db.String(100),nullable=False)
    last_name= db.Column(db.String(100),nullable=False)
    courses=db.relaionship("Course",backref="student",secondary="enrollment",cascade="all,delete")

class Course(db.Model):
    __tablename__= 'course'
    course_id= db.Column(db.Integer,primary_key=True)
    course_code=db.Column(db.String(100),unique=True,nullable=False)
    course_name=db.Column(db.String(100),nullable=False)
    course_description=db.Column(db.String(100))

class Enrollment(db.Model):
    __tablename__= 'enrollment'
    enrollment_id= db.Column(db.Integer,primary_key=True)
    student_id= db.Column(db.Integer,db.ForeignKey('student.student_id'),nullable=False)
    course_id= db.Column(db.Integer,db.ForeignKey('course.course_id'),nullable=False)
#----------Exception Handling----------------

class FoundError(HTTPException):
    def __init__(self,status_code,message=''):
        self.response=make_response(message,status_code)

class NotGivenError(HTTPException):
    def __init__(self,status_code,error_code,error_message):
        message={
            "error_code":error_code,
            "error_message":error_message
        }
        self.response=make_response(json.dumps(message),status_code)

#----------Output Fields----------------

student_fields={
    'student_id':fields.Integer,
    'roll_number':fields.String,
    'first_name':fields.String,
    'last_name':fields.String
}
course_fields={
    'course_id':fields.Integer,
    'course_code':fields.String,
    'course_name':fields.String,
    'course_description':fields.String
}


#---------Request Parsers----------------
student_parse=reqparse.RequestParser()
student_parse.add_argument('first_name')
student_parse.add_argument('last_name')
student_parse.add_argument('roll_number')

course_parse=reqparse.RequestParser()
course_parse.add_argument('course_code')
course_parse.add_argument('course_name')
course_parse.add_argument('course_description')

enrollment_parse=reqparse.RequestParser()
enrollment_parse.add_argument('course_id')

#----------APIs---------


class CourseAPI(Resource):
    
    #GET DETAILS OF A COURSE
    @marshal_with(course_fields)
    def get(self,course_id):
        course= Course.query.filter_by(course_id=course_id).first()
        if not course:
            raise FoundError(404,"Course not found")
        return course

#EDIT COURSE

@marshal_with(course_fields)
def put(self,course_id):
    #check given courseid is present or not
    course= Course.query.filter_by(course_id=course_id).first()
    if course is None:
        raise FoundError(404,"Course not found")
    #if present take arguments
    args= course_parse.parse_args()
    course_name=args.get('course_name',None)
    course_code=args.get('course_code',None)
    course_description=args.get('course_description',None)

    #if name is not given as an argument then raise an error as name is mandatory
    if course_name is None:
        raise NotGivenError(status_code=400,error_code="COURSE001",error_message="Course name is required")
    
    #if code is not given as an argument then raise an error as code is mandatory
    if course_code is None:
        raise NotGivenError(status_code=400,error_code="COURSE002",error_message="Course code is required")
    
    #EVERYTHING IS FINE THEN UPDATE THE DETAILS
    else:
        course.course_name= course_name
        course.course_code= course_code
        course.course_description= course_description
        db.session.add(course)
        db.session.commit()
        return course
#delete a course
def delete(self,course_id):
    course= Course.query.filter(course_id==course_id).scalar()
    if course is None:
        raise FoundError(404,"Course not found")
    db.session.delete(course)
    db.session.commit()
    return '',204

#add a course
@marshal_with(course_fields)
def post(self):
    #take arguments
    args= course_parse.parse_args()
    course_name=args.get('course_name',None)
    course_code=args.get('course_code',None)
    course_description=args.get('course_description',None)
    #check whether name is empty or not
    if course_name is None:
        raise NotGivenError(status_code=400,error_code="COURSE001",error_message="Course name is required")
    #check whether code is empty or not
    if course_code is None:
        raise NotGivenError(status_code=400,error_code="COURSE002",error_message="Course code is required")
    #CHECK WHETHER ANY COURSE WITH SAME CODE IS PRESENT OR NOT
    course= Course.query.filter(course_code==course_code).first()
    #if not add the course
    if course is None:
        course= Course(course_name=course_name,course_code=course_code,course_description=course_description)
        db.session.add(course)
        db.session.commit()
        return course,201
    #otherwise raise an error that course with same code is present
    else:
        raise FoundError(409,"Course with same code already exists")
    
class StudentAPI(Resource):
    #GET DETAILS OF A STUDENT
    @marshal_with(student_fields)
    def get(self,student_id):
        student= Student.query.filter(student_id==student_id).first()
        if not student:
            raise FoundError(404,"Student not found")
        return student
    #EDIT STUDENT DETAILS

    @marshal_with(student_fields)
    def put(self,student_id):
        student= Student.query.filter(student_id==student_id).first()
        if student is None:
            raise FoundError(404,"Student not found")
    #if present take arguments
        args= student_parse.parse_args()
        first_name=args.get('first_name',None)
        last_name=args.get('last_name',None)
        roll_number=args.get('roll_number',None)
    #if roll_number is not given as an argument then raise an error as roll_number is mandatory
        if roll_number is None:
            raise NotGivenError(status_code=400,error_code="STUDENT001",error_message="Roll number is required")
    #if first_name is not given as an argument then raise an error as first_name is mandatory
        if first_name is None:
            raise NotGivenError(status_code=400,error_code="STUDENT002",error_message="First name is required")
    #everything is fine then update the details
        else:
            student.first_name= first_name
            student.last_name= last_name
            student.roll_number= roll_number
            db.session.add(student)
            db.session.commit()
            return student

#delete a student
    def delete(self,student_id):
        student= Student.query.filter(student_id==student_id).scalar()
        if student is None:
            raise FoundError(404,"Student not found")
        db.session.delete(student)
        db.session.commit()
        return '',200

#add a student
@marshal_with(student_fields)
def post(self):
    #take arguments
    args= student_parse.parse_args()
    first_name=args.get('first_name',None)
    last_name=args.get('last_name',None)
    roll_number=args.get('roll_number',None)
    #check whether first name is empty or not
    if first_name is None:
        raise NotGivenError(status_code=400,error_code="STUDENT002",error_message="First name is required")
    #check whether roll number is empty or not
    if roll_number is None:
        raise NotGivenError(status_code=400,error_code="STUDENT001",error_message="Roll number is required")
    #CHECK WHETHER ANY STUDENT WITH SAME ROLL NUMBER IS PRESENT OR NOT
    student= Student.query.filter(roll_number==roll_number).first()
    #if not add the student
    if student is None:
        student= Student(first_name=first_name,last_name=last_name,roll_number=roll_number)
        db.session.add(student)
        db.session.commit()
        return student,201
    #otherwise raise an error that student with same roll number is present
    else:
        raise FoundError(409,"Student with same roll number already exists")

class EnrollmentAPI(Resource):
#get the list of enrollments of a student
    def get (self,student_id):
    #check whether student is valid or not
        student= Student.query.filter(student_id==student_id).first()
        if student is None:
            raise NotGivenError(status_code=400,error_code="ENROLLMENT002",error_message="Student does not exist")
    #check whehter student id is present or not
        enrollments= Enrollment.query.filter(student_id==student_id).all()
    #if present,do followings
        if enrollments:
            enrolls=[]
        #loop runs for each allotment
            for enrollement in enrollments:
                enrolls.append({
                "enrollment_id":enrollement.enrollment_id,"student_id":enrollement.student_id,"course_id":enrollement.course_id})
            return enrolls
    #if student is not present then raise an error
        else:
            raise FoundError(404,"Enrollment not found")
    
#add student enrollment
def post(self,student_id):
    #check whether student id is present or not
    student= Student.query.filter(student_id==student_id).first()
    
