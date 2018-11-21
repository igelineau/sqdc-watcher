# sqdc-watcher

Sqdc Watcher is a simple python application that allows you to monitor Sqdc (Société Québécoise du Cannabis) inventory.
It can periodically scan all products from the website and detect products that became available.

### Prerequisites

Instructions are for debian-based linux OSes.

- Pip

`apt install pip`

- Pipenv (install with pip)

`pip install pipenv`

### How to use

Run these commands while positionned at the root of the repository.

First, create the pipenv environment and install project packages

`pipenv install`

Execute the application

`pipenv run python main.py`

List available arguments

`pipenv run python main.py --help`
