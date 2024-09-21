from .responses import custom_response

class CustomResponseMixin:
    """
    ViewSet의 기본 응답을 custom_response 형식으로 변환하는 Mixin
    """
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return custom_response(data=response.data, message="List fetched successfully")

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return custom_response(data=response.data, message="Details fetched successfully")

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return custom_response(data=response.data, message="Resource created successfully", code=201)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return custom_response(data=response.data, message="Resource updated successfully")

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return custom_response(data=None, message="Resource deleted successfully", code=204)