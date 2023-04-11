from django.shortcuts import render,redirect,reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.core.mail import send_mail
from .models import *
from django.db.models import Q
import json
# Create your views here.



def home_view(request):
	if request.user.is_authenticated:
		all_posts = Post.objects.all().order_by('-date_created')
		paginator = Paginator(all_posts, 10)
		page_number = request.GET.get('page')
		if page_number == None:
			page_number = 1
		posts = paginator.get_page(page_number)
		followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
		suggestions = User.objects.exclude(pk__in=followings).exclude(username=request.user.username).order_by("?")[:6]
		return render(request, "feed.html", {
			"posts": posts,
			"suggestions": suggestions,
			"page": "all_posts"
		})
	else:
		return redirect("login")


def profile_view(request,username):
    user = User.objects.get(username=username)
    all_posts = Post.objects.filter(creater=user).order_by('-date_created')
    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')
    if page_number == None:
        page_number = 1
    posts = paginator.get_page(page_number)
    followings = []
    suggestions = []
    follower = False
    if request.user.is_authenticated:
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings).exclude(username=request.user.username).order_by("?")[:6]

        if request.user in Follower.objects.get(user=user).followers.all():
            follower = True
    
    follower_count = Follower.objects.get(user=user).followers.all().count()
    following_count = Follower.objects.filter(followers=user).count()
    return render(request, 'profile.html', {
        "username": user,
        "posts": posts,
        "posts_count": all_posts.count(),
        "suggestions": suggestions,
        "page": "profile",
        "is_follower": follower,
        "follower_count": follower_count,
        "following_count": following_count
    })

def signup_view(request):
	if request.method == "POST":
		username = request.POST["username"]
		email = request.POST["email"]
		fname = request.POST["firstname"]
		lname = request.POST["lastname"]
		profile = request.FILES.get("profile")
		cover = request.FILES.get('cover')
		password = request.POST["password"]
		confirmation = request.POST["confirmation"]
		checkUser = User.objects.filter(username=username)
		checkEmail = User.objects.filter(email=email)
		if checkUser:
			messages.error(request,"Username already taken!")
			return redirect("/signup")
		elif checkEmail:
			messages.error(request,"Account already exist with this email!")
			return redirect("/signup")
		elif password!=confirmation:
			messages.error(request,"Password and Confirm password doesn't match!")
			return redirect("/signup")
		else:
			user = User.objects.create_user(username, email, password)
			user.first_name = fname
			user.last_name = lname
			if profile is not None:						
				user.profile_pic = profile
			else:
				user.profile_pic = "profile_pic/no_pic.png"
			if cover is not None:						
				user.cover = cover
			else:
				user.cover = "covers/no_covers.png"
			user.save()
			Follower.objects.create(user=user)
			#sending account creation email
			message =  f"Dear {fname},\n\nThank you for signing up to SocialAdda. Your account has been created and you can now log in with the following credentials:\n\nUsername: {username}\nEmail: {email}\n\nWe hope you enjoy using our site!\n\nBest regards,\nThe SocialAdda team"
			send_mail("Welcome to SocialAdda",message,'SocialAdda Team <noreply@SocialAdda.com>',[email])
			login(request, user)
			messages.success(request,"User created")
			return redirect("home")
	else:
		return render(request,"account/signup.html")
def login_view(request):
	'''login'''
	if request.user.is_authenticated:
		return redirect("home")
	if request.method == 'POST':
		username=request.POST.get('username')
		password=request.POST.get('password')
		if username=="" or password == "":
			messages.error(request,"username or password is empty!")
		else:
			user=authenticate(username=username,password=password)
			if user is not None:
				login(request,user)
				messages.success(request,"Login Successfully!")
				return redirect("home")
			else:
				messages.error(request,"Invalid Credentials!")
				return redirect("/")
	else:
		return render(request,"account/login.html")

def logout_view(request):
	if request.user.is_authenticated:
		storage = messages.get_messages(request)
		storage.used=True
		logout(request)
		messages.success(request,"Logout Successfully!")
		return redirect("/")
	else:
		return redirect("/")

		
def following(request):
    if request.user.is_authenticated:
        following_user = Follower.objects.filter(followers=request.user).values('user')
        all_posts = Post.objects.filter(creater__in=following_user).order_by('-date_created')
        paginator = Paginator(all_posts, 10)
        page_number = request.GET.get('page')
        if page_number == None:
            page_number = 1
        posts = paginator.get_page(page_number)
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings).exclude(username=request.user.username).order_by("?")[:6]
        return render(request, "feed.html", {
            "posts": posts,
            "suggestions": suggestions,
            "page": "following"
        })
    else:
        return redirect('login')

def saved(request):
    if request.user.is_authenticated:
        all_posts = Post.objects.filter(savers=request.user).order_by('-date_created')

        paginator = Paginator(all_posts, 10)
        page_number = request.GET.get('page')
        if page_number == None:
            page_number = 1
        posts = paginator.get_page(page_number)

        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings).exclude(username=request.user.username).order_by("?")[:6]
        return render(request, "feed.html", {
            "posts": posts,
            "suggestions": suggestions,
            "page": "saved"
        })
    else:
        return redirect('login')
        


@login_required
def create_post(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        pic = request.FILES.get('picture')
        try:
            post = Post.objects.create(creater=request.user, content_text=text, content_image=pic)
            return redirect("home")
        except Exception as e:
            return HttpResponse(e)
    else:
        return HttpResponse("Method must be 'POST'")

@login_required
@csrf_exempt
def edit_post(request, post_id):
    pass
    if request.method == 'POST':
        text = request.POST.get('text')
        pic = request.FILES.get('picture')
        img_chg = request.POST.get('img_change')
        post_id = request.POST.get('id')
        post = Post.objects.get(id=post_id)
        try:
            post.content_text = text
            if img_chg != 'false':
                post.content_image = pic
            post.save()
            
            if(post.content_text):
                post_text = post.content_text
            else:
                post_text = False
            if(post.content_image):
                post_image = post.img_url()
            else:
                post_image = False
            
            return JsonResponse({
                "success": True,
                "text": post_text,
                "picture": post_image
            })
        except Exception as e:
            print('-----------------------------------------------')
            print(e)
            print('-----------------------------------------------')
            return JsonResponse({
                "success": False
            })
    else:
            return HttpResponse("Method must be 'POST'")

@csrf_exempt
def like_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.likers.add(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return redirect('login')

@csrf_exempt
def unlike_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.likers.remove(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return redirect('login')

@csrf_exempt
def save_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.savers.add(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return redirect('login')

@csrf_exempt
def unsave_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.savers.remove(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return redirect('login')

@csrf_exempt
def follow(request, username):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            user = User.objects.get(username=username)
            print(f".....................User: {user}......................")
            print(f".....................Follower: {request.user}......................")
            try:
                (follower, create) = Follower.objects.get_or_create(user=user)
                follower.followers.add(request.user)
                follower.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return redirect('login')

@csrf_exempt
def unfollow(request, username):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            user = User.objects.get(username=username)
            print(f".....................User: {user}......................")
            print(f".....................Unfollower: {request.user}......................")
            try:
                follower = Follower.objects.get(user=user)
                follower.followers.remove(request.user)
                follower.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return redirect('login')


@csrf_exempt
def comment(request, post_id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            data = json.loads(request.body)
            comment = data.get('comment_text')
            post = Post.objects.get(id=post_id)
            try:
                newcomment = Comment.objects.create(post=post,commenter=request.user,comment_content=comment)
                post.comment_count += 1
                post.save()
                print(newcomment.serialize())
                return JsonResponse([newcomment.serialize()], safe=False, status=201)
            except Exception as e:
                return HttpResponse(e)
    
        post = Post.objects.get(id=post_id)
        comments = Comment.objects.filter(post=post)
        comments = comments.order_by('-comment_time').all()
        return JsonResponse([comment.serialize() for comment in comments], safe=False)
    else:
        return redirect('login')

@csrf_exempt
def delete_post(request, post_id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(id=post_id)
            if request.user == post.creater:
                try:
                    delet = post.delete()
                    return HttpResponse(status=201)
                except Exception as e:
                    return HttpResponse(e)
            else:
                return HttpResponse(status=404)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return redirect('login')

def search(request):
    if request.user.is_authenticated:
        if request.method =="POST":
            search=request.POST.get("search")
            if(search==""):
                users=User.objects.all().exclude(username=request.user.username).order_by("?")
            else:
                users = User.objects.filter(
                Q(username__icontains=search) | 
                Q(first_name__icontains=search) | 
                Q(last_name__icontains=search)
            ).order_by('username')
                startswith_users = User.objects.filter(
                    Q(username__istartswith=search[0]) | 
                    Q(first_name__istartswith=search[0]) | 
                    Q(last_name__istartswith=search[0])
                ).exclude(
                    Q(username__icontains=search) | 
                    Q(first_name__icontains=search) | 
                    Q(last_name__icontains=search)
                ).order_by('username')
                users = list(users) + list(startswith_users)
                req_user =User.objects.get(username=request.user.username)
                if req_user in users:
                    users.remove(req_user)
            return render(request,"search.html",{"search_results":users,"search":search,"page":"search"})
        else:
            return HttpResponse("Method must be 'POST'")
    else:
        return redirect("login")
def edit_profile(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            user=request.user
            if(request.POST.get("name-change")=="true"):
                print("------",request.POST.get("name-change"),"------")
                user.first_name=request.POST.get("first-name")
                user.last_name=request.POST.get("last-name")
                user.save()
            if(request.POST.get("cover-img-change")=="true"):
                print("------",request.POST.get("cover-img-change"),"------")
                cover=request.FILES.get("cover-image-input")
                if cover is not None:
                    user.cover=cover
                else:
                    user.cover="covers/no_covers.png"
                user.save()
            if(request.POST.get("profile-img-change")=="true"):
                print("------",request.POST.get("profile-img-change"),"------")
                profile=request.FILES.get("profile-image-input")
                if profile is not None:
                    user.profile_pic=profile
                else:
                    user.profile_pic="profile_pic/no_pic.png"
                user.save()

            return redirect(reverse('profile',args=[request.user.username,]))
        else:
            return HttpResponse("Method must be 'POST'")
    else:
        return redirect("login")
@csrf_exempt
def more_suggestions(request):
    if request.user.is_authenticated:
        if request.method =="POST":
            offset=int(request.POST.get('offset',0))
            usernames=json.loads(request.body)["usernames"]
            followings=Follower.objects.filter(followers=request.user).values_list("user",flat=True)
            suggestions = User.objects.exclude(pk__in=followings).exclude(username=request.user.username).exclude(username__in=usernames).order_by("?")[offset:offset+6]
            if(len(User.objects.all())==len(usernames)+suggestions.count()+1):
                return JsonResponse({'suggestions':[suggestion.serialize() for suggestion in suggestions],'all_sent':True},safe=False)
            else:
                return JsonResponse({'suggestions':[suggestion.serialize() for suggestion in suggestions],'all_sent':False},safe=False)
        else:
            return HttpResponse("Method must be 'POST'")
    else:
        return redirect("login")
