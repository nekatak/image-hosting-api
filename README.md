Image hosting api
-----------------
Project Requirements
1. Skip the registration part, assume users are created via the admin panel.
2. Users should be able to do the following:
a. Upload images via HTTP request
b. List their images
3. There are three account tiers – Basic, Premium and Enterprise.
a. Users that have a "Basic" plan after uploading an image get:
i. A link to a thumbnail that's 200px in height
b. Users that have a "Premium" plan get:
i. A link to a thumbnail that's 200px in height
ii. A link to a thumbnail that's 400px in height
iii. A link to the originally uploaded image
c. Users that have an "Enterprise" plan get:
i. A link to a thumbnail that's 200px in height
ii. A link to a thumbnail that's 400px in height
iii. A link to the originally uploaded image
iv. Ability to fetch a link that expires after a number of seconds (user
can specify any number between 300 and 30000)
4. Admins should be able to create arbitrary plans with the following
configurable attributes:
a. Thumbnail sizes
b. Presence of the link to the originally uploaded file
c. Ability to generate expiring links
5. Admin UI should be done via django-admin
6. There should be NO custom user UI (just browsable API from DRF)
7. Please keep the following in mind:
a. Python 3.6 or above should be supported
b. Ease of running the project (use of docker-compose is a plus)
c. Tests
d. Validation
e. Performance considerations (assume there can be a lot of images and
the API is frequently accessed)

Development/Testing
-------------------

Assuming a linux dev environment: `docker`, `docker-compose`, `make` packages are needed to be installed before running any of the rest of commands for the development environment.

All operations to run/execute the project are in the makefile.
Running:
```
# this will give help for all the subcommands
make

# build local development docker image
make setup
# run db and apply migrations
make database

# run tests
make test 

# add super user for admin site, generate static files for django admin etc. and run dev server.
make createsuperuser static-files run-server
```

Users/Plans have to be created in the django-admin UI and each user needs to be assigned a plan.
There are 3 predefined plans (Basic, Premium, Enterprise)

Visit:
http://localhost:8000/admin (credentials `admin`:`123`)

After creating a user with a plan in order to get a token
```
curl --request POST \
  --url http://localhost:8000/api/token/ \
  --header 'Content-Type: application/json' \
  --data '{
	"username": "user1",
	"password": "password"
}'

# {
# 	"token": "ef6847c05d873734f9d9cdf3fbd02f571e23e6ba"
# }
```

To upload an image:
```
curl --request POST \
  --url 'http://localhost:8000/api/images/' \
  --header 'Authorization: Token <token-from-previous-request>' \
  --header 'Content-Type: multipart/form-data' \
  --form name=last \
  --form image_field=@/path/to/image/file
```

To list all images uploaded from user:
```
curl --request GET \
  --url 'http://localhost:8000/api/images/' \
  --header 'Authorization: Token <token-from-previous-request>'
```

To get the image back with one of links returned in the above response:
```
curl --request GET \
  --url http://localhost:8000/api/images/links/b7db14c4-71d1-48ac-9d13-c1e91389023d
```
