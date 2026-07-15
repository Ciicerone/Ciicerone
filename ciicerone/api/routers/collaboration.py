import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from ciicerone.collaboration.models import CollaborationMessage, Room, RoomMember

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collaboration", tags=["Collaboration"])

room_manager = None


def set_room_manager(rm):
    global room_manager
    room_manager = rm
