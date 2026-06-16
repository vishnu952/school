from pymongo import MongoClient
from dotenv import load_dotenv
import os, certifi, shutil
from email.mime.text import MIMEText
import smtplib
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request ,Form,UploadFile,File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from pathlib import Path
from typing import List
import random
from datetime import datetime, timedelta
import string
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from pydantic import BaseModel

# Calculate project root path
BASE_DIR = Path(__file__).resolve().parent.parent

# Explicitly load .env from the project root to ensure variables are found
# Load .env from the same directory as this file (backend folder)
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

app = FastAPI()

# Security
SECRET = os.getenv("secret_key")
ALGORITHM = os.getenv("algorithms")

# Admin Login
A_USERNAME = os.getenv("user_name")
A_PASSWORD = os.getenv("passward")

# Email Configuration
SENDER_EMAIL = os.getenv("senderemail")
APP_PASSWORD = os.getenv("passkey")
RECEIVER_EMAIL = os.getenv("receiver_email")

# SMTP Configuration
SMTP_HOST = os.getenv("host")
SMTP_PORT = int(os.getenv("port"))

IS_admin_logged_in = False

otp_storage = {} # In-memory storage for OTPs (for demonstration purposes only)
app.add_middleware(SessionMiddleware, secret_key = SECRET )
errors={}
ca = certifi.where()
client = MongoClient(os.getenv("connectdb"),tlsCAFile=ca, serverSelectionTimeoutMS=5000)

# Initialize database and collections regardless of existence check to avoid startup crash
db = client.get_database("school")
fed = db.get_collection("feedbacks")
add = db.get_collection("addmissions")
con = db.get_collection("contacts")
gal = db.get_collection("gallery")
sl = db.get_collection("student_life")
hv = db.get_collection("home_video")
vis = db.get_collection("visitors")

try:
    # Attempt to verify the connection and check for existing DB
    db_names = client.list_database_names()
    if "school" in db_names:
        print("Connected to existing 'school' database.")
except Exception as e:
    print(f"Warning: Could not connect to MongoDB Atlas during startup: {e}")
    print("Check if your current IP address is whitelisted in the MongoDB Atlas 'Network Access' tab.")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# directing to directories
template = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "pages"))
template.env.cache = None
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")

class Phone(BaseModel):
    phone_number: str
class VerifyOTP(BaseModel):
    phone_number: str
    otp: str
def generate_otp():
    return str(random.randint(100000, 999999))

def send_email_otp(otp):
    msg = MIMEText(f"Your OTP is: {otp}")

    msg["Subject"] = "Admin Login OTP"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()

    server.login(SENDER_EMAIL, APP_PASSWORD)

    server.send_message(msg)

    server.quit()
    return{"message": "OTP Sent Successfully"}


@app.get("/ADMIN")
async def admin_login_get(request: Request):
    return template.TemplateResponse(
        request=request,
        name="admin.html",
        context={}
    )

@app.post("/school-admin")
def school_admin(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    otp: str = Form(...)
):
    if (
        username == A_USERNAME
        and password == A_PASSWORD
        and otp == request.session.get("admin_login_otp")
    ):
        request.session["is_admin"] = True
        Is_admin_logged_in = True
        request.session.pop("admin_login_otp", None)

        return RedirectResponse(
            url="/users_data",
            status_code=303
        )
    else:
        request.session["is_admin"] = False
        Is_admin_logged_in = False


    return template.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "error": "Invalid username, password or OTP"
        }
    )
    
@app.get("/admin-otp")
def admin_otp(request: Request):
    otp = generate_otp()
    request.session["admin_login_otp"] = otp
    try:
        if request.session.get("admin_login_otp")== otp:
            print(A_USERNAME, A_PASSWORD, otp)  # Debug: Check credentials and OTP
            send_email_otp(otp)
            return {"message": "OTP Sent Successfully"}
        else:
            return {"message": "Failed to send OTP"}
    except Exception as e:
        print("Email Error:", e)
        return {"message": str(e)}

@app.get("/users_data")
async def admin_dashboard(request: Request):
    print(request.session.get("is_admin"))  # Debug: Check admin login status
    if not IS_admin_logged_in and not request.session.get("is_admin"):
        return RedirectResponse(url="/ADMIN")
    else:
        # Fetch all data from the database with IDs
        admissions = []
        for item in add.find():
            admissions.append({**item, "_id": str(item["_id"])})

        contacts = []
        for item in con.find():
            contacts.append({**item, "_id": str(item["_id"])})

        feedbacks = []
        for item in fed.find():
            feedbacks.append({**item, "_id": str(item["_id"])})
        
        gallery_items = []
        for item in gal.find():
            gallery_items.append({**item, "_id": str(item["_id"])})
        
        student_life = sl.find_one({"type": "student_life"}) or {}
        home_video = hv.find_one({"type": "home_video"}) or {}
        
        # Visitor Analytics Calculation
        now = datetime.utcnow()
        visitor_stats = {
            "last_24h": vis.count_documents({"timestamp": {"$gte": now - timedelta(days=1)}}),
            "last_week": vis.count_documents({"timestamp": {"$gte": now - timedelta(days=7)}}),
            "last_month": vis.count_documents({"timestamp": {"$gte": now - timedelta(days=30)}}),
            "last_year": vis.count_documents({"timestamp": {"$gte": now - timedelta(days=365)}}),
            "total": vis.count_documents({})
        }

        return template.TemplateResponse(
            request=request,
            name="users_data.html",
            context={
                "admissions": admissions,
                "contacts": contacts,
                "feedbacks": feedbacks,
                "gallery_items": gallery_items,
                "student_life": student_life,
                "home_video": home_video,
                "visitor_stats": visitor_stats
            }
        )


@app.post("/gallery-upload")
async def gallery_upload(
    request: Request,
    occasion: str = Form(...),
    date: str = Form(...),
    photo: UploadFile = File(None),
    edit_id: str = Form(None)
):
    
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/ADMIN")
    else:
        update_data = {
            "occasion": occasion,
            "date": date
        }

        if photo and photo.filename:
            upload_dir = BASE_DIR / "frontend" / "static" / "gallery"
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = upload_dir / photo.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(photo.file, buffer)
            update_data["image_url"] = f"/static/gallery/{photo.filename}"
            
        if edit_id:
            gal.update_one({"_id": ObjectId(edit_id)}, {"$set": update_data})
        else:
            # Ensure photo is provided for new entries
            if "image_url" not in update_data:
                update_data["image_url"] = "/static/images/placeholder.png"
            gal.insert_one(update_data)
        
        return RedirectResponse(url="/users_data", status_code=303)

@app.post("/student-life-upload")
async def student_life_upload(
    request: Request,
    academic: UploadFile = File(None),
    sports: UploadFile = File(None),
    arts: UploadFile = File(None),
    digital: UploadFile = File(None)
):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/ADMIN")
    
    upload_dir = BASE_DIR / "frontend" / "static" / "student_life"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    update_data = {}
    for key, file in {"academic_img": academic, "sports_img": sports, "arts_img": arts, "digital_img": digital}.items():
        if file and file.filename:
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            update_data[key] = f"/static/student_life/{file.filename}"
            
    sl.update_one({"type": "student_life"}, {"$set": update_data}, upsert=True)
    return RedirectResponse(url="/users_data", status_code=303)

@app.post("/home-video-upload")
async def home_video_upload(
    request: Request,
    video: UploadFile = File(None)
):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/ADMIN")
    
    if video and video.filename:
        upload_dir = BASE_DIR / "frontend" / "static" / "videos"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / video.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
            
        hv.update_one(
            {"type": "home_video"},
            {"$set": {"video_url": f"/static/videos/{video.filename}"}},
            upsert=True
        )
    return RedirectResponse(url="/users_data", status_code=303)

@app.post("/gallery-delete/{photo_id}")
async def gallery_delete(request: Request, photo_id: str):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/ADMIN")
    else:
        gal.delete_one({"_id": ObjectId(photo_id)})
        return RedirectResponse(url="/users_data", status_code=303)

@app.post("/admission-delete/{item_id}")
async def admission_delete(request: Request, item_id: str):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/ADMIN")
    else:
        add.delete_one({"_id": ObjectId(item_id)})
        return RedirectResponse(url="/users_data", status_code=303)

@app.post("/contact-delete/{item_id}")
async def contact_delete(request: Request, item_id: str):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/ADMIN")
    else:
        con.delete_one({"_id": ObjectId(item_id)})
        return RedirectResponse(url="/users_data", status_code=303)

@app.post("/feedback-delete/{item_id}")
async def feedback_delete(request: Request, item_id: str):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/ADMIN")
    else:
        fed.delete_one({"_id": ObjectId(item_id)})
        return RedirectResponse(url="/users_data", status_code=303)


@app.get("/")
async def index(request: Request):
    # Log every visit to the home page
    vis.insert_one({"timestamp": datetime.utcnow()})
    request.session["is_admin"] = False
    student_life = sl.find_one({"type": "student_life"}) or {}
    home_video = hv.find_one({"type": "home_video"}) or {}

    return template.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "student_life": student_life, "home_video": home_video}
    )

@app.get("/{page_name}")
async def get_page(request: Request, page_name: str):
    ctx = {"request": request}
    if page_name == "gallery.html":
        try:
            ctx["gallery_items"] = list(gal.find({}, {"_id": 0}))
        except Exception as e:
            print(f"Database connection error: {e}")
            ctx["gallery_items"] = []
    elif page_name == "index.html":
        ctx["student_life"] = sl.find_one({"type": "student_life"}) or {}
        ctx["home_video"] = hv.find_one({"type": "home_video"}) or {}

    return template.TemplateResponse(
        request=request,
        name=page_name,
        context=ctx
    )

@app.post("/feedbackinput") 
async def feedbackinput(request:Request,user_name:str = Form() ,user_email:str=Form(), user_message:str=Form()):
    msg = ""
    feedback_data = {
        "name": user_name,
        "email": user_email,
        "message": user_message
    }
    if feedback_data["name"] == "" or feedback_data["email"] == "" or feedback_data["message"] == "":
        msg = "Please fill in all fields before submitting."
    else:
        try:
            fed.insert_one(feedback_data)
            msg = f"Thank you {user_name}😉 Your feedback has been recorded."
        except Exception as e:
            print(f"Database error: {e}")
            msg = "Failed to record feedback. Please check database connection."

    return {"notification": msg}

# @app.post("/send-otp")
# async def request_otp_handler(request: Request, phone: str = Form(...)):
#     otp = generate_otp()
#     otp_storage[phone] = otp  # Store OTP in memory (for demonstration purposes only)
#     try:
#         dispatch_sms_otp(phone, otp)
#         # Store OTP and phone in session so addmissioninput can verify them upon form submission
#         request.session["admission_otp"] = otp
#         request.session["otp_phone"] = phone
#         return {"notification": "OTP sent successfully"}
#     except TwilioRestException as e:
#         print(f"Twilio error: {e}")
#         return {"notification": "Invalid phone number. Please include country code (e.g. +91)."}
#     except Exception as e:
#         print(f"General error: {e}")
#         return {"notification": "Failed to send OTP. Please try again later."}


# @app.post("/verify-otp")
# async def verify_otp(request: Request, verify_otp: VerifyOTP = Form(...)):
#     stored_otp = otp_storage.get(verify_otp.phone_number)
#     if stored_otp and stored_otp == verify_otp.otp:
#         del otp_storage[verify_otp.phone_number]  # Remove OTP after successful verification
#         request.session["admission_otp"] = verify_otp.otp  # Store OTP in session for later verification
#         request.session["otp_phone"] = verify_otp.phone_number  # Store phone number in session for later verification
#         return {"message": "OTP verified successfully"}
#     else:
#         return {"message": "Invalid OTP"}



@app.post("/addmissioninput") 
async def addmissioninput(request:Request, user_name:str = Form(), email:str=Form(), phone:str=Form(), address:str=Form(), otp:str=Form(None)):
    # session_otp = request.session.get("admission_otp")
    # session_phone = request.session.get("otp_phone")
    msg = ""
    admission_data = {
        "name": user_name,
        "email": email,
        "phone": phone,
        "address": address
    }
    # Check if OTP matches and belongs to the correct phone number
    # if not session_otp or otp != session_otp or phone != session_phone:
    #     return {"notification": "Invalid or expired OTP. Please verify your phone number again."}
    if not all([user_name, email, phone, address]):
        msg = "Incomplete data. Please provide all required information."
    else:
        try:
            # Check for existing record with same name and phone
            existing_record = add.find_one({"name": user_name, "phone": phone})
            if existing_record:
                return {"notification": f"An application for {user_name} with this phone number is already recorded."}

            add.insert_one(admission_data)
            msg = f"Thank you {user_name}! Your admission request has been recorded."
        except Exception as e:
            print(f"Database error: {e}")
            msg = "Failed to record admission. Please check database connection."
        # Clear the OTP from session after successful registration
        # request.session.pop("admission_otp", None)
    return {"notification": msg}

@app.post("/contactinput") 
async def contactinput(request:Request, user_name:str = Form(), user_email:str=Form(), user_message:str=Form(), phone:str=Form(), otp:str=Form(None)):
    # session_otp = request.session.get("admission_otp")
    # session_phone = request.session.get("otp_phone")
    
    # Verify OTP and phone number match the session
    # if not session_otp or otp != session_otp or phone != session_phone:
    #     return {"notification": "Invalid or expired OTP. Please verify your phone number again."}

    contact_data = {
        "name": user_name,
        "email": user_email,
        "phone": phone,
        "message": user_message
    }
    
    # Insert into the 'contacts' collection
    try:
        con.insert_one(contact_data)
        msg = f"Thank you {user_name}! Your message has been received."
    except Exception as e:
        print(f"Database error: {e}")
        msg = "Failed to send message. Please check database connection."
    
    # Clean up session
    # request.session.pop("admission_otp", None)
    return {"notification": msg}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
