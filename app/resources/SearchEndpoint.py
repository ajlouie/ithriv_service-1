import elasticsearch
import flask_restful
from flask import request, g

from app import elastic_index, RestException
from app.models import ThrivResource, Availability, ThrivInstitution
from app.models import Facet, FacetCount, Filter, Search
from app.resources.schema import SearchSchema, ThrivResourceSchema
from app.resources.Auth import login_optional


class SearchEndpoint(flask_restful.Resource):
    @login_optional
    def post(self):
        request_data = request.get_json()
        search, errors = SearchSchema().load(request_data)

        if errors:
            raise RestException(RestException.INVALID_OBJECT, details=errors)
        try:
            results = elastic_index.search_resources(search)
        except elasticsearch.ElasticsearchException as e:
            print(e)
            raise RestException(RestException.ELASTIC_ERROR)

        resources = []
        filterredResults = []
        for hit in results:
            resource = ThrivResource.query.filter_by(id=hit.id).first()
            if resource is not None:
                resources.append(resource)
                filterredResults.append(hit)
                # if resource.user_may_view():
                #     print(resource.id, ': ', resource.name,
                #           ' : ', resource.user_may_view())
                # else:
                #     print(resource.id, ': ', resource.name,
                #           ' : ', resource.user_may_view())
                if resource.user_may_view:
                    print(resource.id, ': ', resource.name,
                          ' : ', resource.user_may_view)
                else:
                    print(resource.id, ': ', resource.name,
                          ' : ', resource.user_may_view)

        search.total = results.hits.total
        search.resources = ThrivResourceSchema().dump(
            resources, many=True).data

        results.hits = filterredResults
        search.facets = []
        for facet_name in results.facets:
            if facet_name == "Approved":
                if 'user' in g and g.user and g.user.role == "Admin":
                    facet = Facet(facet_name)
                    facet.facetCounts = []
                    for category, hit_count, is_selected in results.facets[
                            facet_name]:
                        facet.facetCounts.append(
                            FacetCount(category, hit_count, is_selected))
                    search.facets.append(facet)
            else:
                facet = Facet(facet_name)
                facet.facetCounts = []
                for category, hit_count, is_selected in results.facets[
                        facet_name]:
                    facet.facetCounts.append(
                        FacetCount(category, hit_count, is_selected))
                search.facets.append(facet)

        return SearchSchema().jsonify(search)


class SearchEndpointOld(flask_restful.Resource):
    @login_optional
    def post(self):
        request_data = request.get_json()
        search, errors = SearchSchema().load(request_data)
        search_start = search.start

        if errors:
            raise RestException(RestException.INVALID_OBJECT, details=errors)
        try:
            resources = []
            filterredResults = []
            results = elastic_index.search_resources(search)
            total_count = 0
            while (True):
                for hit in results:
                    resource = ThrivResource.query.filter_by(id=hit.id).first()
                    if resource is not None and resource.user_may_view():
                        if len(filterredResults) < search.size:
                            resources.append(resource)
                            filterredResults.append(hit)
                        total_count = total_count+1
                        print(resource.id, ': ', resource.name,
                              ' : ', resource.user_may_view())
                    # else:
                    #     print(resource.id, ': ', resource.name,
                    #           ' : ', resource.user_may_view())

                search.start = search.start + search.size
                if results.hits.total < search.size or search.start > results.hits.total:
                    search.total = total_count
                    break
                results = elastic_index.search_resources(search)

            search.start = search_start
        except elasticsearch.ElasticsearchException as e:
            print(e)
            raise RestException(RestException.ELASTIC_ERROR)

            #     resource.name = 'Not available to view'
            #     resource.description = 'Not available to view'
            #     resource.website = 'Not available to view'
            #     resource.starts = None
            #     resource.ends = None
            #     resource.location = None
            #     resources.append(resource)
            #     filterredResults.append(hit)

        # search.total = results.hits.total
        search.resources = ThrivResourceSchema().dump(
            resources, many=True).data

        results.hits = filterredResults
        search.facets = []
        for facet_name in results.facets:
            if facet_name == "Approved":
                if 'user' in g and g.user and g.user.role == "Admin":
                    facet = Facet(facet_name)
                    facet.facetCounts = []
                    for category, hit_count, is_selected in results.facets[
                            facet_name]:
                        facet.facetCounts.append(
                            FacetCount(category, hit_count, is_selected))
                    search.facets.append(facet)
            else:
                facet = Facet(facet_name)
                facet.facetCounts = []
                for category, hit_count, is_selected in results.facets[
                        facet_name]:
                    facet.facetCounts.append(
                        FacetCount(category, hit_count, is_selected))
                search.facets.append(facet)

        return SearchSchema().jsonify(search)
