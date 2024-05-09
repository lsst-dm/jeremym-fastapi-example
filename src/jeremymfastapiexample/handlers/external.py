"""Handlers for the app's external root, ``/jeremym-fastapi-example/``."""

from typing import Annotated, Any

import httpx
import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from felis.datamodel import Schema
from httpx import AsyncClient
from safir.dependencies.http_client import http_client_dependency
from safir.dependencies.logger import logger_dependency
from safir.metadata import get_metadata
from structlog.stdlib import BoundLogger

from ..config import config
from ..models import Index

__all__ = ["get_index", "external_router"]

external_router = APIRouter()
"""FastAPI router for all external handlers."""


@external_router.get(
    "/",
    description=(
        "Document the top-level API here. By default it only returns metadata"
        " about the application."
    ),
    response_model=Index,
    response_model_exclude_none=True,
    summary="Application metadata",
)
async def get_index(
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
) -> Index:
    """GET ``/jeremym-fastapi-example/`` (the app's external root).

    Customize this handler to return whatever the top-level resource of your
    application should return. For example, consider listing key API URLs.
    When doing so, also change or customize the response model in
    `jeremymfastapiexample.models.Index`.

    By convention, the root of the external API includes a field called
    ``metadata`` that provides the same Safir-generated metadata as the
    internal root endpoint.
    """
    # There is no need to log simple requests since uvicorn will do this
    # automatically, but this is included as an example of how to use the
    # logger for more complex logging.
    logger.info("Request for application metadata")

    metadata = get_metadata(
        package_name="jeremym-fastapi-example",
        application_name=config.name,
    )
    return Index(metadata=metadata)


@external_router.get("/hello", summary="Get a friendly greeting.")
async def get_greeting() -> str:
    return "Hello, SQuaRE Services Bootcamp!"


async def fetch_data(schema_url: str) -> str:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(schema_url)
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=200, detail=f"URL not found\n{schema_url}"
            ) from e
        return response.text


@external_router.get(
    "/schema",
    summary="Get an SDM schema by name.",
    response_model=Schema,
)
async def get_schema(
    name: Annotated[str, Query()],
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
    http_client: Annotated[AsyncClient, Depends(http_client_dependency)],
) -> Schema:
    """Get an SDM schema by name."""
    schema_url = f"https://raw.githubusercontent.com/lsst/sdm_schemas/main/yml/{name}.yaml"
    logger.info("Request for SDM schema", schema_url=schema_url)
    try:
        response = await http_client.get(schema_url)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=404, detail=f"URL not found\n{schema_url}"
        ) from e
    data: dict[str, Any] = yaml.safe_load(response.text)
    return Schema(**data)
