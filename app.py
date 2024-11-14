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

# User Registration
class UserRegister(Resource):
    def post(self):
        data = request.get_json()
        name = data.get("name")
        username = data.get("username")
        email = data.get("email")
        password = str(data.get("password"))
        image_url = data.get("image_url")
        age = data.get("age")

        if not username or not email or not password:
            return {"error": "Username, email, and password are required."}, 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return {"error": "Email already in use."}, 400

        new_user = User(
            name=name,
            username=username,
            email=email,
            password=password,
            image_url=image_url,
            age=age,
            created_at=datetime.now()
        )

        db.session.add(new_user)
        db.session.commit()

        return new_user.to_dict(), 201

api.add_resource(UserRegister, "/user/register")



class UserLogin(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = str(data.get("password"))

        user = User.query.filter_by(email=email).first()

        if user:
            return user.to_dict(), 200
        else:
            return {"error": "Invalid email or password"}, 400

api.add_resource(UserLogin, "/user/login")


# Fetch All Users
class Users(Resource):
    def get(self):
        users = User.query.all()
        return make_response(jsonify([user.to_dict() for user in users]), 200)

api.add_resource(Users, "/users")


#
class UserByID(Resource):
    def get(self, id):
        user = User.query.filter(User.id == id).first()
        if user:
            return make_response(jsonify(user.to_dict()), 200)
        else:
            return make_response(jsonify({"error": "User not found"}), 404)

    def patch(self, id):
        data = request.get_json()
        user = User.query.filter(User.id == id).first()

        if not user:
            return make_response(jsonify({"error": "User not found"}), 404)

        for attr in data:
            setattr(user, attr, data.get(attr))

        db.session.add(user)
        db.session.commit()

        return make_response(user.to_dict(), 200)

    def delete(self, id):
        user = User.query.filter(User.id == id).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return make_response("", 204)
        else:
            return make_response(jsonify({"error": "User not found"}), 404)

api.add_resource(UserByID, "/users/<int:id>")



class Notes(Resource):
    def get(self):
        notes = Note.query.all()
        return make_response(jsonify([note.to_dict() for note in notes]), 200)

    def post(self):
        data = request.get_json()
        user_id = data.get("user_id")
        title = data.get("title")
        content = data.get("content")
        created_at = datetime.now()

        new_note = Note(user_id=user_id, title=title, content=content, created_at=created_at)

        db.session.add(new_note)
        db.session.commit()

        return make_response(jsonify(new_note.to_dict()), 201)

class NoteByID(Resource):
    def get(self, id):
        note = Note.query.filter(Note.id == id).first()
        if note:
            return make_response(jsonify(note.to_dict()), 200)
        else:
            return make_response(jsonify({"error": "note not found"}), 404)
    
    def patch(self, id):
        data = request.get_json()
        note = Note.query.filter(Note.id == id).first()

        if note:
            for attr, value in data.items():
                setattr(note, attr, value)

            db.session.commit()
            return make_response(jsonify(note.to_dict()), 200)
        else:
            return make_response(jsonify({"error": "note not found"}), 404)
    
    def delete(self, id):
        note = Note.query.filter(Note.id == id).first()
        if note:
            db.session.delete(note)
            db.session.commit()
            return make_response("", 204)
        else:
            return make_response(jsonify({"error": "note not found"}), 404)

# Route Registration
api.add_resource(Notes, "/notes")
api.add_resource(NoteByID, "/notes/<int:id>")

# User Info
class UserInfo(Resource):
    def get(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return make_response(jsonify({"error": "User not found!"}), 404)

        user_data = user.to_dict()
        return make_response(jsonify(user_data), 200)

api.add_resource(UserInfo, "/users/<int:user_id>/info")




if __name__ == "__main__":
    app.run(debug=True)