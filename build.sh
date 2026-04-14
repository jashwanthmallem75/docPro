#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py loaddata core/fixtures/initial_data.json

echo "
from django.contrib.auth.models import User
if not User.objects.filter(username='mallem').exists():
    User.objects.create_superuser('mallem', 'demoformydjangoproj@gmail.com', 'mallem')
" | python manage.py shell