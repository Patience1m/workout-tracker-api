from datetime import date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates

db = SQLAlchemy()

class Exercise(db.Model): 
    __tablename__ = 'exercises'
    __table_args__ = (
        db.UniqueConstraint('name', name='uq_exercises_name'),
        db.CheckConstraint('length(trim(name)) > 0', name='ck_exercises_name_not_blank'),
        db.CheckConstraint('length(trim(category)) > 0', name='ck_exercises_category_not_blank'),
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)
    workout_exercises = db.relationship(
        'WorkoutExercise',
        back_populates='exercise',
        cascade='all, delete-orphan',
    )
    workouts = association_proxy('workout_exercises', 'workout') 
    @validates('name', 'category')
    def validate_text(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{key} must be a non-empty string.')
        return value.strip()
    @validates('equipment_needed')
    def validate_equipment_needed(self, key, value):
        if not isinstance(value, bool):
            raise ValueError('equipment_needed must be true or false.')
        return value
    def __repr__(self):
        return f'<Exercise {self.id}: {self.name}>'

class Workout(db.Model): 
    __tablename__ = 'workouts'
    __table_args__ = (
        db.CheckConstraint('duration_minutes > 0', name='ck_workouts_duration_positive'),
    )
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)  
    workout_exercises = db.relationship(
        'WorkoutExercise',
        back_populates='workout',
        cascade='all, delete-orphan',
    )
    exercises = association_proxy('workout_exercises', 'exercise')
    @validates('date')
    def validate_date(self, key, value):
        if not isinstance(value, date):
            raise ValueError('date must be a valid date.')
        return value
    @validates('duration_minutes')
    def validate_duration_minutes(self, key, value):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError('duration_minutes must be a positive integer.')
        return value
    def __repr__(self):
        return f'<Workout {self.id}: {self.date}>'

class WorkoutExercise(db.Model):  
    __tablename__ = 'workout_exercises'
    __table_args__ = (      
        db.UniqueConstraint('workout_id', 'exercise_id', name='uq_workout_exercise_pair'),
        db.CheckConstraint('reps IS NULL OR reps > 0', name='ck_workout_exercises_reps_positive'),
        db.CheckConstraint('sets IS NULL OR sets > 0', name='ck_workout_exercises_sets_positive'),
        db.CheckConstraint(
            'duration_seconds IS NULL OR duration_seconds > 0',
            name='ck_workout_exercises_duration_positive',
        ),     
        db.CheckConstraint(
            '(reps IS NOT NULL AND sets IS NOT NULL) OR duration_seconds IS NOT NULL',
            name='ck_workout_exercises_has_effort',
        ),
    )
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workouts.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    reps = db.Column(db.Integer)
    sets = db.Column(db.Integer)
    duration_seconds = db.Column(db.Integer)
    workout = db.relationship('Workout', back_populates='workout_exercises')
    exercise = db.relationship('Exercise', back_populates='workout_exercises')
    @validates('reps', 'sets', 'duration_seconds')
    def validate_positive_int(self, key, value):
        if value is None:
            return value
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f'{key} must be a positive integer.')
        return value
    def __repr__(self):
        return f'<WorkoutExercise {self.id}: workout {self.workout_id}, exercise {self.exercise_id}>'