from django.conf.urls import url

from plugins.unassigned import views

urlpatterns = [
    url(r'^admin/$', views.admin, name='unassigned_admin'),
    url(r'^$', views.index, name='unassigned_index'),
    url(r'^article/(?P<article_id>\d+)/$', views.unassigned_article, name='unassigned_article'),
]