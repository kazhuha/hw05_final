from django.core.paginator import Paginator

from yatube.settings import PAGE_COUNT


def paginate(request, object_list, limit=PAGE_COUNT):
    paginator = Paginator(object_list, limit)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
