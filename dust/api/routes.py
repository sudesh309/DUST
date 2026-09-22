"""API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from dust.llm.base import LLMError
from dust.llm.factory import build_client
from dust.ontology.build import to_graph, to_mermaid, to_turtle
from dust.pipeline.orchestrator import formalize
from dust.render.ears import render_ears
from dust.render.sysml import render_sysml

from .schemas import FormalizeRequest, FormalizeResponse, OntologyArtifact, Target

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/formalize", response_model=FormalizeResponse)
def formalize_endpoint(req: FormalizeRequest) -> FormalizeResponse:
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="'text' must not be empty")

    try:
        client = build_client(provider=req.provider)
        result = formalize(req.text, client)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    targets = set(req.targets)
    response = FormalizeResponse(statements=len(result.requirements))

    if Target.ir in targets:
        response.ir = result
    if Target.ears in targets:
        response.ears = render_ears(result)
    if Target.sysml in targets:
        response.sysml = render_sysml(result)
    if Target.ontology in targets:
        response.ontology = OntologyArtifact(
            graph=to_graph(result),
            mermaid=to_mermaid(result),
            turtle=to_turtle(result),
        )
    return response
