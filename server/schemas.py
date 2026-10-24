from marshmallow import Schema, ValidationError, fields, validate, validates_schema

def validate_not_blank(value):
    """Reject strings that are empty or contain only whitespace."""
    if not value.strip():
        raise ValidationError('Must not be blank.')
class ExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(
        required=True,
        validate=[validate.Length(max=100), validate_not_blank],
    )
    category = fields.String(
        required=True,
        validate=[validate.Length(max=50), validate_not_blank],
    )
    equipment_needed = fields.Boolean(
        load_default=False,
        truthy={True},
        falsy={False},
    )
class WorkoutSchema(Schema):
    id = fields.Integer(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Integer(
        required=True,
        strict=True,
        validate=validate.Range(min=1, max=1440),
    )
    notes = fields.String(allow_none=True, validate=validate.Length(max=1000))
class WorkoutExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    workout_id = fields.Integer(dump_only=True)
    exercise_id = fields.Integer(dump_only=True)
    reps = fields.Integer(allow_none=True, strict=True, validate=validate.Range(min=1))
    sets = fields.Integer(allow_none=True, strict=True, validate=validate.Range(min=1))
    duration_seconds = fields.Integer(
        allow_none=True, strict=True, validate=validate.Range(min=1)
    )
    exercise = fields.Nested(ExerciseSchema, dump_only=True)
    workout = fields.Nested(WorkoutSchema, dump_only=True)
    @validates_schema
    def validate_effort(self, data, **kwargs):
        has_reps_and_sets = data.get('reps') is not None and data.get('sets') is not None
        has_duration = data.get('duration_seconds') is not None
        if not (has_reps_and_sets or has_duration):
            raise ValidationError(
                'Provide both reps and sets, or duration_seconds.', field_name='_schema'
            )
class WorkoutDetailSchema(WorkoutSchema):
    workout_exercises = fields.Nested(
        WorkoutExerciseSchema,
        many=True,
        dump_only=True,
        only=('id', 'reps', 'sets', 'duration_seconds', 'exercise'),
    )
class ExerciseDetailSchema(ExerciseSchema):
       workout_exercises = fields.Nested(
        WorkoutExerciseSchema,
        many=True,
        dump_only=True,
        only=('id', 'reps', 'sets', 'duration_seconds', 'workout'),
    )
exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)
exercise_detail_schema = ExerciseDetailSchema()
workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
workout_detail_schema = WorkoutDetailSchema()
workout_exercise_schema = WorkoutExerciseSchema()