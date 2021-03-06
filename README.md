# stiflers_mom

___

## Requirements
- docker-compose

___

## Features

- aiohttp
- mypy
- pytest
- flake8
- trafaret
- docker-compose
- aio devtools
- aiohttp debug toolbar
- postgres
- alembic
- aiopg
- sqlAlchemy


## Local development
All develop settings for application are in the `/config/api.dev.yml`.

### Run
To start the project in develop mode, run the following command:

```
make run
```

or just

```
make
```

For stop work of docker containers use:

```
make stop
```

For clean up work of docker containers use:

```
make clean
```

Interactive work inside container

```
make bash # the command must be running after `make run` 
```

### Upgrade
To upgrade dependencies:

```
make upgrade
```

### Help

If needed a list of available commands
```
make help
```

### Docs

For generate sphinx docs
```
make doc
```

### Linters
To run flake8, run the following command:

```
make lint
```

The all settings connected with a `flake8` you can customize in `.flake8`.

### Type checking
To run mypy for type checking run the following command:

```
make mypy
```

The all settings connected with a `mypy` you can customize in `mypy.ini`.
___

### Testing
```
make test
```

### Database
Management of database (postgres) migrations takes place with the help of [alembic](http://alembic.zzzcomputing.com/en/latest/).

Create new migration (new file in `stiflers_mom/migrations/versions/`):

```
make migrations # the command must be running after `make run` 
```

Apply migrations:

```
make migrate # the command must be running after `make run` 
```

If u wanna create new file with tables u should import tables to `stiflers_mom/migrations/env.py`

```
import stiflers_mom.users.tables # import new files here
```

If u need to make downgrade or other special things with alembic, use `make bash`
for penetration inside the container and run native alembic's commands.

```
make bash
alembic downgrade -1
```

To connect to postgres, use the command below

```
make psql # the command must be running after `make run` 
```

## Production
All production settings for application are in the `/config/api.prod.yml`.

The production and develop containers have a little bit different and all that different describe in docker-compose.production.yml. This  is works with the command bellow:

```
make production
```

for more information [docs](https://docs.docker.com/compose/reference/overview/).
___

## Software

- python3.7
