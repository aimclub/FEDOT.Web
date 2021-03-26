from typing import List

from flask_accepts import responds
from flask_restx import Namespace, Resource

from .models import PlotData
from .schema import PlotDataSchema
from .service import (get_quality_analytics, get_modelling_results)

api = Namespace("Analytics", description="Operations with analytics data")


@api.route("/quality/<string:case_id>")
class QualityPlotResource(Resource):
    """Quality plot data for cases"""

    @responds(schema=PlotDataSchema, many=True)
    def get(self, case_id) -> List[PlotData]:
        """Get all lines for quality plot"""
        quality_plots = get_quality_analytics(case_id)
        return quality_plots


@api.route("/results/<string:case_id>")
class ResultsPlotResource(Resource):
    """Quality plot data for cases"""

    @responds(schema=PlotDataSchema, many=True)
    def get(self, chain_id) -> List[PlotData]:
        """Get all lines for results plot"""
        results_plots = get_modelling_results(chain_id)
        return results_plots
