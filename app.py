from flask import Flask,flash
from flask_sqlalchemy import SQLAlchemy
from extensions import *
from datetime import datetime
from flask import render_template, request,redirect,url_for,session
from models import *
import os
from werkzeug.utils import secure_filename

app=Flask(__name__)

#database configuration

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.secret_key='123'

#db initialization 
db.init_app(app)

from flask_login import LoginManager
login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view="login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#----------------------------------------Auth Routes-------------------------------------------------------------------

@app.route('/')
def home():
    return render_template('auth/home.html')


@app.route('/login',methods=["GET","POST"])
def login():
    if request.method=="POST":
        #Take the info from the form and save it in the variables.
        email=request.form["email"]
        password=request.form["password"]
        #now use the email and password to verify whether the given user is in the database or not!!
        

        user=User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.role=="company" and not user.is_approved:
                flash("Company verification is under process !! Please Try Again later.","warning")
                return redirect(url_for("login"))
            login_user(user)
            if user.role=="admin":
                login_user(user)
                flash("Logged in!!","success")
                return redirect(url_for("admin_dashboard"))
            
            elif user.role == "company" and user.is_approved==True:
                login_user(user)
                flash("Logged in!!","success")
                return redirect(url_for("company_dashboard"))
            elif user.role == "student" and user.is_approved==True:
                login_user(user)
                flash("Logged in!!","success")
                return redirect(url_for("student_dashboard"))
            else:
                logout_user()
                flash("You are blacklisted for malicious activity","danger")

    return render_template('auth/login.html')


@app.route('/company_reg',methods=["POST","GET"])
def company_reg():
    if request.method=="POST":
        #separate out imp info for the user table which is email,password and user
        email=request.form["email"]
        password=request.form["password"]
        user=User(email=email,role="company",is_approved=False)
        user.set_password(password)   #this set password is the function we made under the user function to make the password hashable and then store it
        db.session.add(user)
        db.session.flush()
        company=Company_Profiles(user_id=user.id,company_name=request.form["company_name"],approval_status="pending",hr_number=request.form["hr_num"],website_url=request.form["website_url"])
        db.session.add(company)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template('auth/company_reg.html')


@app.route('/student_reg',methods=["GET","POST"])
def student_reg():
    #First make a path to store all the info in the database.
    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"]
        resume = request.files["resume"]

        user=User(email=email,role="student",is_approved=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        #flush gives user.id before commit

        UPLOAD_FOLDER = "static/resumes"
        app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
        

        #This is the setup for saving the resume for the student's resume
        filename = None
        if resume and resume.filename != "":
            filename = secure_filename(resume.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            resume.save(filepath)

        
        student=Student_Profiles(user_id=user.id,
                                 first_name=request.form["first_name"],
                                 last_name=request.form["last_name"],cgpa=float(request.form["cgpa"]) if request.form["cgpa"] else None,
                                 department_name=request.form["department_name"],
                                 graduation_year=request.form["graduation_year"],
                                 resume_path= filepath if filename else None)
        db.session.add(student)
        db.session.commit()
        return redirect(url_for("login"))
    
    return render_template('auth/student_reg.html')

#--------------------------------------------Admin-------------------------------------------------------------
#Routes to take you to the dashboards
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return "Unauthorized",403
    #In this admin dashboard when we will call it it will run some functions which will give us the names of different categories
    students=Student_Profiles.query.all()
    
    #To get the total number of fields at the home page
    total_companies = Company_Profiles.query.filter_by(approval_status="approved").count()
    total_students = User.query.filter_by(role='student').count()
    unapproved_companies = Company_Profiles.query.filter_by(approval_status="pending").count()
    pending_drives = Placement_Drives.query.filter_by(status='pending').count()
    ongoing_drives = Placement_Drives.query.filter_by(status='active').count()
    total_applications = Applications_Table.query.count()
    return render_template('admin/admin_dashboard.html',students=students,total_companies=total_companies,total_students=total_students,unapproved_companies=unapproved_companies,
                           pending_drives=pending_drives,ongoing_drives=ongoing_drives,total_applications=total_applications)


@app.route('/admin_dashboard/companies')
@login_required
def admin_comp():
    com_apply=Company_Profiles.query.filter_by(approval_status="pending")
    com=Company_Profiles.query.filter_by(approval_status="approved")

    return render_template("admin/companies.html",com_apply=com_apply,com=com)

#Button for admin authorization of company
@app.route("/admin/approve/<int:company_id>")
@login_required
def approve_company(company_id):

    if current_user.role != "admin":
        return "Unauthorized", 403

    company = Company_Profiles.query.get(company_id)

    if company:
        company.approval_status = "approved"
        company.user.is_approved = True   # if you also store it in users table
        db.session.commit()

    return redirect(url_for("admin_dashboard"))

#Button for admin rejection
@app.route("/admin/reject_company/<int:company_id>")
@login_required
def reject_company(company_id):
    if current_user.role !="admin":
        return "Unauthorized",403
    company=Company_Profiles.query.get(company_id)
    if company:
        company.approval_status="rejected"
        db.session.commit()
        flash("Company Rejected Successfully","danger")
        return redirect(url_for("admin_dashboard"))

#blacklist button
@app.route("/admin/blacklist_user/<int:user_id>")
def blacklist_user(user_id):
    user=User.query.get(user_id)
    user.is_approved=False
    db.session.commit()
    return redirect(request.referrer)




#-----------------------------------------------------Student-------------------------------
@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student/student_dashboard.html')








#----------------------Company-------------------------
@app.route('/company_dashboard')
def company_dashboard():
    return render_template('company/company_dashboard.html')





#------------------------------Navbar------------------------------
#logout button
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__=='__main__':
    app.run(debug=True)
