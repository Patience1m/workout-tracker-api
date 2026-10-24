from datetime import date
from app import app
from models import Exercise, Workout, WorkoutExercise, db

with app.app_context():
    print('Clearing existing data...')
    WorkoutExercise.query.delete()
    Workout.query.delete()
    Exercise.query.delete()
    db.session.commit()
    print('Seeding exercises...')
    squat = Exercise(name='Barbell Squat', category='Strength', equipment_needed=True)
    bench = Exercise(name='Bench Press', category='Strength', equipment_needed=True)
    deadlift = Exercise(name='Deadlift', category='Strength', equipment_needed=True)
    pushup = Exercise(name='Push-Up', category='Bodyweight', equipment_needed=False)
    plank = Exercise(name='Plank', category='Core', equipment_needed=False)
    running = Exercise(name='Treadmill Run', category='Cardio', equipment_needed=True)
    yoga = Exercise(name='Sun Salutation', category='Flexibility', equipment_needed=False)
    exercises = [squat, bench, deadlift, pushup, plank, running, yoga]
    db.session.add_all(exercises)
    print('Seeding workouts...')
    leg_day = Workout(
        date=date(2026, 10, 5),
        duration_minutes=60,
        notes='Focus on form. Increase squat weight next week.',
    )
    upper_body = Workout(
        date=date(2026, 10, 7),
        duration_minutes=50,
        notes='Superset push-ups after bench press.',
    )
    cardio_core = Workout(
        date=date(2026, 10, 9),
        duration_minutes=40,
        notes='Steady pace on the treadmill.',
    )
    recovery = Workout(
        date=date(2026, 10, 12),
        duration_minutes=30,
        notes=None,
    )
    workouts = [leg_day, upper_body, cardio_core, recovery]
    db.session.add_all(workouts)
    db.session.commit()
    print('Linking exercises to workouts...')
    workout_exercises = [
        WorkoutExercise(workout=leg_day, exercise=squat, reps=8, sets=4),
        WorkoutExercise(workout=leg_day, exercise=deadlift, reps=5, sets=3),
        WorkoutExercise(workout=leg_day, exercise=plank, duration_seconds=60),
        WorkoutExercise(workout=upper_body, exercise=bench, reps=10, sets=4),
        WorkoutExercise(workout=upper_body, exercise=pushup, reps=15, sets=3),
        WorkoutExercise(workout=cardio_core, exercise=running, duration_seconds=1200),
        WorkoutExercise(workout=cardio_core, exercise=plank, duration_seconds=90),
        WorkoutExercise(workout=recovery, exercise=yoga, duration_seconds=900),
    ]
    db.session.add_all(workout_exercises)
    db.session.commit()
    print(
        f'Done: {Exercise.query.count()} exercises, '
        f'{Workout.query.count()} workouts, '
        f'{WorkoutExercise.query.count()} workout exercises.'
    )