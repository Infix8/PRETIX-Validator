from django.utils.translation import gettext_lazy as _
from pretix.base.plugins import PluginConfig


class PluginApp(PluginConfig):
    name = 'pretix_rollno_validator'
    verbose_name = 'Roll Number Validator'

    class PretixPluginMeta:
        name = _('Roll Number Validator')
        author = 'Your Name'
        description = _('Ensures Roll Number uniqueness during ticket purchase')
        visible = True
        version = '1.0.0'
        category = 'CUSTOMIZATION'
        compatibility = 'pretix>=4.0.0'

    def ready(self):
        from . import signals  # noqa

default_app_config = 'pretix_rollno_validator.PluginApp' 