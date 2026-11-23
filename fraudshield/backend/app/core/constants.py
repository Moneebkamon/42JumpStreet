TOOL_VERSION = "fraudshield 0.1.0"

# Case lifecycle (stage 09). Display labels live in the frontend.
STATUS_NEW = "new"
STATUS_REVIEW = "under_review"
STATUS_CONFIRMED = "confirmed"
STATUS_TAKEDOWN = "takedown_requested"
STATUS_TAKEN_DOWN = "taken_down"
STATUS_CLOSED = "closed"
STATUS_FALSE_POSITIVE = "false_positive"

# from-status -> statuses it may move to. False positive is allowed from any review state.
TRANSITIONS: dict[str, tuple[str, ...]] = {
    STATUS_NEW: (STATUS_REVIEW,),
    STATUS_REVIEW: (STATUS_CONFIRMED, STATUS_FALSE_POSITIVE, STATUS_CLOSED),
    STATUS_CONFIRMED: (STATUS_TAKEDOWN, STATUS_FALSE_POSITIVE, STATUS_CLOSED),
    STATUS_TAKEDOWN: (STATUS_TAKEN_DOWN, STATUS_FALSE_POSITIVE, STATUS_CLOSED),
    STATUS_TAKEN_DOWN: (STATUS_CLOSED,),
    STATUS_CLOSED: (),
    STATUS_FALSE_POSITIVE: (),
}
OPEN_STATUSES = (STATUS_NEW, STATUS_REVIEW, STATUS_CONFIRMED, STATUS_TAKEDOWN)
