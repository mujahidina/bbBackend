from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from flask_migrate import Migrate
from sqlalchemy import MetaData, func
from datetime import datetime, timedelta
from sqlalchemy_serializer import SerializerMixin


metadata = MetaData()
db = SQLAlchemy(metadata=metadata)

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)  # Not serialized
    username = db.Column(db.String(), unique=True, nullable=False)  
    age = db.Column(db.String()) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_url = db.Column(db.String())
    
    # Achievements initially set to False
    seven_day_streak = db.Column(db.Boolean, default=False)
    thirty_day_streak = db.Column(db.Boolean, default=False)
    hundred_study_sessions = db.Column(db.Boolean, default=False)
    focused_for_one_hour = db.Column(db.Boolean, default=False)
    completed_weekly_challenge = db.Column(db.Boolean, default=False)
    

    study_streaks = db.relationship('StudyStreak', backref='user_streaks', lazy=True)
    achievements = db.relationship('Achievement', backref='user_achievements', lazy=True)

    serialize_rules = ('-password', '-study_streaks.user_streaks', '-achievements.user_achievements')

    @validates('password')
    def validate_password(self, key, password):
        if len(password) < 8:
            raise ValueError('Password must be more than 8 characters.')
        return password
    
    @validates('email')
    def validate_email(self, key, email):
        if not email.endswith("@gmail.com"):
            raise ValueError("Email is not valid. It should end with @gmail.com")
        return email

    def __repr__(self):
        return f'<User {self.username} ({self.name})>'





class Note(db.Model, SerializerMixin):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  
    title = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  


    user = db.relationship('User', backref='notes', lazy=True)

    serialize_rules = ('-user.notes',)  

    def __repr__(self):
        return f'<Note {self.id} by User {self.user_id}>'




class StudyStreak(db.Model, SerializerMixin):
    __tablename__ = 'study_streaks'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)  
    session_count = db.Column(db.Integer, default=0)  
    streak_length = db.Column(db.Integer, default=0)  
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  

    serialize_rules = ('-user_streaks.study_streaks',)

    def __repr__(self):
        return f'<StudyStreak {self.date} - {self.session_count} sessions, Streak: {self.streak_length} days>'




class Achievement(db.Model, SerializerMixin):
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  
    description = db.Column(db.String(255), nullable=False)  
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)  
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  
    
    # SerializerMixin configuration with serialize_rules
    serialize_rules = ('-user_achievements.achievements',)

    def __repr__(self):
        return f'<Achievement {self.name}>'

# Utility function to update study streak for the day
def update_study_streak(user_id, session_date, session_duration):
    session_date = session_date.date()
    

    streak = StudyStreak.query.filter_by(user_id=user_id, date=session_date).first()
    
    if streak:
        streak.session_count += 1  
    else:
        streak = StudyStreak(user_id=user_id, date=session_date, session_count=1, streak_length=1)
        db.session.add(streak)


    last_streak = StudyStreak.query.filter_by(user_id=user_id).order_by(StudyStreak.date.desc()).first()
    if last_streak and last_streak.date == session_date - timedelta(days=1):
        streak.streak_length = last_streak.streak_length + 1
    else:
        streak.streak_length = 1

    check_achievements(user_id, streak, session_duration)

    db.session.commit()

def check_achievements(user_id, streak, session_duration):
    user = User.query.get(user_id)

    if streak.streak_length >= 7 and not user.seven_day_streak:
        user.seven_day_streak = True
        achievement = Achievement(name="7-Day Study Streak", description="Study for 7 consecutive days", user_id=user_id)
        db.session.add(achievement)

    if streak.streak_length >= 30 and not user.thirty_day_streak:
        user.thirty_day_streak = True
        achievement = Achievement(name="30-Day Study Streak", description="Study for 30 consecutive days", user_id=user_id)
        db.session.add(achievement)

    total_sessions = db.session.query(func.sum(StudyStreak.session_count)).filter(StudyStreak.user_id == user_id).scalar()
    if total_sessions >= 100 and not user.hundred_study_sessions:
        user.hundred_study_sessions = True
        achievement = Achievement(name="100 Study Sessions", description="Complete 100 study sessions", user_id=user_id)
        db.session.add(achievement)

    if session_duration >= 60 and not user.focused_for_one_hour:
        user.focused_for_one_hour = True
        achievement = Achievement(name="Focused for 1 Hour", description="Study for 1 hour in a single session", user_id=user_id)
        db.session.add(achievement)

    if streak.streak_length >= 5 and not user.completed_weekly_challenge:
        user.completed_weekly_challenge = True
        achievement = Achievement(name="Completed Weekly Challenge", description="Complete the weekly study challenge", user_id=user_id)
        db.session.add(achievement)

    db.session.commit()


















