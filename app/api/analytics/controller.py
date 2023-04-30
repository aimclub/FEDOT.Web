from flask_accepts import responds
from flask_restx import Namespace, Resource

from app.api.pipelines.service import pipeline_by_uid, graph_by_uid
from app.api.showcase.showcase_utils import showcase_item_from_db
from .models import BoxPlotData, PlotData
from .schema import BoxPlotDataSchema, PlotDataSchema
from .service import (get_modelling_results, get_population_analytics,
                      get_quality_analytics)

api = Namespace("Analytics", description="Operations with analytics data")


@api.route("/quality/<string:case_id>")
class QualityPlotResource(Resource):
    """Quality plot data for cases"""

    @responds(schema=PlotDataSchema, many=False)
    def get(self, case_id: str) -> PlotData:
        """Get all lines for quality plot"""
        quality_plot = get_quality_analytics(case_id)
        return quality_plot


@api.route("/generations/<string:case_id>/<string:analytic_type>")
class GenerationsPlotResource(Resource):
    """Quality plot data for cases"""

    @responds(schema=BoxPlotDataSchema, many=False)
    def get(self, case_id: str, analytic_type: str) -> BoxPlotData:
        """Get all lines for quality plot"""
        generation_plot = get_population_analytics(case_id, analytic_type=analytic_type)
        return generation_plot


@api.route("/results/<string:case_id>/<string:individual_id>")
class ResultsPlotResource(Resource):
    """Quality plot data for cases"""

    @responds(schema=PlotDataSchema, many=False)
    def get(self, case_id: str, individual_id: str) -> PlotData:
        """Get all lines for results plot"""
        case = showcase_item_from_db(case_id)
        if case.metadata.task_name == 'golem':
            pipeline = graph_by_uid(individual_id)
        else:
            pipeline = pipeline_by_uid(individual_id)
        if pipeline is None:
            raise ValueError(f'Pipeline with id {individual_id} not exists.')
        if case.metadata.task_name == 'golem':
            baseline = graph_by_uid(f'{case_id}_baseline')
        else:
            baseline = pipeline_by_uid(f'{case_id}_baseline')
        results_plot = get_modelling_results(case, pipeline, baseline)
        return results_plot
