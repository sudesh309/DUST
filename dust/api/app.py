"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from dust import __version__
from dust.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="DUST — Requirements Formalization Engine",
        version=__version__,
        description=(
            "Formalize natural-language engineering requirements into a JSON IR, "
            "EARS-normalized text, SysML v2 textual notation, and an ontology."
        ),
    )
    app.include_router(router)
    return app


app = create_app()


def main() -> None:
    """Console-script entrypoint (``dust-api``)."""
    import uvicorn

    uvicorn.run("dust.api.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
