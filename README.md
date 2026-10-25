# Workout Tracker API

A REST API backend for a workout tracking application used by personal trainers.
Trainers can record workouts, keep a reusable library of exercises, and attach
exercises to workouts together with the sets, reps or duration performed.

Built with **Flask**, **Flask-SQLAlchemy**, **Flask-Migrate** and **Marshmallow**,
using a SQLite database.

## Features

- Create, view and delete **workouts**
- Create, view and delete **exercises** (reusable across many workouts)
- Add an exercise to a workout with `reps`/`sets` or a `duration_seconds`
- Validation at three levels: database constraints, model validations and schema validations
- Deleting a workout or exercise also removes its linked workout exercises
- Seed script and an automated test suite

## Data model

| Model | Fields |
|-------|--------|
| `Exercise` | `id`, `name`, `category`, `equipment_needed` |
| `Workout` | `id`, `date`, `duration_minutes`, `notes` |
| `WorkoutExercise` (join table) | `id`, `workout_id`, `exercise_id`, `reps`, `sets`, `duration_seconds` |

A `Workout` has many `Exercise`s through `WorkoutExercise`, and an `Exercise` has
many `Workout`s through `WorkoutExercise`.

## Validations

| Level | Where | Rules |
|-------|-------|-------|
| **Table constraints** | `models.py` (`__table_args__`) | Exercise `name` is unique and not blank; `category` is not blank; workout `duration_minutes > 0`; `reps`, `sets` and `duration_seconds` must be positive; a `WorkoutExercise` needs reps **and** sets, or a duration; the same exercise cannot be added to the same workout twice |
| **Model validations** | `models.py` (`@validates`) | Names and categories must be non-empty strings (whitespace is trimmed); `equipment_needed` must be a boolean; `date` must be a date; `duration_minutes` must be a positive integer; `reps`, `sets`, `duration_seconds` must be positive integers |
| **Schema validations** | `schemas.py` (Marshmallow) | Required fields; length limits; `duration_minutes` between 1 and 1440; `reps`/`sets`/`duration_seconds` at least 1; strict integers (`"30"` is rejected); valid ISO dates; unknown fields rejected; a custom schema validator requires reps and sets, or a duration |

## Installation

Requires Python 3.12 and [Pipenv](https://pipenv.pypa.io/).

```bash
git clone https://github.com/Patience1m/workout-tracker-api.git
cd workout-tracker-api

pipenv install --dev      # installs dependencies (including pytest)
pipenv shell              # activates the virtual environment

cd server
export FLASK_APP=app.py

flask db upgrade head     # creates the database tables
python seed.py            # adds example data (safe to re-run)
```

## Changing the models

If you change a model, generate and apply a new migration:

```bash
flask db migrate -m "describe the change"
flask db upgrade head
```

## Running the app

From the `server` folder:

```bash
flask run --port 5555
# or
python app.py
```

The API is then available at `http://127.0.0.1:5555`.

## Running the tests

From the `server` folder:

```bash
pytest
```

The tests use an in-memory database, so they never touch your real data.

## API endpoints

All request and response bodies are JSON. Dates use the `YYYY-MM-DD` format.

### Workouts

| Method | Endpoint | Description | Success |
|--------|----------|-------------|---------|
| `GET` | `/workouts` | List all workouts | `200` |
| `GET` | `/workouts/<id>` | Show one workout with its exercises, including reps, sets and duration | `200` |
| `POST` | `/workouts` | Create a workout | `201` |
| `DELETE` | `/workouts/<id>` | Delete a workout and its workout exercises | `204` |

Example `POST /workouts` body:

```json
{ "date": "2026-11-01", "duration_minutes": 45, "notes": "Upper body" }
```

### Exercises

| Method | Endpoint | Description | Success |
|--------|----------|-------------|---------|
| `GET` | `/exercises` | List all exercises | `200` |
| `GET` | `/exercises/<id>` | Show one exercise with the workouts it appears in | `200` |
| `POST` | `/exercises` | Create an exercise | `201` |
| `DELETE` | `/exercises/<id>` | Delete an exercise and its workout exercises | `204` |

Example `POST /exercises` body (`equipment_needed` defaults to `false`):

```json
{ "name": "Push-Up", "category": "Bodyweight", "equipment_needed": false }
```

### Adding an exercise to a workout

| Method | Endpoint | Description | Success |
|--------|----------|-------------|---------|
| `POST` | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout with reps/sets or a duration | `201` |

Example bodies:

```json
{ "reps": 10, "sets": 3 }
```

```json
{ "duration_seconds": 60 }
```

### Error responses

| Status | Meaning |
|--------|---------|
| `400` | Invalid data. The body contains `errors` (schema) or `error` (model/database) |
| `404` | Workout, exercise or route not found |
| `405` | HTTP method not allowed for that route |
| `409` | Conflict: duplicate exercise name, or exercise already in that workout |

## Project structure

```
.
├── Pipfile
├── README.md
└── server/
    ├── app.py          # Flask app and route definitions
    ├── models.py       # SQLAlchemy models, relationships, constraints, model validations
    ├── schemas.py      # Marshmallow schemas and schema validations
    ├── seed.py         # Resets and seeds example data
    ├── test_app.py     # pytest suite
    └── migrations/     # Alembic migrations
```
