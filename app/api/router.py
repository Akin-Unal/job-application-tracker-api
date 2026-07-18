from fastapi import APIRouter

from app.api.routes import applications, auth, companies, contacts, interviews, notes, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(companies.router)
api_router.include_router(contacts.router)
api_router.include_router(applications.router)
api_router.include_router(interviews.router)
api_router.include_router(notes.router)
