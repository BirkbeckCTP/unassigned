from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse

from submission import models
from security.decorators import editor_user_required
from utils import ithenticate
from core import models as core_models
from review import models as review_models


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
