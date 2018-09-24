from utils import models
from submission.models import STAGE_UNASSIGNED

PLUGIN_NAME = 'Unassigned Article Plugin'
DESCRIPTION = 'A workflow plugin for handling unassigned articles.'
AUTHOR = 'Andy Byers'
VERSION = '0.1'
SHORT_NAME = 'unassigned'
MANAGER_URL = 'unassigned_admin'

# Workflow Settings
IS_WORKFLOW_PLUGIN = True
HANDSHAKE_URL = 'unassigned_article'
ARTICLE_PK_IN_HANDSHAKE_URL = True
STAGE = STAGE_UNASSIGNED
KANBAN_CARD = 'unassigned/kanban_card.html'


def install():
    new_plugin, created = models.Plugin.objects.get_or_create(name=SHORT_NAME, version=VERSION, enabled=True)

    if created:
        print('Plugin {0} installed.'.format(PLUGIN_NAME))
    else:
        print('Plugin {0} is already installed.'.format(PLUGIN_NAME))


def hook_registry():
    # On site load, the load function is run for each installed plugin to generate
    # a list of hooks.
    pass