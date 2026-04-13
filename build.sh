#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser if not exists
echo "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'demoformydjangoproj@gmail.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
" | python manage.py shell