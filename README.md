<span style="font-family:Consolas">

# url shortener application programming interface

##  I. Specification
Create a webservice that shortens urls akin to tinyurl and bit.ly, and provides statistics on their usage.

Endpoints to expose:
- POST /shorten\
The request body will have the following content:

    {"url": "https://www.example.com/",
"shortcode": "asd123"}


    When no shortcode is provided it should create a random shortcode for the provided url. The shortcode has a length of 6 characters and will contain only alphanumeric characters or underscores.\
Returns http status 201 with the following body:\
{"shortcode": "asd123"}
    - Errors:
      - 400
        Url not present
      - 409
        Shortcode already in use
      - 412
        The provided shortcode is invalid

- GET /\<shortcode>\
Returns http status 302 with the Location header containing the url
    - Error:
      - 404
Shortcode not found
- GET /\<shortcode>/stats\
Returns http status 200 with the following body:

    {"created": "2017-05-10T20:45:00.000Z",
    "lastRedirect": "2018-05-16T10:16:24.666Z",
    "redirectCount": 5}

  - \<created> contains the creation datetime of the shortcode (in ISO8601)\
  \<lastRedirect> contains the datetime of the last usage of the shortcode (in ISO8601)\
  \<redirectCount> indicates the number of times the shortcode has been used
  - Error:
      - 404
    Shortcode not found


<br>

## II. Status report

__Tasks done:__
1. database creation automation
2. POST /shorten
3. GET /\<shortcode\>
4. GET /\<shortcode\>/stats
5. 7 unittests working

<br>


__Further possible improvements:__
1. separation of concerns:\
        - database initialization bash / separate python script, or Dockerfile\
        - gunicorn / waitress to handle wsgi in production
2. making database calls threadsafe
    - low level write lock transaction
3. parse with urllib parser for various URLs/URIs, such as file:///, fish:/// etc.
4. test if re.match is faster than re.search for shortcode validation
5. mock sqlalchemy responses for testing without app context
6. more unittests for errors


<br>

## III. Installation

### 1. Set environment variables for postgres in backend/backend/.env

### 2. Python packages
#### a. Using poetry:
``poetry install``

#### b. Using pip:
`python -m pip install .`
(pip supports installing pyproject.toml dependencies natively)

#### c. Using pipenv/Pipfile:
``poetry export -f requirements.txt > requirements.txt``\
``pipenv install requirements.txt``\
i.
``pipenv shell`` 
``python backend/url_shortener.py``
or \
ii.
``pipenv run backend/url_shortener.py``

> Pipfile lock should be generated separately if multiple python versions are being used. Not included in repository. Another solution to the problem is pyenv + venv/virtualenv

<br>

## IV. Usage
### A. Development
``poetry run python backend/backend/url_shortener.py``\
``poetry run pytest /tests/test_backend.py``

### B. Deployment
#### 1. Vagrant
[Installing Vagrant](https://www.vagr\antup.com/docs/installation/ "vagrant installation instructions") \
[Installing bionic64 18.04 LTS on Vagrant](https://app.vagrantup.com/hashicorp/boxes/bionic64 "bionic64 installation instructions")


#### 2. Docker + PostgreSQL
[Installing Docker on bionic64](https://docs.docker.com/install/linux/docker-ce/ubuntu/ "docker on bionic installation instructions")\
[Installing PostgreSQL service on Docker](https://docs.docker.com/engine/examples/postgresql_service/ "docker postgresql installation instructions")
[Repository of Dockerfile and entrypoint](https://github.com/docker-library/postgres/tree/4a82eb932030788572b637c8e138abb94401640c/12 "dockerfile+entrypoint repo link") 

#### 3. Create the database and its table
#### 3.1. psql
\c <database name\>
#### 3.2. Python
i.
py
from models import db\
or\
ii.
psql

i. ``requests.get('http://127.0.0.1:5000/init')`` or\
ii. db.create_all() or\
iii. psql\
``create table ...``\
based on backend/backend/models.py
#### 4. Initialize
 -  init endpoint (see III.5.)


<br>


## V. Containerized deployment
#### 1. Start Vagrant
cd \<working directory>
vagrant up
vagrant ssh

#### 2. Connect to container
docker run --rm -P -e POSTGRES_PASSWORD="..." --name /<container name> -p 5432:5432 -v $HOME/docker/postgresql/data:/var/lib/postgresql/data postgres


#### 3. Connect to postgres
* psql -h localhost -p 5432:5432 -U postgres __or__
* docker exec -it /<container name> psql -U postgres -W

#### 4. Run development server
poetry run python backend/backend/url_shortener.py

#### 5. Run browser, Postman, requests, httpie, etc. to send requests to API endpoints
[Postman download](https://www.getpostman.com/downloads/ "postman download link")\
[Requests](https://docs.python-requests.org/en/latest/)\
[httpie](https://httpie.io/download)\
[curl](https://curl.se/docs/manpage.html)




<br>


## VI. Testing
Note: unittesting only works after proper initialization, as the app context is needed in order to not check third-party elements of flask and sqlalchemy

``poetry run pytest backend/backend/tests``\
5 sample json files are provided in backend/backend/tests\
<br>
### Examples:

``curl http://localhost:5000/init``\
``http POST localhost:5000/shorten < "<path of json file>"``\
``http GET localhost:5000/<shortcode>``\
``http GET localhost:5000/<shortcode>/stats``\
``curl -X POST http://localhost:5000/shorten -H 'Content-Type: application/json' -d '{"url":"https://example.com","shortcode":"asd123"}'``

<br>


## VII. Known issue
If you get a ModuleNotFoundError after installation, create
``backend/backend/__init__.py``
and change backend/backend/url_shortener.py:26\
``from models import Shortcode, db``
to\
``from backend.models import Shortcode, db``











