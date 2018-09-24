from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db import IntegrityError

from submission import models
from security.decorators import editor_user_required, senior_editor_user_required
from utils import ithenticate
from core import models as core_models
from review import models as review_models
from review.logic import get_assignment_content
from events import logic as event_logic
from utils import models as util_models


@editor_user_required
def admin(request):
    pass


@editor_user_required
def index(request):
    """
    Displays a list of unassigned articles.
    :param request: HttpRequest object
    :return: HttpResponse
    """
    articles = models.Article.objects.filter(stage=models.STAGE_UNASSIGNED,
                                             journal=request.journal)

    template = 'unassigned/index.html'
    context = {
        'articles': articles,
    }

    return render(request, template, context)


@editor_user_required
def unassigned_article(request, article_id):
    """
    Displays metadata of an individual article, can send details to Crosscheck for reporting.
    :param request: HttpRequest object
    :param article_id: Article PK
    :return: HttpResponse or Redirect if POST
    """
    article = get_object_or_404(models.Article, pk=article_id)

    if article.ithenticate_id and not article.ithenticate_score:
        ithenticate.fetch_percentage(request.journal, [article])

    if 'crosscheck' in request.POST:
        file_id = request.POST.get('crosscheck')
        file = get_object_or_404(core_models.File, pk=file_id)
        id = ithenticate.send_to_ithenticate(article, file)
        article.ithenticate_id = id
        article.save()
        return redirect(reverse('unassigned_article', kwargs={'article_id': article.pk}))

    current_editors = [assignment.editor.pk for assignment in
                       review_models.EditorAssignment.objects.filter(article=article)]
    editors = core_models.AccountRole.objects.filter(role__slug='editor',
                                                     journal=request.journal).exclude(user__id__in=current_editors)
    section_editors = core_models.AccountRole.objects.filter(role__slug='section-editor',
                                                             journal=request.journal
                                                             ).exclude(user__id__in=current_editors)

    template = 'unassigned/unassigned_article.html'
    context = {
        'article': article,
        'editors': editors,
        'section_editors': section_editors,
    }

    return render(request, template, context)


@senior_editor_user_required
def assign_editor(request, article_id, editor_id, assignment_type, should_redirect=True):
    """
    Allows a Senior Editor to assign another editor to an article.
    :param request: HttpRequest object
    :param article_id: Article PK
    :param editor_id: Account PK
    :param assignment_type: string, 'section-editor' or 'editor'
    :param should_redirect: if true, we redirect the user to the notification page
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(models.Article, pk=article_id)
    editor = get_object_or_404(core_models.Account, pk=editor_id)

    if not editor.has_an_editor_role(request):
        messages.add_message(request, messages.WARNING, 'User is not an Editor or Section Editor')
        return redirect(reverse('unassigned_article', kwargs={'article_id': article.pk}))

    try:
        assignment = review_models.EditorAssignment.objects.create(article=article, editor=editor, editor_type=assignment_type)
        messages.add_message(request, messages.SUCCESS, '{0} added as an Editor'.format(editor.full_name()))

        kwargs = {'user_message_content': '',
                  'editor_assignment': assignment,
                  'request': request,
                  'skip': True,
                  'acknowledgement': False}

        event_logic.Events.raise_event(event_logic.Events.ON_ARTICLE_ASSIGNED, task_object=article, **kwargs)

        if should_redirect:
            return redirect('{0}?return={1}'.format(
                reverse('unassigned_assignment_notification', kwargs={'article_id': article_id, 'editor_id': editor.pk}),
                request.GET.get('return')))
    except IntegrityError:
        messages.add_message(request, messages.WARNING,
                             '{0} is already an Editor on this article.'.format(editor.full_name()))
        if should_redirect:
            return redirect(reverse('unassigned_article', kwargs={'article_id': article_id}))


@senior_editor_user_required
def unassign_editor(request, article_id, editor_id):
    """Unassigns an editor from an article"""
    article = get_object_or_404(models.Article, pk=article_id)
    editor = get_object_or_404(core_models.Account, pk=editor_id)
    assignment = get_object_or_404(review_models.EditorAssignment, article=article, editor=editor)

    assignment.delete()

    util_models.LogEntry.add_entry(types='EditorialAction',
                                   description='{0} unassigned from article {1}'.format(editor.full_name(), article.id),
                                   level='Info',
                                   request=request, target=article)

    return redirect(reverse('unassigned_article', kwargs={'article_id': article_id}))


@senior_editor_user_required
def assignment_notification(request, article_id, editor_id):
    """
    A senior editor can sent a notification to an assigned editor.
    :param request: HttpRequest object
    :param article_id: Article PK
    :param editor_id: Account PK
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(models.Article, pk=article_id)
    editor = get_object_or_404(core_models.Account, pk=editor_id)
    assignment = get_object_or_404(review_models.EditorAssignment, article=article, editor=editor, notified=False)

    email_content = get_assignment_content(request, article, editor, assignment)

    if request.POST:

        email_content = request.POST.get('content_email')
        kwargs = {'user_message_content': email_content,
                  'editor_assignment': assignment,
                  'request': request,
                  'skip': False,
                  'acknowledgement': True}

        if 'skip' in request.POST:
            kwargs['skip'] = True

        event_logic.Events.raise_event(event_logic.Events.ON_ARTICLE_ASSIGNED_ACKNOWLEDGE, **kwargs)

        if request.GET.get('return', None):
            return redirect(request.GET.get('return'))
        else:
            return redirect(reverse('unassigned_article', kwargs={'article_id': article_id}))

    template = 'unassigned/assignment_notification.html'
    context = {
        'article': article_id,
        'editor': editor,
        'assignment': assignment,
        'email_content': email_content,
    }

    return render(request, template, context)
