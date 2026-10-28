# Simple Flask Event Registration

A basic event registration form built with Flask and packaged using Docker.

## Project structure

- `app.py` — Flask application
- `requirements.txt` — Python dependency
- `Dockerfile` — builds the Docker image
- `templates/register.html` — registration form
- `templates/success.html` — success page

## Run locally

```bash
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000/register`.

## Run with Docker

Build the image:

```bash
docker build -t simple-flask-app .
```

Run the container:

```bash
docker run -p 5000:5000 simple-flask-app
```

Open `http://localhost:5000/register`.

> This is a classroom demonstration. It does not save registrations to a database, and it must not be used in production as-is. A real application should validate input, use CSRF protection, and never store plain-text passwords.
