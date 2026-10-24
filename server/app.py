import os

from flask import Flask, jsonify, make_response, request
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from models import Exercise, Workout, WorkoutExercise, db
from schemas import (
    exercise_detail_schema,
    exercise_schema,
    exercises_schema,
    workout_detail_schema,
    workout_exercise_schema,
    workout_schema,
    workouts_schema,
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)
db.init_app(app)

def respond(body, status=200):
    return make_response(jsonify(body), status)
def error(message, status):
    return respond({'error': message}, status)
def get_json_body():  
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None
@app.errorhandler(404)
def handle_not_found(_):
    return error('Resource not found.', 404)
@app.errorhandler(405)
def handle_method_not_allowed(_):
    return error('Method not allowed.', 405)
@app.route('/')
def index():
    return respond({'message': 'Workout API is running.'})
@app.route('/workouts', methods=['GET'])
def get_workouts():
    workouts = Workout.query.order_by(Workout.date.desc(), Workout.id).all()
    return respond(workouts_schema.dump(workouts))
@app.route('/workouts/<int:id>', methods=['GET'])
def get_workout(id):
    workout = db.session.get(Workout, id)
    if workout is None:
        return error(f'Workout {id} not found.', 404)
    return respond(workout_detail_schema.dump(workout))
@app.route('/workouts', methods=['POST'])
def create_workout():
    data = get_json_body()
    if data is None:
        return error('Request body must be a JSON object.', 400)
    try:
        validated = workout_schema.load(data)
        workout = Workout(**validated)
        db.session.add(workout)
        db.session.commit()
    except ValidationError as err:
        return respond({'errors': err.messages}, 400)
    except ValueError as err:  # raised by the model validations
        db.session.rollback()
        return error(str(err), 400)
    except IntegrityError:  # raised by the table constraints
        db.session.rollback()
        return error('Workout violates a database constraint.', 400)

    return respond(workout_schema.dump(workout), 201)
@app.route('/workouts/<int:id>', methods=['DELETE'])
def delete_workout(id):
    workout = db.session.get(Workout, id)
    if workout is None:
        return error(f'Workout {id} not found.', 404)
    db.session.delete(workout)
    db.session.commit()
    return make_response('', 204)
@app.route('/exercises', methods=['GET'])
def get_exercises():
    exercises = Exercise.query.order_by(Exercise.name).all()
    return respond(exercises_schema.dump(exercises))
@app.route('/exercises/<int:id>', methods=['GET'])
def get_exercise(id):
    exercise = db.session.get(Exercise, id)
    if exercise is None:
        return error(f'Exercise {id} not found.', 404)
    return respond(exercise_detail_schema.dump(exercise))
@app.route('/exercises', methods=['POST'])
def create_exercise():
    data = get_json_body()
    if data is None:
        return error('Request body must be a JSON object.', 400)
    try:
        validated = exercise_schema.load(data)
        exercise = Exercise(**validated)
        db.session.add(exercise)
        db.session.commit()
    except ValidationError as err:
        return respond({'errors': err.messages}, 400)
    except ValueError as err:
        db.session.rollback()
        return error(str(err), 400)
    except IntegrityError:
        db.session.rollback()
        return error('An exercise with that name already exists.', 409)
    return respond(exercise_schema.dump(exercise), 201)
@app.route('/exercises/<int:id>', methods=['DELETE'])
def delete_exercise(id):
    exercise = db.session.get(Exercise, id)
    if exercise is None:
        return error(f'Exercise {id} not found.', 404)
    db.session.delete(exercise)
    db.session.commit()
    return make_response('', 204)
@app.route(
    '/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises',
    methods=['POST'],
)
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return error(f'Workout {workout_id} not found.', 404)
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return error(f'Exercise {exercise_id} not found.', 404)
    data = get_json_body()
    if data is None:
        return error('Request body must be a JSON object.', 400)
    already_added = WorkoutExercise.query.filter_by(
        workout_id=workout_id, exercise_id=exercise_id
    ).first()
    if already_added:
        return error('That exercise is already part of this workout.', 409)
    try:
        validated = workout_exercise_schema.load(data)
        workout_exercise = WorkoutExercise(
            workout_id=workout_id, exercise_id=exercise_id, **validated
        )
        db.session.add(workout_exercise)
        db.session.commit()
    except ValidationError as err:
        return respond({'errors': err.messages}, 400)
    except ValueError as err:
        db.session.rollback()
        return error(str(err), 400)
    except IntegrityError:
        db.session.rollback()
        return error('Workout exercise violates a database constraint.', 400)
    return respond(workout_exercise_schema.dump(workout_exercise), 201)

if __name__ == '__main__':
    app.run(port=5555, debug=True)