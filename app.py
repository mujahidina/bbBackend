from flask import Flask, request, jsonify, make_response
from flask_migrate import Migrate
from flask_restful import Resource, Api
from models import db, User, StudyStreak, Achievement, update_study_streak, Note
from flask_cors import CORS
from datetime import datetime
import cloudinary
import cloudinary.uploader
import cloudinary.api



cloudinary.config(
    cloud_name='breakbuddy',
    api_key='896593449937286',
    api_secret='****************************'
)



app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///breakbuddy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.json.compact = False

db.init_app(app)

migrate = Migrate(app, db)
api = Api(app)


class UserRegister(Resource):
    def post(self):
        data = request.get_json()
        name = data.get("name")
        username = data.get("username")
        email = data.get("email")
        password = str(data.get("password"))
        image_url = data.get("image_url")
        date_of_birth = data.get("date_of_birth")

        if not username or not email or not password:
            return {"error": "Username, email, and password are required."}, 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return {"error": "Email already in use."}, 400

        if date_of_birth:
            try:
                date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d')
            except ValueError:
                return {"error": "Invalid date format. Please use YYYY-MM-DD."}, 400

        # Create a new user
        new_user = User(
            name=name,
            username=username,
            email=email,
            password=password,
            image_url=image_url,
            date_of_birth=date_of_birth,
            created_at=datetime.now()
        )

        db.session.add(new_user)
        db.session.commit()

        return {
            "id": new_user.id,
            "name": new_user.name,
            "username": new_user.username,
            "email": new_user.email,
            "image_url": new_user.image_url,
            "date_of_birth": new_user.date_of_birth.strftime('%Y-%m-%d') if new_user.date_of_birth else None,
            "created_at": new_user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }, 201
api.add_resource(UserRegister, "/user/register")





# User Login
class UserLogin(Resource):
    def post(self):
        data = request.get_json()
        
        email = data.get("email")
        password = str(data.get("password"))

        user = User.query.filter_by(email=email).first()

        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "image_url": user.image_url,
            "date_of_birth": user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else None,
            "created_at": user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }, 200

api.add_resource(UserLogin, "/user/login")


class Users(Resource):
    def get(self):
        users = User.query.all()  
        return make_response(jsonify([user.to_dict() for user in users]), 200)  


class UserByID(Resource):

    def get(self,id):
        user = User.query.filter(User.id==id).first()

        if user:
            return make_response(jsonify(user.to_dict()),200) 

    def patch(self,id):

        data = request.get_json()

        user = User.query.filter(User.id==id).first()

        for attr in data:
            setattr(user,attr,data.get(attr))

        db.session.add(user)
        db.session.commit()

        return make_response(user.to_dict(),200)

    

  

    def delete(self,id):

        user = User.query.filter(User.id==id).first()

        if user:
            db.session.delete(user)
            db.session.commit()
            return make_response("",204)
        else:
            return make_response(jsonify({"error":"User not found"}),404) 


class Notes(Resource):
    def get(self):
        notes = Note.query.all()  
        return make_response(jsonify([note.to_dict() for note in notes]), 200)  
    
    
    def post(self):
        data = request.get_json()
        user_id = data.get("user_id")
        title = data.get("title")
        content = data.get("content")
        created_at = data.get("created_at")
        
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00")) if created_at else datetime.utcnow()
        except ValueError:
            return {"error": "Invalid date format. Please use ISO 8601 format."}, 400

        
        new_note = Note(user_id=user_id, title=title, content=content, created_at=created_at)

        db.session.add(new_note)
        db.session.commit()

        return make_response(new_note.to_dict(), 201)

    


class NoteByID(Resource):
    
    def get(self,id):
        note = Note.query.filter(Note.id==id).first()
        if note:
            return make_response(jsonify(note.to_dict()),200) 
        

    def patch(self,id):

        data = request.get_json()

        note = Note.query.filter(Note.id==id).first()

        for attr in data:
            setattr(note,attr,data.get(attr))

        db.session.add(note)
        db.session.commit()

        return make_response(note.to_dict(),200)

    def delete(self,id):

        note = Note.query.filter(Note.id==id).first()

        if note:
            db.session.delete(note)
            db.session.commit()
            return make_response("",204)
        else:
            return make_response(jsonify({"error":"User not found"}),404) 




class UserStudyStreaks(Resource):

    def get(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found!"}), 404
        streaks = [streak.to_dict(only=('date', 'session_count', 'streak_length')) for streak in StudyStreak.query.filter_by(user_id=user_id).all()]
        return make_response({"user_id": user_id, "study_streaks": streaks}, 200)


class AddStudySession(Resource):
    def post(self, user_id):
        data = request.get_json()
        session_duration = data.get('session_duration')  
        session_date = datetime.strptime(data.get('session_date'), '%Y-%m-%d')  
        
        updated_streak = update_study_streak(user_id, session_date, session_duration)
    
        return make_response(jsonify(updated_streak.to_dict(only=('date', 'session_count', 'streak_length'))), 200)




class UserAchievements(Resource):
    def get(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return make_response(jsonify({"error": "User not found!"}), 404)

        achievements = [
            achievement.to_dict(only=('name', 'description', 'earned_at'))
            for achievement in Achievement.query.filter_by(user_id=user_id).all()
        ]

        return make_response(jsonify(achievements), 200)

class UserInfo(Resource):
    def get(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return make_response(jsonify({"error": "User not found!"}), 404)

        user_data = user.to_dict(only=(
            'id', 'name', 'email', 'username', 'date_of_birth', 'created_at',
            'seven_day_streak', 'thirty_day_streak', 'hundred_study_sessions',
            'focused_for_one_hour', 'completed_weekly_challenge', 'image_url'
        ))

        return make_response(jsonify(user_data), 200)



api.add_resource(Users, "/users")
api.add_resource(Notes, "/notes")
api.add_resource(NoteByID, "/notes/<int:id>")
api.add_resource(UserByID, "/users/<int:id>")
api.add_resource(UserStudyStreaks, "/user/<int:user_id>/streaks")
api.add_resource(AddStudySession, "/user/<int:user_id>/study_session")
api.add_resource(UserAchievements, "/user/<int:user_id>/achievements")
api.add_resource(UserInfo, "/user/<int:user_id>")



if __name__ == "__main__":
    app.run(debug=True)