from fastapi import APIRouter, Depends

from app.api.deps import require_admin, require_analyst
# TODO(DELETE LATER - privacy): webhooks and whatsapp_link are switched off (reading WhatsApp / SMS / email is a privacy risk)
from app.api.v1.endpoints import admin, auth, devices, me, feedback, settings, cases, citizen_reports, evidence, feed, health, scan, stats, takedowns

api_router = APIRouter()
analyst = [Depends(require_analyst)]

# public
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(scan.router, tags=["scan"])
api_router.include_router(citizen_reports.public_router, tags=["citizen reports"])
# signed-in accounts (me) and extension / webhook callers (their own tokens)
api_router.include_router(me.router, tags=["me"])
# TODO(DELETE LATER - privacy): linking a WhatsApp account to read its messages
# api_router.include_router(whatsapp_link.router, tags=["me"])
api_router.include_router(devices.router, tags=["extension"])
# TODO(DELETE LATER - privacy): inbound WhatsApp / SMS message webhooks and the Manee WhatsApp bot
# api_router.include_router(webhooks.router, tags=["webhooks"])
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
