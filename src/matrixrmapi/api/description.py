"""Descriptions API"""

from typing import Literal, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, Extra
from libpvarki.schemas.product import ProductDescription


LOGGER = logging.getLogger(__name__)

router = APIRouter()  # These endpoints are public
router_v2 = APIRouter()


PRODUCT_SHORTNAME = "matrix"


class ProductComponent(BaseModel):  # pylint: disable=too-few-public-methods
    """Project component info"""

    type: Literal["link", "markdown", "component"]
    ref: str


class ProductDescriptionExtended(BaseModel):  # pylint: disable=too-few-public-methods
    """Description of a product"""

    shortname: str = Field(description="Short name for the product, used as slug/key in dicts and urls")
    title: str = Field(description="Fancy name for the product")
    icon: Optional[str] = Field(description="URL for icon")
    description: str = Field(description="Short-ish description of the product")
    language: str = Field(description="Language of this response")
    docs: str = Field(description="Link to documentation")
    component: ProductComponent = Field(description="Component type and ref")

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic configs"""

        extra = Extra.forbid


@router.get(
    "/{language}",
    response_model=ProductDescription,
)
async def return_product_description(language: str) -> ProductDescription:
    """Fetch description from each product in manifest"""
    LOGGER.debug("Got language: {}".format(language))
    if language == "fi":
        return ProductDescription(
            shortname=PRODUCT_SHORTNAME,
            title="Matrix",
            icon=None,
            description=""""tuote" integraatioiden testaamiseen""",
            language="fi",
        )
    if language == "en":
        return ProductDescription(
            shortname=PRODUCT_SHORTNAME,
            title="Matrix",
            icon=None,
            description="Matrix messaging service",
            language="en",
        )
    # NOTE: Generally should return just the default language but this is for testing purposes
    raise HTTPException(status_code=404)


@router_v2.get(
    "/{language}",
    response_model=ProductDescriptionExtended,
)
async def return_product_description_extended(language: str) -> ProductDescriptionExtended:
    """Fetch description from each product in manifest"""
    docs_url = "https://pvarki.github.io/Docusaurus-docs/docs/android/deployapp/home/"

    if language == "fi":
        return ProductDescriptionExtended(
            shortname=PRODUCT_SHORTNAME,
            title="Feikkituote",
            icon=f"ui/{PRODUCT_SHORTNAME}/matrixlogo.svg",
            description=""""tuote" integraatioiden testaamiseen""",
            language=language,
            docs=docs_url,
            component=ProductComponent(type="component", ref=f"/ui/{PRODUCT_SHORTNAME}/remoteEntry.js"),
        )
    if language == "sv":
        return ProductDescriptionExtended(
            shortname=PRODUCT_SHORTNAME,
            title="Falsk produkt",
            icon=f"ui/{PRODUCT_SHORTNAME}/matrixlogo.svg",
            description="Falsk produkt för integrationstestning och exempel",
            language=language,
            docs=docs_url,
            component=ProductComponent(type="component", ref=f"/ui/{PRODUCT_SHORTNAME}/remoteEntry.js"),
        )
    return ProductDescriptionExtended(
        shortname=PRODUCT_SHORTNAME,
        title="Matrix",
        icon=f"ui/{PRODUCT_SHORTNAME}/matrixlogo.svg",
        description="Matrix messaging service",
        language=language,
        docs=docs_url,
        component=ProductComponent(type="component", ref=f"/ui/{PRODUCT_SHORTNAME}/remoteEntry.js"),
    )
