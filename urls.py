from django.conf.urls import url

from plugins.unassigned import views

urlpatterns = [
    url(r'^admin/$', views.admin, name='unassigned_admin'),
    url(r'^$', views.index, name='unassigned_index'),
    url(r'^article/(?P<article_id>\d+)/$', views.unassigned_article, name='unassigned_article'),
    url(r'^article/(?P<article_id>\d+)/assign/(?P<editor_id>\d+)/type/(?P<assignment_type>[-\w.]+)/$',
        views.assign_editor, name='unassigned_assign_editor'),
    url(r'^article/(?P<article_id>\d+)/unassign/(?P<editor_id>\d+)/$', views.unassign_editor,
        name='unassigned_unassign_editor'),
    url(r'^article/(?P<article_id>\d+)/notify/(?P<editor_id>\d+)/$', views.assignment_notification,
        name='unassigned_assignment_notification'),
]
