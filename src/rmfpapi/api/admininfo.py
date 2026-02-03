"""Endpoints for information for the admin"""

import logging

from fastapi import APIRouter, Depends
from libpvarki.middleware import MTLSHeader
from libpvarki.schemas.product import UserInstructionFragment
from jinja2 import Environment, FileSystemLoader

from ..config import TEMPLATES_PATH

LOGGER = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(MTLSHeader(auto_error=True))])


@router.get("/fragment", deprecated=True)
async def admin_instruction_fragment() -> UserInstructionFragment:
    """Return user instructions, we use POST because the integration layer might not keep
    track of callsigns and certs by UUID and will probably need both for the instructions"""
    template = Environment(loader=FileSystemLoader(TEMPLATES_PATH), autoescape=True).get_template("admininfo.html")
    result = UserInstructionFragment(html=template.render())
    return result
