from flask import Flask,flash,abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_,and_
from extensions import *
import datetime
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

from flask_login import LoginManager, login_user, logout_user, current_user, login_required
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
            elif user.is_approved==False:
                logout_user()
                flash("You are blacklisted for malicious activity","danger")
            else:
                flash('Invalid Credentials',"danger")

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
        company=Company_Profiles(user_id=user.id,company_name=request.form["company_name"],approval_status="pending",hr_number=request.form["hr_num"],website_url=request.form["website_url"],description=request.form.get('description'))
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
    pending_drives = Placement_Drives.query.filter_by(drive_status='pending').count()
    ongoing_drives = Placement_Drives.query.filter_by(drive_status='active').count()
    total_applications = Applications_Table.query.count()
    return render_template('admin/admin_dashboard.html',students=students,total_companies=total_companies,total_students=total_students,unapproved_companies=unapproved_companies,
                           pending_drives=pending_drives,ongoing_drives=ongoing_drives,total_applications=total_applications)

#navbar link to companies page
@app.route('/admin_dashboard/companies')
@login_required
def admin_comp():
    q=request.args.get("q")
    if q:
        com_apply=Company_Profiles.query.filter(Company_Profiles.approval_status=="pending",
                                                or_(Company_Profiles.company_name.ilike(f"{q}%"))).all()
        com = Company_Profiles.query.filter(
        Company_Profiles.approval_status == "approved",or_(
            Company_Profiles.company_name.ilike(f"{q}%"))).all()
    
    else:
        com_apply=Company_Profiles.query.filter_by(approval_status="pending").all()
        com=Company_Profiles.query.filter_by(approval_status="approved").all()
    return render_template("admin/companies.html",com_apply=com_apply,com=com)

#navbar link to students page
@app.route("/admin_dashboard/students")
@login_required
def admin_students():
    q=request.args.get('q')
    if q:
        students=Student_Profiles.query.filter(or_(Student_Profiles.first_name.ilike(f"{q}%"),Student_Profiles.last_name.ilike(f"{q}%"),
                                                   Student_Profiles.department_name.ilike(f"{q}%")
                                                   )
                                                   ).all()
    else:
        students=Student_Profiles.query.all()
    return render_template("admin/students.html",Students=students)

#navbar link to drives link
@app.route("/admin_dashboard/drives")
@login_required
def admin_drives():
    pending=Placement_Drives.query.filter_by(drive_status="pending")
    active=Placement_Drives.query.filter_by(drive_status="active")
    closed=Placement_Drives.query.filter_by(drive_status="closed")
    rejected=Placement_Drives.query.filter_by(drive_status="rejected")

    return render_template("admin/drives.html",pending=pending,active=active,closed=closed,rejected=rejected)
#functions for drive management
@app.route("/admin_dashboard/drives/approve/<int:d_id>")
@login_required
def approve_drive(d_id):
    if current_user.role!="admin":
        return "Unauthorized",403
    drive=Placement_Drives.query.get(d_id)
    if drive:
        drive.drive_status="active"
        db.session.commit()
        flash("A Drive Started","success")
    else:
        flash("invalid operation","information")
    return redirect(url_for("admin_drives"))

@app.route("/admin_dashboard/drives/reject/<int:d_id>")
@login_required
def reject_drive(d_id):
    if current_user.role!="admin":
        return "Unauthorized",403
    drive=Placement_Drives.query.get(d_id)
    if drive:
        drive.drive_status="rejected"
        db.session.commit()
        flash("A Drive Rejected","danger")
    else:
        flash("invalid operation","information")
    return redirect(url_for("admin_drives"))
    


#navbar link to job applications
@app.route("/admin_dashboard/applications")
@login_required
def admin_applications():
    applications = Applications_Table.query.all()

    return render_template("admin/applications.html", applications=applications)

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

    return redirect(url_for("admin_comp"))

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
        return redirect(url_for("admin_comp"))

#blacklist button
@app.route("/admin/blacklist_user/<int:user_id>")
def blacklist_user(user_id):
    user=User.query.get(user_id)
    user.is_approved=False
    db.session.commit()
    flash("User Blacklisted!!","danger")
    return redirect(request.referrer)

#whitelist
@app.route("/admin/whitelist_user/<int:user_id>")
def whitelist_user(user_id):
    user=User.query.get(user_id)
    user.is_approved=True
    db.session.commit()
    flash("User Whitelisted!!","information")
    return redirect(request.referrer)




#-----------------------------------------------------Student-------------------------------

#this route for redirecting us to the student dashboard and processing the applications and active drive status
@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role!='student':
        abort(403)
    #this will give us the active drives.
    drives= Placement_Drives.query.filter_by(drive_status="active").all()
    print(drives)
    #we also want to show the registered application the current student did , toh pehle ham ek variable mai uss student ki user_id lenge and then filter out his application
    student_profile=current_user.student_profiles
    applications=Applications_Table.query.filter_by(student_id=student_profile.user_id).all()

    # the very first table will be made of the companies so use that to maek the very first tables
    """ the reason why we are using join is that it will only gives those companies 
    which have a drive under there name else it wont be shown to us  """
    companies=Company_Profiles.query.join(Placement_Drives).filter(Placement_Drives.drive_status=="active").distinct().all()



    return render_template('student/student_dashboard.html',drives=drives,applications=applications,companies=companies)

#View Company page routing :
def is_profile_complete(student):
    return bool(
        student and
        student.first_name and
        student.last_name and
        student.cgpa is not None and
        student.department_name and
        student.graduation_year and
        student.resume_path
    )



#Viewing company and then being applied
@app.route('/student_dashboard/view_company/<int:company_id>')
@login_required
def view_company(company_id):
    if current_user.role != 'student':
        abort(403)

    company = Company_Profiles.query.get_or_404(company_id)
    com_drives = Placement_Drives.query.filter_by(
        company_id=company.user_id,
        drive_status="active").all()
    profile_complete = is_profile_complete(current_user.student_profiles)
    if not profile_complete:
        flash("Please complete your profile before applying to drives.", "warning")
    return render_template('student/view_com.html',company=company,drives=com_drives,profile_complete=profile_complete)

@app.route('/student_dashboard/view_company/<int:drive_id>')
@login_required
def view_drive(drive_id):
    drives=Placement_Drives.query.get_or_404(drive_id)

    return render_template('student/view_drive')

#Route for editing student profiles
@app.route('/student_dashboard/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_sprofile():
    student = Student_Profiles.query.get(current_user.id)

    if request.method == 'POST':
        student.first_name = request.form.get('first_name')
        student.last_name = request.form.get('last_name')
        student.cgpa = request.form.get('cgpa')
        student.department_name = request.form.get('department_name')
        student.graduation_year = request.form.get('graduation_year')

        # handle file upload
        file = request.files.get('resume')
        if file and file.filename:
            filepath = os.path.join('static/resumes', file.filename)
            file.save(filepath)
            student.resume_path = filepath

        db.session.commit()
        flash("Profile Updated","success")

        return redirect(url_for('student_dashboard'))
    

    return render_template('student/edit.html', student=student)


#route for the student to apply

@app.route('/apply/<int:drive_id>', methods=['POST'])
@login_required
def apply(drive_id):
    student_profile = current_user.student_profiles
    if not is_profile_complete(student_profile):
        flash("Please complete your profile before applying.", "warning")
        return redirect(url_for('edit_sprofile'))

    student_id = student_profile.user_id

    existing = Applications_Table.query.filter_by(
        student_id=student_id,
        drive_id=drive_id
    ).first()

    if existing:
        flash("Already applied","warning")
        return redirect(url_for('student_dashboard'))

    application = Applications_Table(
        student_id=student_id,
        drive_id=drive_id,
        status="applied"
    )

    db.session.add(application)
    db.session.commit()

    return redirect(url_for('student_dashboard'))









#----------------------Company-------------------------

@app.route('/company_dashboard')
@login_required
def company_dashboard():
    # Show company dashboard with separate upcoming and closed drives
    if current_user.role != 'company':
        abort(403)

    company_id = current_user.id
    upcoming_drives = Placement_Drives.query.filter(
        Placement_Drives.company_id == company_id,
        Placement_Drives.drive_status != 'closed'
    ).all()
    closed_drives = Placement_Drives.query.filter_by(
        company_id=company_id,
        drive_status='closed'
    ).all()

    return render_template(
        'company/company_dashboard.html',
        company_id=company_id,
        upcoming_drives=upcoming_drives,
        closed_drives=closed_drives
    )

@app.route('/company_dashboard/drive/<int:drive_id>')
@login_required
def company_drive_details(drive_id):
    # Show a single drive's details and received applications
    if current_user.role != 'company':
        abort(403)

    drive = Placement_Drives.query.get_or_404(drive_id)
    if drive.company_id != current_user.id:
        abort(403)

    applications = drive.applications.all()
    return render_template('company/drive_details.html', drive=drive, applications=applications)

@app.route('/company_dashboard/application/<int:app_id>/status', methods=['POST'])
@login_required
def update_application_status(app_id):
    # Update application status (only for company that owns the drive)
    if current_user.role != 'company':
        abort(403)
    
    application = Applications_Table.query.get_or_404(app_id)
    drive = application.drive
    
    if drive.company_id != current_user.id:
        abort(403)
    
    new_status = request.form.get('status')
    if new_status in ['applied', 'shortlisted', 'selected', 'rejected']:
        application.status = new_status
        db.session.commit()
        flash(f"Application status updated to {new_status}", "success")
    else:
        flash("Invalid status", "danger")
    
    return redirect(url_for('company_drive_details', drive_id=drive.id))



@app.route("/company_dashboard/create_drive/<int:company_id>",methods=['GET','POST'])
@login_required
def create_drive(company_id):
    if request.method=='POST':
        drive=Placement_Drives(drive_name=request.form.get('drive_name'),
                               job_title=request.form.get('job_title'),
                               job_type=request.form.get('job_type'),
                               cgpa=float(request.form.get('cgpa')),
                               description=request.form.get('description'),
                               application_deadline=datetime.datetime.strptime(request.form.get('application_deadline'), "%Y-%m-%d").date(),
                               location=request.form.get('location'),
                               ctc=float(request.form.get('ctc')),
                               company_id=company_id)
                               #adding company id from current_user
                               
        db.session.add(drive)
        db.session.commit()
        flash("Drive Created Successfully","success")
        return redirect(url_for('company_dashboard'))
    return render_template("company/create_drive.html",company_id=company_id)


#Function to activate or deactivate a drive by the company and delete drive
@app.route('/company_dashboard/toggle_status/<int:drive_id>', methods=['POST'])
@login_required
def toggle_drive_status(drive_id):
    # Company may only close active drives; admin activation is handled separately.
    if current_user.role != 'company':
        abort(403)
    drive = Placement_Drives.query.get_or_404(drive_id)
    if drive.company_id != current_user.id:
        abort(403)
    if drive.drive_status == 'active':
        drive.drive_status = 'closed'
        db.session.commit()
        flash("Drive closed successfully", "success")
    else:
        flash("Only active drives can be closed by the company", "warning")
    return redirect(url_for('company_dashboard'))

@app.route('/admin_dashboard/drives/close/<int:d_id>')
@login_required
def close_drive(d_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    drive = Placement_Drives.query.get(d_id)
    if drive and drive.drive_status == 'active':
        drive.drive_status = 'closed'
        db.session.commit()
        flash("Drive closed successfully", "success")
    else:
        flash("Only active drives can be closed", "warning")
    return redirect(url_for('admin_drives'))

#------------------------------Navbar------------------------------
#logout button
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__=='__main__':
    app.run(debug=True)
