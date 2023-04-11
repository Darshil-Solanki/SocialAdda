from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.contrib.auth.views import PasswordResetDoneView as BasePasswordResetDoneView
from django.contrib.auth.views import PasswordResetConfirmView as BasePasswordResetConfirmView
from django.contrib.auth.views import PasswordResetCompleteView as BasePasswordResetCompleteView
from django.urls import reverse_lazy
from .models import User
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
 
class PasswordResetView(BasePasswordResetView):
    template_name = 'account/password_reset_form.html'
    email_template_name = 'account/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    subject_template_name = 'account/password_reset_subject.txt'
    def get_user_model(self):
        return User

    form_class = PasswordResetForm
    
    def form_valid(self, form):
        try:
            user = User.objects.get(email=form.cleaned_data['email'])
        except User.DoesNotExist:
            messages.error(self.request,"There is no user with the email address provided.")
            return super().form_invalid(form)
        return super().form_valid(form) 
class PasswordResetDoneView(BasePasswordResetDoneView):
    template_name = 'account/password_reset_done.html'

class PasswordResetConfirmView(BasePasswordResetConfirmView):
    template_name = 'account/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def get_user_model(self):
        return User
class PasswordResetCompleteView(BasePasswordResetCompleteView):
    template_name = 'account/password_reset_complete.html'


urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("signup", views.signup_view, name="signup"),
    path("p/<str:username>", views.profile_view, name='profile'),
	path("home",views.home_view,name="home"),
    path("n/following", views.following, name='following'),
    path("n/saved", views.saved, name="saved"),
    path("n/createpost", views.create_post, name="createpost"),
    path("n/post/<int:id>/like", views.like_post, name="likepost"),
    path("n/post/<int:id>/unlike", views.unlike_post, name="unlikepost"),
    path("n/post/<int:id>/save", views.save_post, name="savepost"),
    path("n/post/<int:id>/unsave", views.unsave_post, name="unsavepost"),
    path("n/post/<int:post_id>/comments", views.comment, name="comments"),
    path("n/post/<int:post_id>/write_comment",views.comment, name="writecomment"),
    path("n/post/<int:post_id>/delete", views.delete_post, name="deletepost"),
    path("<str:username>/follow", views.follow, name="followuser"),
    path("<str:username>/unfollow", views.unfollow, name="unfollowuser"),
    path("n/post/<int:post_id>/edit", views.edit_post, name="editpost"),
    path("n/edit_profile",views.edit_profile,name="edit_profile"),
    path("n/more_suggestions",views.more_suggestions,name="more_suggestions"),
    path("search/",views.search,name="search"),

    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
