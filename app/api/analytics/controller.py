from flask_accepts import responds
from flask_restx import Namespace, Resource

from app.api.chains.service import chain_by_uid
from app.api.showcase.service import showcase_item_by_uid
from .models import PlotData
from .schema import PlotDataSchema
from .service import (get_modelling_results, get_quality_analytics)

api = Namespace("Analytics", description="Operations with analytics data")


@api.route("/quality/<string:case_id>")
class QualityPlotResource(Resource):
    """Quality plot data for cases"""

    @responds(schema=PlotDataSchema, many=False)
    def get(self, case_id) -> PlotData:
        """Get all lines for quality plot"""
        quality_plots = get_quality_analytics(case_id)
        return quality_plots


@api.route("/results/<string:case_id>/<string:chain_id>")
class ResultsPlotResource(Resource):
    """Quality plot data for cases"""

    @responds(schema=PlotDataSchema, many=False)
    def get(self, case_id: str, chain_id: str) -> PlotData:
        """Get all lines for results plot"""
        chain, case = chain_by_uid(chain_id), showcase_item_by_uid(case_id)
        baseline = chain_by_uid(f'{case_id}_baseline')
        results_plots = get_modelling_results(case, chain, baseline)
        return results_plots
