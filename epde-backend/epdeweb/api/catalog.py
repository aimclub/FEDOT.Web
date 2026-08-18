"""What the server and the installed EPDE can do."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import __version__
from ..adapters.availability import describe_epde
from ..adapters.controls import describe_specs
from ..adapters.search import PREPROCESSORS, TOKEN_FAMILIES
from ..datasets.samples import SAMPLES
from ..schemas import Capabilities, ControlInfo, SampleInfo, TokenFamilyInfo
from ..settings import Settings
from .deps import get_run_settings

router = APIRouter(tags=["epde catalog"])


@router.get("/capabilities", response_model=Capabilities)
def capabilities(settings: Settings = Depends(get_run_settings)) -> Capabilities:
    """Whether EPDE is installed, and which of its options this build offers.

    The GUI asks this before it shows anything: the run screen is meaningless
    without EPDE, and the token families and second Pareto axis differ between
    the released version and master.
    """
    availability = describe_epde()
    families = [
        TokenFamilyInfo(
            id=family["id"],
            label=family["label"],
            description=family["description"],
            params=family["params"],
            available=(
                not availability.available or family["class"] in availability.token_families
            ),
        )
        for family in TOKEN_FAMILIES
    ]

    return Capabilities(
        module_version=__version__,
        epde_available=availability.available,
        epde_version=availability.version,
        epde_error=availability.error,
        features=availability.features,
        preprocessors=list(PREPROCESSORS),
        token_families=families,
        controls=[ControlInfo(**spec) for spec in describe_specs()],
        samples=[SampleInfo(**sample.as_dict()) for sample in SAMPLES],
        max_run_timeout_minutes=settings.max_run_timeout_minutes,
        max_concurrent_runs=settings.max_concurrent_runs,
        max_grid_nodes=settings.max_grid_nodes,
    )
