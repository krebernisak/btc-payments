# btc_payments

Implement a Python REST web service that provides the functionality to create BTC transactions

## Development

### Install dependencies

Install dependencies into your environment by running the following in the terminal:

```bash
$ pip install -r ./btc_api/requirements/dev.txt
```

This will install dependencies for development environment including black formatter and flake8 linter (excluded in prod).

### Run development server

Start Flask development server (in debug mode) by running the following in the terminal:

```bash
$ cd btc_api/src
$ env FLASK_APP=app.py FLASK_DEBUG=1 flask run
```

### Install the hooks

Install the git hooks defined in the pre-commit file by running the following in the terminal:

```bash
$ pre-commit install
```

## Production deployment

The production environment scales Python Flask App using [Gunicorn](https://gunicorn.org/) application server and [NGINX](https://www.nginx.com/) web server using multiple Containers with Docker Compose.

### Docker Compose

```bash
$ docker-compose up --build --detach
```
