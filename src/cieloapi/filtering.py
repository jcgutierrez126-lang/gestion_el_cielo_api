def filter_by_search_students(data, query, fields):
    """
    Filtra una lista de diccionarios (o JSON serializados) según una query y una lista de campos.
    """
    if not query:
        return data

    query = query.lower()
    return [
        item for item in data
        if any(query in str(item.get(field, '')).lower() for field in fields)
    ]


def get_status_filter(request):
    """
    Obtiene el filtro de status desde los query params.
    - Si show_inactive=true, devuelve None (sin filtro, muestra todos)
    - Si no, devuelve True (solo activos)
    """
    show_inactive = request.query_params.get('show_inactive', 'false').lower()
    if show_inactive == 'true':
        return None  # No filtrar por status
    return True  # Solo activos


def filter_by_search(data, query, fields):
    """
    Filtra una lista de objetos según una query y una lista de campos.
    """
    if not query:
        return data
    query = query.lower()
    return [
        item for item in data
        if any(query in str(getattr(item, field, '')).lower() for field in fields)
    ]

