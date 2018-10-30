import os
import re

from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from markdown import markdown

class DocumentationView(TemplateView):
    template_name = 'docs/layout.html'
    static_link_re = re.compile(r'(src|href)="static')

    def get_context_data(self, **kwargs):
        filename = kwargs['filename']
        with open(os.path.join(os.path.dirname(__file__), filename)) as f:
            content = markdown(f.read())

        return super().get_context_data(
            content=mark_safe(self.static_link_re.sub(r'\1="/static', content))
        )
