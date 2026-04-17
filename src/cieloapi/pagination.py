from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    """
    Paginación personalizada.
    """
    page_size = 5  # Tamaño de página por defecto
    page_size_query_param = 'page_size'  # Parámetro en la URL para ajustar el tamaño de página
    max_page_size = 100  # Tamaño máximo permitido (opcional)