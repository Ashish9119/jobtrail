# Jobtrail

Jobtrail is a web app for tracking job applications. You log each application, update its status as the process moves along, and use a dashboard to see where your job search stands. Every user has a private account and can only see and change their own records.

It is built with Django, uses SQLite for local development and PostgreSQL in production, and is ready to deploy.

---

## Contents

1. [Features](#features)
2. [Tech stack](#tech-stack)
3. [Project structure](#project-structure)
4. [How the app works](#how-the-app-works)
5. [Data model](#data-model)
6. [Pages and URLs](#pages-and-urls)
7. [Security and permissions](#security-and-permissions)
8. [Dashboard and analytics](#dashboard-and-analytics)
9. [Getting started (Windows)](#getting-started-windows)
10. [Getting started (Mac and Linux)](#getting-started-mac-and-linux)
11. [Configuration](#configuration)
12. [Running the tests](#running-the-tests)
13. [Using PostgreSQL](#using-postgresql)
14. [Deployment](#deployment)
15. [Troubleshooting](#troubleshooting)
16. [Design decisions and limitations](#design-decisions-and-limitations)
17. [Ideas for next steps](#ideas-for-next-steps)

---

## Features

- **Accounts:** sign up, log in and log out. Each person has their own private list.
- **Track applications:** company, job title, location, date applied, status, salary, job posting URL and notes.
- **Full CRUD:** add, view, edit and delete applications.
- **Search:** one box searches company, job title, location and notes.
- **Filter and sort:** filter by status; sort by date, company or salary.
- **Pagination:** 10 applications per page; your search and filters are kept when you change page.
- **Dashboard:** status totals, interview and offer rates, a 12-month trend chart and your most recent applications.
- **Admin site:** Django's built-in admin at `/admin/` for superusers.
- **Production-ready:** environment-based settings, PostgreSQL support, static files via WhiteNoise, HTTPS and cookie hardening, and a health-check URL.

---

## Tech stack

| Part | Choice |
|---|---|
| Language | Python 3.12+ |
| Framework | Django 5.2 to 6.0 (`requirements.txt` pins `>=5.2,<6.1`) |
| Database | SQLite locally, PostgreSQL in production (via `dj-database-url` and `psycopg`) |
| Static files | WhiteNoise |
| Web server | Gunicorn |
| Charts | Chart.js 4.4.1 loaded from the jsDelivr CDN |
| Config | Environment variables, with an optional `.env` file via `python-dotenv` |
| Styling | Plain CSS in `static/css/app.css` (no CSS framework) |

---

## Project structure

```
jobtrail/
├── manage.py                  Django command-line entry point
├── requirements.txt           Python dependencies
├── .env.example               Template for your local .env file
├── build.sh                   Build step used when deploying
├── Procfile                   Process definitions (Heroku-style hosts)
├── render.yaml                Render.com blueprint (web service + database)
├── config/                    Project-wide configuration
│   ├── settings.py            All settings, driven by environment variables
│   ├── urls.py                Root URL routes, including /healthz/
│   ├── wsgi.py / asgi.py      Server entry points
├── accounts/                  Sign-up, login and logout
│   ├── views.py               SignUpView (creates the user, then logs them in)
│   └── urls.py                /accounts/login/, /logout/, /signup/
├── applications/              The main app
│   ├── models.py              JobApplication model
│   ├── forms.py               Add/edit form and the search/filter form
│   ├── views.py               Dashboard, list, detail, create, update, delete
│   ├── urls.py                Routes for the app
│   ├── analytics.py           Status totals, conversion rates, monthly trend
│   ├── admin.py               Admin configuration
│   ├── tests.py               Automated tests, including ownership checks
│   └── m

How the app works
A request flows like this:
The browser asks for a URL such as /applications/.
config/urls.py hands it to the right app, and that app's urls.py picks a view.
The view checks you are logged in (otherwise it redirects you to the login page).
The view asks the database for your records only, then renders a template with them.
The template turns the data into HTML and sends it back.
Views are Django's class-based generic views (ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView). Most of the behaviour comes from Django; the project adds ownership scoping, filtering and analytics on top.
Data model
There is one main table, JobApplication.
Field
Type
Notes
user
Foreign key to User
The owner. Set by the server, never by the form. Deleting a user deletes their applications.
company
Text (200)
Required
job_title
Text (200)
Required
location
Text (200)
Optional
applied_date
Date
Defaults to today. The form rejects future dates.
status
Choice
Applied, Screening, Interviewing, Offer, Rejected, Withdrawn. Defaults to Applied.
salary
Positive integer
Optional, annual
job_url
URL (500)
Optional
notes
Long text
Optional
interviewed
Yes/No
Whether the application ever reached an interview stage (see below)
created_at, updated_at
Date and time
Set automatically
Applications are ordered newest first by default. There are database indexes on (user, status) and (user, applied_date), since almost every query filters by user first.

Why there is an interviewed field

A single status only says where an application is now. If you interview and are later rejected, the status becomes "Rejected" and the interview would vanish from your statistics. The interviewed flag remembers it.

It is set to Yes automatically whenever the status is Interviewing or Offer. You can also tick it by hand, for example for an application you have already marked Rejected after an interview.

