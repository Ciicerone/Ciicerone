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


@router.get("/rooms", response_model=List[Room])
async def list_rooms(active_only: bool = Query(True)):
    if room_manager is None:
        raise HTTPException(status_code=503, detail="Room manager not initialized")
    return await room_manager.list_rooms(active_only=active_only)


@router.post("/rooms", response_model=Room, status_code=201)
async def create_room(name: str, description: str = "", created_by: str = ""):
    if room_manager is None:
        raise HTTPException(status_code=503, detail="Room manager not initialized")
    return await room_manager.create_room(name=name, created_by=created_by, description=description)


@router.get("/rooms/{room_id}", response_model=Room)
async def get_room(room_id: str):
    if room_manager is None:
        raise HTTPException(status_code=503, detail="Room manager not initialized")
    room = await room_manager.get_room(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.get("/rooms/{room_id}/members", response_model=List[RoomMember])
async def get_room_members(room_id: str):
    if room_manager is None:
        raise HTTPException(status_code=503, detail="Room manager not initialized")
    return await room_manager.get_room_members(room_id)


@router.get("/rooms/{room_id}/online", response_model=List[RoomMember])
async def get_online_users(room_id: str):
    if room_manager is None:
        raise HTTPException(status_code=503, detail="Room manager not initialized")
    return await room_manager.get_online_users(room_id)


@router.post("/rooms/{room_id}/join")
async def join_room(room_id: str, user_id: str, username: str = "", role: str = "member"):
    if room_manager is None:
        raise HTTPException(status_code=503, detail="Room manager not initialized")
    room = await room_manager.join_room(room_id, user_id, username, role)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"status": "joined", "room_id": room_id}


@router.post("/rooms/{room_id}/leave")
async def leave_room(room_id: str, user_id: str):
    if room_manager is None:
        raise HTTPException(status_code=503, detail="Room manager not initialized")
    room = await room_manager.leave_room(room_id, user_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"status": "left", "room_id": room_id}


@router.get("/health")
async def collaboration_health():
    return {
        "status": "operational" if room_manager else "unavailable",
        "rooms": len(await room_manager.list_rooms()) if room_manager else 0,
    }
