from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import CustomUserCreationForm, ChamaForm, AddMemberForm, ContributionForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Sum

from .models import Chama, Member, CustomUser, Contribution

User = get_user_model()

# Create your views here.
@login_required
def members_home(request):
    # get all chamas the user belongs to
    user_chamas = Chama.objects.filter(members__user=request.user)

    context = {
        'user_chamas': user_chamas
    }

    return render(request, 'app/members_home.html', context)

@login_required
def chama_members(request, chama_id):

    # ensure user belongs to this chama before showing members
    chama = get_object_or_404(Chama, id=chama_id, members__user=request.user)
    members = Member.objects.filter(chama=chama).select_related('user')

    context = {
        'chama': chama,
        'members': members
    }

    return render(request, 'app/chama_members.html', context)

@login_required
def contributions_overview(request):
    # get all groups the user belongs to
    memberships = Member.objects.filter(user=request.user).select_related('chama')
    context = {'memberships': memberships}
    return render(request, 'app/contributions_overview.html', context)

# ====================================================================================================
@login_required
def contributions_list(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)

    # ensure user is a member of this chama
    if not Member.objects.filter(user=request.user, chama=chama).exists():
        return redirect('dashboard')

    # get all contributions for this chama
    contributions = Contribution.objects.filter(
        member__chama=chama
    ).order_by('-date')

    # calculate total contributions
    total = contributions.aggregate(Sum('amount'))['amount__sum'] or 0

    return render(
        request,
        'app/contributions_list.html',
        {
            'chama': chama,
            'contributions': contributions,
            'total': total
        }
    )

# ====================================================================================================
@login_required
def add_contribution(request, chama_id):
    chama = Chama.objects.get(id=chama_id)

    # only leader/treasurer can record contributions
    if not Member.objects.filter(user=request.user, chama=chama, role__in=['leader']).exists():
        return redirect('dashboard') # unauthorised

    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save()
            return redirect('dashboard')
    else:
        form = ContributionForm()

    return render(
        request,
        'app/add_contribution.html',
        {
            'chama': chama,
            'form': form
        }
    )

# ====================================================================================================
@login_required
def add_member(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)

    # ensure only the leader can add members
    if not Member.objects.filter(user=request.user, chama=chama, role='leader').exists():
        messages.error(request, "You are not authorised to add members to this chama.")
        return redirect('dashboard') # unauthorized

    if request.method == 'POST':
        form = AddMemberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                messages.error(request, "No User with that email exists.")
                return render(request, 'app/add_member.html', {
                    'chama': chama,
                    'form': form
                })

            # prevent duplicates
            Member.objects.get_or_create(
                user = user,
                chama = chama,
                defaults = {'role': 'Member'}
            )
            messages.success(request, f"{user.username} was successfully added to {chama.name}.")
            return redirect('dashboard')
    else:
        form = AddMemberForm()
    return render(
        request,
        'app/add_member.html',
        {
            'form': form,
            'chama': chama
        }
    )

# ====================================================================================================
@login_required
def create_chama(request):
    if request.method == 'POST':
        form = ChamaForm(request.POST)
        if form.is_valid():
            chama = form.save(commit=False)
            chama.created_by = request.user
            chama.save()

            # Auto-add creator as Leader in the Member table
            Member.objects.create(
                user = request.user,
                chama = chama,
                role = 'leader'
            )

            return redirect('dashboard')
    else:
        form = ChamaForm()
    return render(request, 'app/create_chama.html', {'form': form})

# ====================================================================================================
def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

# ====================================================================================================
@login_required
def dashboard_view(request):
     # Chamas created by the current user
    chamas = Chama.objects.filter(created_by=request.user)

    # all chamas where the user is a member
    user_chamas = Member.objects.filter(user=request.user).values_list('chama', flat=True)

    # get the latest 3 contributions only from those chamas
    latest_contributions = (
        Contribution.objects.filter(member__chama__in=user_chamas)
        .select_related("member__user", "member__chama")
        .order_by("-date")[:3]
    )

    context = {
        'chamas': chamas,
        'latest_contributions': latest_contributions
    }
    return render(request, 'app/dashboard.html', context)

# ====================================================================================================
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'app/signup.html', {'form': form})

# ====================================================================================================
def login_view(request):
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(
            request, 
            username=username, 
            password=password
        )
        if user is not None:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'app/login.html')

"""
Right now, the login view expects "username". 
But many Kenyan users may try to log in with email or even phone number.
Suggestion: For Phase 1, I'll keep it simple with username. 
Later, I can add email/phone login.
"""

# ====================================================================================================
def logout_view(request):
    logout(request)
    return redirect('login')