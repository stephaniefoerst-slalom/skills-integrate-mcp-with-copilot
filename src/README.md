# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Register users with `student` or `mentor` role
- Login and receive bearer tokens
- Access protected endpoints with authenticated identity
- Sign up and unregister student accounts from activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| POST   | `/auth/register`                                                  | Register a user account (`email`, `password`, `role`)              |
| POST   | `/auth/login`                                                     | Login and return a bearer token                                     |
| GET    | `/auth/me`                                                        | Return the authenticated user's identity                            |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup`                              | Sign up the authenticated student for an activity                   |
| DELETE | `/activities/{activity_name}/unregister`                          | Unregister the authenticated student from an activity               |

Protected endpoints require the `Authorization: Bearer <token>` header.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
