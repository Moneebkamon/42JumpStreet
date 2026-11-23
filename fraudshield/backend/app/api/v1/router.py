from fastapi import APIRouter, Depends

from app.api.deps import require_admin, require_analyst
from app.api.v1.endpoints import admin, auth, feedback, settings, cases, citizen_reports, evidence, feed, health, scan, stats, takedowns

api_router = APIRouter()
analyst = [Depends(require_analyst)]

# public
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(scan.router, tags=["scan"])
api_router.include_router(citizen_reports.public_router, tags=["citizen reports"])
# staff only
api_router.include_router(feed.router, tags=["discovery"], dependencies=analyst)
api_router.include_router(stats.router, tags=["discovery"], dependencies=analyst)
api_router.include_router(cases.router, tags=["cases"], dependencies=analyst)
api_router.include_router(evidence.router, tags=["evidence"], dependencies=analyst)
api_router.include_router(takedowns.router, tags=["takedowns"], dependencies=analyst)
api_router.include_router(citizen_reports.staff_router, tags=["citizen reports"], dependencies=analyst)
api_router.include_router(admin.router, tags=["admin"], dependencies=[Depends(require_admin)])
api_router.include_router(settings.router, tags=["admin"], dependencies=[Depends(require_admin)])
api_router.include_router(feedback.router, tags=["admin"], dependencies=[Depends(require_admin)])
