"""Endpoints for information for the end-user"""

from typing import List, Dict
import logging
import io
import zipfile
import base64

from fastapi import APIRouter, Depends
from libpvarki.middleware import MTLSHeader
from libpvarki.schemas.product import UserCRUDRequest

LOGGER = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(MTLSHeader(auto_error=True))])


def zip_pem(pem: str, filename: str) -> bytes:
    """in-memory zip of the pem"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr(filename, pem)
    return zip_buffer.getvalue()


@router.post("/fragment", deprecated=True)
async def client_instruction_fragment(user: UserCRUDRequest) -> List[Dict[str, str]]:
    """Return user instructions, we use POST because the integration layer might not keep
    track of callsigns and certs by UUID and will probably need both for the instructions"""
    zip1_bytes = zip_pem(user.x509cert, f"{user.callsign}_1.pem")
    zip2_bytes = zip_pem(user.x509cert, f"{user.callsign}_2.pem")

    return [
        {
            "title": "iFake",
            "data": f"data:application/zip;base64,{base64.b64encode(zip1_bytes).decode('ascii')}",
            "filename": f"{user.callsign}_1.zip",
        },
        {
            "title": "aFake",
            "data": f"data:application/zip;base64,{base64.b64encode(zip2_bytes).decode('ascii')}",
            "filename": f"{user.callsign}_2.zip",
        },
    ]
