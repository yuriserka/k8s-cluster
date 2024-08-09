from django.http import HttpResponse, JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views import View
import json


class HelloWorldView(View):
    async def get(self, request: HttpRequest) -> HttpResponse:
        query_params = request.GET
        name = query_params.get('name')

        if name:
            return JsonResponse({'message': f'Hello, {name}!'})

        return HttpResponseBadRequest('Missing name query parameter')

    async def post(self, request: HttpRequest) -> HttpResponse:
        request_body = request.body
        if not request_body:
            return HttpResponseBadRequest('Missing request body')

        json_body = json.loads(request_body.decode('utf-8'))
        name = json_body.get('name')

        if name:
            return JsonResponse({'message': f'Hello, {name}!'})

        return HttpResponseBadRequest('Missing name in request body')
