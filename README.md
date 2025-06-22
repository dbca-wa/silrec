# Spatial Query Service

# Install SQS Project
```
 cd /var/www
 git clone https://github.com/dbca-wa/silrec.git
 cd silrec

 virtualenv venv
 . venv/bin/activate

 pip install -r requirements.txt 
```
     
## Add in .env
```
DEBUG=True
DATABASE_URL="postgis://<dev_user>:<dev_pw>@localhost:5432/db_name"
#
TZ=Australia/Perth
EMAIL_HOST="smtp.corporateict.domain"
DEFAULT_FROM_EMAIL='no-reply@dbca.wa.gov.au'
NOTIFICATION_EMAIL='user.name@dbca.wa.gov.au'
NON_PROD_EMAIL='user.name@dbca.wa.gov.au'
PRODUCTION_EMAIL=False
EMAIL_INSTANCE='DEV'
SECRET_KEY="ThisisNotRealKey"
SITE_PREFIX='silrec-dev'
SITE_DOMAIN='dbca.wa.gov.au'
OSCAR_SHOP_NAME='Conservation and Ecosystem Management'
BPAY_ALLOWED=False
ENABLE_DJANGO_LOGIN=True
ENABLE_WEB=True
ENABLE_CRON=False
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False

ALLOWED_HOSTS=['*']
CONSOLE_EMAIL_BACKEND=True
```


# Setup DB (in schema silrec)
```
NOTE:
File 'silrec_v3_backup_01Apr2025-OWNER-DEV_Schema_SILREC-schema_prefix_removed.sql' has:
1. removed references to SCHEMA 'public' (or 'silrec')
2. set search_path=silrec;

psql -h localhost -p 5432 -U postgres -W -f silrec_test1.sql
psql -h localhost -p 5432 -U dev -d silrec_test1 -W -f ~/projects/tmp/silrec_v3_backup_01Apr2025-OWNER-DEV_Schema_SILREC-schema_prefix_removed.sql
```

## Add in .env
```
# Needs to be dbca.wa.gov.au for ../internal URL login, else defaults to external login

./manage.py shell_plus
u = User.objects.create(email='firstname.lastname@dbca.wa.go.au', username='jawaidm', first_name='Firstname', last_name='Lastname')

In [2]:  u.set_password('pw')
In [5]:  u.is_staff=True
In [10]: u.save()

./manage.py runserver 0.0.0.0:8002

NOTE: check firewall is allowing port 8002

sudo ufw status

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere                  
80/tcp                     ALLOW       Anywhere                  
443                        ALLOW       Anywhere                  
9000:9100/tcp              ALLOW       Anywhere                  
8000:8100/tcp              ALLOW       Anywhere                  
22/tcp (v6)                ALLOW       Anywhere (v6)             
80/tcp (v6)                ALLOW       Anywhere (v6)             
443 (v6)                   ALLOW       Anywhere (v6)             
9000:9100/tcp (v6)         ALLOW       Anywhere (v6)             
8000:8100/tcp (v6)         ALLOW       Anywhere (v6)   
```


