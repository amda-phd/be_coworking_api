# Coworking REST API

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)![Swagger](https://img.shields.io/badge/-Swagger-%23Clojure?style=for-the-badge&logo=swagger&logoColor=white)

A REST API to manage a coworking facility.

## Usage

### Pre-requirements

In order to run this repository on your local device you'll need to have:

- Python 3.9 with `venv` environment administrator.
- MongoDB installed and running.

It will also be good to have an HTTP testing software, such as Postman or Insomnia, in order to explore the API. But the app's documentation can provide means to test the endpoint without the need to install anything else.

### Installation

1. Clone this package with

   ```bash
    git clone https://github.com/amda-phd/be_coworking_api.git
    ```

2. Move to the repo's root folder and create a `.env` file with information required to connect to your local instance of MongoDB. Make sure that you use a database that exists in your workspace. The resulting file should look like:

   ```bash
    # .env
    MONGODB_HOST=localhost
    MONGODB_PORT=27017
    MONGODB_NAME=coworking
   ```

3. Create the project's virtual environment by executing:

   ```bash
   python -m venv venv
   ```

4. Activate the environment with the command:
   1. Windows: `venv\Scripts\activate.bat`
   2. Unix and/or MacOS: `source venv/bin/activate`
5. Once you're running the environment, install all the packages contained in the `requirements.txt` with the command:

   ```bash
   pip install -r requirements.txt
   ```

### Execution

Once all the steps described in the Installation instructions have been executed, you can run your local instance of the Coworking API by running the following command from the project's root while running the aforementioned environment:

```bash
uvicorn src.main:app --reload 
```

If you don't specify a different port, the REST API will be served from [http://localhost:8000/](http://localhost:8000/)

### Tests

Although testing coverage is still a work in progress, the current version of the testing suite for this project can be executed with the following command, again from the project's root and while running its environment:

```bash
pytest tests/
```

### OpenAPI Documentation

The project serves its own OpenAPI-compliant documentation on execution. The documentation can be accessed wia the following paths:

- [http://localhost:8000/doc](http://localhost:8000/doc) for Swagger UI version.
- [http://localhost:8000/redoc](http://localhost:8000/redoc) for ReDoc version.

Both UIs allow testing the endpoints locally.

## Features

The project has been created to comply with the specs supplied by Baobab Soluciones. The complete list of endpoints it produces can be examined, along with a brief description of teach endpoint's functionalities and potential responses, by inspecting the OpenAPI documentation mentioned in the previous point.

For easier exploration, we're also providing a Postman collection to help the exploration of the endpoints. Don't foget to provide `IP` and `PORT` environment variables when running the Postman collection, or modifying the `url` collection variable with the url of your local setup.

### Considerations

- Since the sample data provided by the company required the usage of `int` numbers as `ids` for the MongoDB collections, the ability to create unique ids for each new entry has been enforced in the data models. This way of storing `ids` is, however, highly problematic. I would suggest the usage of unique handles or micro-uuids if MongoDB's ObjectIds are considered too human-unfriendly.
- The `/seed` endpoint will write **ANY** data provided into the database. Ideally, provide the data that was contained in the sample json file that was offered with the specs.
- The requirement number 7. in the company's document, "obtain the usage % of the rooms" wasn't totally clear. An endpoint that analyses the time usage for a provided time period has been produced to cover this feature.
- Python's typing library `pydantic` has been employed as a source of type hinting, database model definition and validation for the endpoints.
  
### TODOs and future work

- Testing for several endpoints is provided, but test coverage is far from perfect yet.
- Althgough OpenAPI documentation is provided, there's work left to do regarding the response models definition. All the responses remain generic.
- Error-handling middleware would help provide more detailed errors if an exception is raised at the database-communication level.
- Include linting, pre-commit hook and testing Github workflow.
