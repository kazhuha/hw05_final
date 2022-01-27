from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """View класс для создания статичной страницы
    про автора"""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """View класс для создания статичной страницы
    про технологии"""
    template_name = 'about/tech.html'
