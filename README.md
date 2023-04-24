# Voting REST API for Lunch Restaurants

## Table of Contents

- [Architecture](#architecture)
- [Views](#views)
- [Setup and Installation](#setup-and-installation)
- [Tests](#tests)
- [Swagger Documentation](#swagger-documentation)
- [Deployment & Credentials](#deployment-and-credentials)
- [Coding Style Guide](#coding-style-guide)

## Architecture

The API is built using Django and the Django REST framework. It consists of two main models: `Restaurant` and `Vote`. The `Restaurant` model represents a restaurant with a name and a description also inherits from the base model to have basic
history about who created who edited etc. while the `Vote` model represents a user's vote for a specific restaurant on a given date. 

In order to keep the `Vote` scalable and maintainable I have decided
to create `Vote` object for each day that user voted for a restaurant. This way in worst case scenario we can have (user x restaurant) times of Vote in a single day.
In a real world application I would divide hot data from the old ones in order to optimize our queries.  

### Models

- `Restaurant`: Stores restaurant information such as name and description.
- `Vote`: Stores user votes for restaurants, including the vote weight, vote count and the date of the vote.

### Serializers

- `RestaurantSerializer`: Handles serialization and deserialization for the `Restaurant` model. This serializer is used in the main `/restaurant/` API. I could add more data here but I also don't have exact front end requirement. So just to list restaurants, I kept it simple & stupid. 
- `RestaurantRatingSerializer`: Inherits from `RestaurantSerializer` and adds a rating field to display the restaurant's rating based on votes.
- `RestaurantVoteSerializer`: Handles serialization and deserialization for the voting process.

### Utils

- `utils.py`: Contains utility functions for checking vote limits, calculating vote weights, and calculating restaurant ratings. This is basically where main logic is located.

## Views

The API has the following views:

- `RestaurantViewSet`: Handles creating, retrieving, updating, and deleting restaurants.
  - `list`: Lists all restaurants.
  - `create`: Creates a new restaurant.
  - `retrieve`: Retrieves a specific restaurant by its UUID.
  - `update`: Updates a specific restaurant.
  - `destroy`: Deletes a specific restaurant.
  - `order_by_ratings`: Lists all restaurants ordered by their ratings and number of distinct voters.

- `VoteViewSet`: Handles user votes for restaurants.
  - `post`: Allows a user to vote for a specific restaurant.


## Setup and Installation
- Copy the environment variables from `.env-example` and create your own `.env` file
Here is an example one: 
```
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mydb
MAX_VOTES_PER_DAY=5
POSTGRES_HOST=conv_db
POSTGRES_PORT=5432
```
- Build the docker image and it should just work :)

`docker-compose up --build`

- You can check `build/Dockerfile & build/bootstrap.sh` file for setup commands that is running on behind.
- Side note, in the docker image default port is exposing `8000:8000` I didn't bother to add environment variable to this but you may change if you want.

- Second side note, in order to make testing easy for you. 
I have created a management command just like `createsuperuser` but this one is called `create_superuser` 
and it creates default admin user with a default token. The management command is located in the `Restaurant` model which I don't like but, it's purpose is just to test this application so not much to do.

- **Credentials**

```markdown
email : admin@convious.com
password : superultrastrongpassword
username = admin
token : a7259cd9a5ed2bcfa8a958b7efab5151f6185987
```

## Tests

Tests are located in the `tests.py` file and cover the following functionalities:

- Restaurant CRUD operations
- Voting process and its validation
- Weighted voting system
- Rating calculation for restaurants

To run the tests, execute the following command:

```
docker exec -it container-id /bin/bash
./manage.py test
```

To run the coverage, execute the following command:
```
docker exec -it container-id /bin/bash
coverage run --source='.' manage.py test
coverage report
```

Here is the latest report with the **92%** of coverage, however tests can DEFINITELY improve more to cover all edge corners. 
```markdown
Name                                                 Stmts   Miss  Cover
------------------------------------------------------------------------
__init__.py                                              0      0   100%
convious/__init__.py                                     0      0   100%
convious/asgi.py                                         4      4     0%
convious/settings.py                                    21      0   100%
convious/urls.py                                         8      0   100%
convious/wsgi.py                                         4      4     0%
manage.py                                               12      2    83%
restaurant/__init__.py                                   0      0   100%
restaurant/admin.py                                      1      0   100%
restaurant/apps.py                                       4      0   100%
restaurant/management/__init__.py                        0      0   100%
restaurant/management/commands/__init__.py               0      0   100%
restaurant/management/commands/create_superuser.py      14     14     0%
restaurant/migrations/0001_initial.py                    8      0   100%
restaurant/migrations/__init__.py                        0      0   100%
restaurant/models.py                                    24      1    96%
restaurant/pagination.py                                 5      0   100%
restaurant/serializers.py                               48      1    98%
restaurant/tests/__init__.py                             0      0   100%
restaurant/tests/tests_api.py                           85      0   100%
restaurant/tests/tests_utils.py                         45      0   100%
restaurant/urls.py                                       4      0   100%
restaurant/utils.py                                     31      0   100%
restaurant/views.py                                     51      3    94%
------------------------------------------------------------------------
TOTAL                                                  369     29    92%

```

## Swagger Documentation

The documentation is generated using the `drf-yasg` package and is available in both Swagger and ReDoc formats. You can access the documentation at the following endpoints:

- Swagger UI: `/swagger/`
- ReDoc: `/redoc/`

## Deployment & Credentials

I have managed to deploy application to a platform called [Render](https://render.com/). TBH this is the first time I am using their platform but, it all went smoothly and I did deploy docker container directly. 
Yet I **really** don't know how stable it is going to be in that platform since it is free tier deployment, anyways. 

- Application can be accessed through https://convious-task.onrender.com 
- Debug is set to True in case you may want to see more details, if needed.
- You can access the admin and create more users if needed via https://convious-task.onrender.com/admin/ 
Admin credentials are default ones that I have mentioned earlier

```markdown
email : admin@convious.com
password : superultrastrongpassword
username = admin
token : a7259cd9a5ed2bcfa8a958b7efab5151f6185987
```
- Swagger documentation https://convious-task.onrender.com/swagger/ 
- Redoc documentation https://convious-task.onrender.com/redoc/
- In order to access the main APIs you need to have one of the following authentication
  - Session
  - Token
  - Basic

Here is two example CURL request, one for local build and one fore Render deployment.

Local request
```bash
curl  -H "Content-type: application/json" -H "Authorization: Token a7259cd9a5ed2bcfa8a958b7efab5151f6185987"   http://0.0.0.0:8000/api/restaurant/
```

Render.com deployment request
```bash
curl  -H "Content-type: application/json" -H "Authorization: Token a7259cd9a5ed2bcfa8a958b7efab5151f6185987"   https://convious-task.onrender.com/api/restaurant/
```
    
## Coding Style Guide
List of the tools that has been used in the code.

- [Black](https://github.com/psf/black) as a linter.
- [Mypy](https://mypy-lang.org/) as a type checker.
- [isort](https://pycqa.github.io/isort/) for import optimization.


Final notes from the dev:

More could have been done as always but I am happy how I designed the structure and the way this design helped me on the way. 
I believe I covered all the requirements and added more things for real world like application, like pagination and more.


Feel free to reach me out for any questions at omeralkin7@gmail.com
