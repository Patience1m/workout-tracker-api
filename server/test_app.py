import os
import runpy
from datetime import date
import pytest
from sqlalchemy.exc import IntegrityError

os.environ['DATABASE_URI'] = 'sqlite:///:memory:'

from app import app  
from models import Exercise, Workout, WorkoutExercise, db  

@pytest.fixture(autouse=True)
def database():
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
@pytest.fixture
def client():
    return app.test_client()
@pytest.fixture
def squat():
    exercise = Exercise(name='Squat', category='Strength', equipment_needed=True)
    db.session.add(exercise)
    db.session.commit()
    return exercise
@pytest.fixture
def workout():
    workout = Workout(date=date(2026, 10, 5), duration_minutes=45, notes='Legs')
    db.session.add(workout)
    db.session.commit()
    return workout
class TestModelValidations:
    def test_exercise_name_cannot_be_blank(self):
        with pytest.raises(ValueError):
            Exercise(name='   ', category='Strength')
    def test_exercise_category_cannot_be_blank(self):
        with pytest.raises(ValueError):
            Exercise(name='Squat', category='')
    def test_exercise_equipment_needed_must_be_boolean(self):
        with pytest.raises(ValueError):
            Exercise(name='Squat', category='Strength', equipment_needed='yes')
    def test_exercise_name_is_stripped(self):
        assert Exercise(name='  Squat  ', category='Strength').name == 'Squat'
    def test_workout_duration_must_be_positive(self):
        with pytest.raises(ValueError):
            Workout(date=date(2026, 1, 1), duration_minutes=0)
    def test_workout_duration_must_be_integer(self):
        with pytest.raises(ValueError):
            Workout(date=date(2026, 1, 1), duration_minutes='30')
    def test_workout_date_must_be_a_date(self):
        with pytest.raises(ValueError):
            Workout(date='2026-01-01', duration_minutes=30)
    def test_workout_exercise_values_must_be_positive(self):
        with pytest.raises(ValueError):
            WorkoutExercise(reps=-1)
        with pytest.raises(ValueError):
            WorkoutExercise(sets=0)
        with pytest.raises(ValueError):
            WorkoutExercise(duration_seconds='60')
class TestTableConstraints:
    def test_exercise_name_must_be_unique(self, squat):
        db.session.add(Exercise(name='Squat', category='Other'))
        with pytest.raises(IntegrityError):
            db.session.commit()
    def test_workout_duration_check_constraint(self):
        with pytest.raises(IntegrityError):
            db.session.execute(
                db.text("INSERT INTO workouts (date, duration_minutes) VALUES ('2026-01-01', 0)")
            )
    def test_exercise_blank_name_check_constraint(self):
        with pytest.raises(IntegrityError):
            db.session.execute(
                db.text(
                    "INSERT INTO exercises (name, category, equipment_needed) "
                    "VALUES ('  ', 'x', 0)"
                )
            )
    def test_workout_exercise_needs_effort_check_constraint(self, workout, squat):
        db.session.add(WorkoutExercise(workout=workout, exercise=squat))
        with pytest.raises(IntegrityError):
            db.session.commit()
    def test_workout_exercise_pair_must_be_unique(self, workout, squat):
        db.session.add(WorkoutExercise(workout=workout, exercise=squat, reps=5, sets=5))
        db.session.commit()
        db.session.add(WorkoutExercise(workout=workout, exercise=squat, reps=8, sets=3))
        with pytest.raises(IntegrityError):
            db.session.commit()
    def test_workout_exercise_foreign_keys_required(self):
        db.session.add(WorkoutExercise(reps=5, sets=5))
        with pytest.raises(IntegrityError):
            db.session.commit()
class TestRelationships:
    def test_workout_has_many_exercises_through_join_table(self, workout, squat):
        link = WorkoutExercise(workout=workout, exercise=squat, reps=5, sets=5)
        db.session.add(link)
        db.session.commit()
        assert link.workout is workout
        assert link.exercise is squat
        assert workout.workout_exercises == [link]
        assert squat.workout_exercises == [link]
        assert list(workout.exercises) == [squat]
        assert list(squat.workouts) == [workout]
    def test_deleting_workout_removes_its_join_rows(self, workout, squat):
        db.session.add(WorkoutExercise(workout=workout, exercise=squat, reps=5, sets=5))
        db.session.commit()
        db.session.delete(workout)
        db.session.commit()
        assert WorkoutExercise.query.count() == 0
        assert Exercise.query.count() == 1
class TestWorkoutEndpoints:
    def test_get_workouts(self, client, workout):
        response = client.get('/workouts')
        assert response.status_code == 200
        assert response.json == [
            {'id': workout.id, 'date': '2026-10-05', 'duration_minutes': 45, 'notes': 'Legs'}
        ]
    def test_get_workouts_empty(self, client):
        assert client.get('/workouts').json == []
    def test_get_workout_includes_exercises_with_reps_sets(self, client, workout, squat):
        db.session.add(WorkoutExercise(workout=workout, exercise=squat, reps=8, sets=4))
        db.session.commit()
        response = client.get(f'/workouts/{workout.id}')
        assert response.status_code == 200
        entry = response.json['workout_exercises'][0]
        assert entry['reps'] == 8
        assert entry['sets'] == 4
        assert entry['exercise']['name'] == 'Squat'
    def test_get_workout_not_found(self, client):
        response = client.get('/workouts/999')
        assert response.status_code == 404
        assert 'error' in response.json
    def test_create_workout(self, client):
        response = client.post(
            '/workouts', json={'date': '2026-11-01', 'duration_minutes': 30, 'notes': 'Easy'}
        )
        assert response.status_code == 201
        assert response.json['id'] is not None
        assert Workout.query.count() == 1
    def test_create_workout_notes_optional(self, client):
        response = client.post('/workouts', json={'date': '2026-11-01', 'duration_minutes': 30})
        assert response.status_code == 201
    @pytest.mark.parametrize(
        'payload',
        [
            {},
            {'date': 'not-a-date', 'duration_minutes': 30},
            {'date': '2026-11-01', 'duration_minutes': 0},
            {'date': '2026-11-01', 'duration_minutes': -5},
            {'date': '2026-11-01', 'duration_minutes': '30'},
            {'date': '2026-11-01', 'duration_minutes': 5000},
            {'date': '2026-11-01', 'duration_minutes': 30, 'surprise': 1},
            {'date': '2026-11-01', 'duration_minutes': 30, 'id': 7},
        ],
    )
    def test_create_workout_rejects_invalid_data(self, client, payload):
        response = client.post('/workouts', json=payload)
        assert response.status_code == 400
        assert 'errors' in response.json
        assert Workout.query.count() == 0
    def test_create_workout_requires_json_object(self, client):
        assert client.post('/workouts', data='nope').status_code == 400
        assert client.post('/workouts', json=[1, 2]).status_code == 400
    def test_delete_workout(self, client, workout, squat):
        db.session.add(WorkoutExercise(workout=workout, exercise=squat, reps=5, sets=5))
        db.session.commit()
        response = client.delete(f'/workouts/{workout.id}')
        assert response.status_code == 204
        assert Workout.query.count() == 0
        assert WorkoutExercise.query.count() == 0

    def test_delete_workout_not_found(self, client):
        assert client.delete('/workouts/999').status_code == 404
class TestExerciseEndpoints:
    def test_get_exercises(self, client, squat):
        response = client.get('/exercises')
        assert response.status_code == 200
        assert response.json == [
            {'id': squat.id, 'name': 'Squat', 'category': 'Strength', 'equipment_needed': True}
        ]
    def test_get_exercise_includes_workouts(self, client, workout, squat):
        db.session.add(WorkoutExercise(workout=workout, exercise=squat, reps=8, sets=4))
        db.session.commit()
        response = client.get(f'/exercises/{squat.id}')
        assert response.status_code == 200
        entry = response.json['workout_exercises'][0]
        assert entry['workout']['date'] == '2026-10-05'
        assert entry['reps'] == 8
    def test_get_exercise_not_found(self, client):
        assert client.get('/exercises/999').status_code == 404
    def test_create_exercise(self, client):
        response = client.post(
            '/exercises',
            json={'name': 'Plank', 'category': 'Core', 'equipment_needed': False},
        )
        assert response.status_code == 201
        assert response.json['name'] == 'Plank'
    def test_create_exercise_equipment_defaults_to_false(self, client):
        response = client.post('/exercises', json={'name': 'Plank', 'category': 'Core'})
        assert response.status_code == 201
        assert response.json['equipment_needed'] is False
    @pytest.mark.parametrize(
        'payload',
        [
            {},
            {'name': 'Plank'},
            {'category': 'Core'},
            {'name': '   ', 'category': 'Core'},
            {'name': 'Plank', 'category': ''},
            {'name': 'x' * 101, 'category': 'Core'},
            {'name': 'Plank', 'category': 'Core', 'equipment_needed': 'maybe'},
        ],
    )
    def test_create_exercise_rejects_invalid_data(self, client, payload):
        response = client.post('/exercises', json=payload)
        assert response.status_code == 400
        assert Exercise.query.count() == 0
    def test_create_exercise_duplicate_name(self, client, squat):
        response = client.post('/exercises', json={'name': 'Squat', 'category': 'Legs'})
        assert response.status_code == 409
        assert Exercise.query.count() == 1
    def test_delete_exercise(self, client, workout, squat):
        db.session.add(WorkoutExercise(workout=workout, exercise=squat, reps=5, sets=5))
        db.session.commit()
        response = client.delete(f'/exercises/{squat.id}')
        assert response.status_code == 204
        assert Exercise.query.count() == 0
        assert WorkoutExercise.query.count() == 0
        assert Workout.query.count() == 1
    def test_delete_exercise_not_found(self, client):
        assert client.delete('/exercises/999').status_code == 404
class TestAddExerciseToWorkout:
    def url(self, workout, exercise):
        return f'/workouts/{workout.id}/exercises/{exercise.id}/workout_exercises'
    def test_add_with_reps_and_sets(self, client, workout, squat):
        response = client.post(self.url(workout, squat), json={'reps': 8, 'sets': 4})
        assert response.status_code == 201
        assert response.json['reps'] == 8
        assert response.json['exercise']['name'] == 'Squat'
        assert response.json['workout']['id'] == workout.id
        assert WorkoutExercise.query.count() == 1
    def test_add_with_duration_only(self, client, workout, squat):
        response = client.post(self.url(workout, squat), json={'duration_seconds': 60})
        assert response.status_code == 201
        assert response.json['reps'] is None
    @pytest.mark.parametrize(
        'payload',
        [
            {},
            {'reps': 8},
            {'sets': 4},
            {'reps': 0, 'sets': 4},
            {'reps': 8, 'sets': -1},
            {'duration_seconds': 0},
            {'reps': '8', 'sets': 4},
            {'reps': 8, 'sets': 4, 'workout_id': 99},
        ],
    )
    def test_add_rejects_invalid_data(self, client, workout, squat, payload):
        response = client.post(self.url(workout, squat), json=payload)
        assert response.status_code == 400
        assert WorkoutExercise.query.count() == 0
    def test_add_duplicate_pair(self, client, workout, squat):
        client.post(self.url(workout, squat), json={'reps': 8, 'sets': 4})
        response = client.post(self.url(workout, squat), json={'reps': 5, 'sets': 5})
        assert response.status_code == 409
        assert WorkoutExercise.query.count() == 1
    def test_add_workout_not_found(self, client, squat):
        response = client.post(f'/workouts/999/exercises/{squat.id}/workout_exercises', json={'reps': 1, 'sets': 1})
        assert response.status_code == 404
    def test_add_exercise_not_found(self, client, workout):
        response = client.post(f'/workouts/{workout.id}/exercises/999/workout_exercises', json={'reps': 1, 'sets': 1})
        assert response.status_code == 404
def test_unknown_route_returns_json_404(client):
    response = client.get('/nope')
    assert response.status_code == 404
    assert response.json == {'error': 'Resource not found.'}
def test_wrong_method_returns_json_405(client):
    assert client.put('/workouts').status_code == 405
def test_seed_file_runs_and_can_be_rerun_without_duplicating():
    for _ in range(2):
        runpy.run_path(os.path.join(os.path.dirname(__file__), 'seed.py'))
        assert Exercise.query.count() == 7
        assert Workout.query.count() == 4
        assert WorkoutExercise.query.count() == 8