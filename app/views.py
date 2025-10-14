from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import CustomUserCreationForm, ChamaForm, AddMemberForm, ContributionForm, UpdateUserForm, SupportMessageForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from django.db import transaction
from django.http import HttpResponseForbidden

from .models import Chama, Member, CustomUser, Contribution, VirtualAccount
from payments.models import Transaction, AuditLog

User = get_user_model()

# Create your views here.
def leave_chama_confirm(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    membership = get_object_or_404(Member, user=request.user, chama=chama)

    # Prevent leader from leaving
    if membership.role == 'leader':
        messages.error(request, "You cannot leave a chama you lead. Transfer leadership first.")
        return redirect('chama_members', chama_id=chama.id)

    if request.method == 'POST':
        membership.delete()
        messages.success(request, f'You have successfully left {chama.name}.')
        return redirect('dashboard')

    return render(request, 'app/leave_chama_confirm.html', {'chama': chama})

# ===================================================================================================
def remove_member_confirm(request, chama_id, member_id):
    chama = get_object_or_404(Chama, id=chama_id)
    leader = get_object_or_404(Member, user=request.user, chama=chama, role='leader')
    member_to_remove = get_object_or_404(Member, id=member_id, chama=chama)

    # Prevent removing yourself
    if member_to_remove.user == request.user:
        messages.error(request, "You cannot remove yourself as leader.")
        return redirect('chama_members', chama_id=chama.id)

    if request.method == 'POST':
        member_to_remove.delete()
        messages.success(request, f'{member_to_remove.user.username} has been removed from {chama.name}.')
        return redirect('chama_members', chama_id=chama.id)

    return render(request, 'app/remove_member_confirm.html', {
        'chama': chama,
        'member_to_remove': member_to_remove
    })

# ===================================================================================================
def delete_chama_confirm(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)

    # check if the current user is the leader of this chama
    if not Member.objects.filter(user=request.user, chama=chama, role='leader').exists():
        return HttpResponseForbidden("You are not authorized to delete this Chama.")
    
    if request.method == 'POST':
        chama.delete()
        messages.success(request, "Chama deleted successfully.")
        return redirect('dashboard')

    return render(request, 'app/delete_chama_confirm.html', {'chama': chama})

# ====================================================================================================
def contact_support(request):
    if request.method == "POST":
        form = SupportMessageForm(request.POST)
        if form.is_valid():
            form.save()

            messages.success(request, "Your message has been sent! Our team will get back to you soon.")
            return redirect('contact_support')
    else:
        form = SupportMessageForm()
    return render(request, 'app/contact_support.html', {'form': form})

# ====================================================================================================
def transactions_view(request):
    # get the user's chamas
    memberships = Member.objects.filter(user=request.user)
    chamas = [m.chama for m in memberships]

    # get all transactions and audit logs for those chamas
    transactions = Transaction.objects.filter(chama__in=chamas).order_by('-timestamp')
    audit_logs = AuditLog.objects.filter(chama__in=chamas).order_by('-timestamp')

    # handle filter toggle: deposit / withdrawal / all
    filter_type = request.GET.get('type', 'all')

    if filter_type == 'deposit':
        transactions = transactions.filter(transaction_type='deposit')
        audit_logs = audit_logs.filter(action_type='deposit')
    elif filter_type == 'withdrawal':
        transactions = transactions.filter(transaction_type='withdrawal')
        audit_logs = audit_logs.filter(action_type='withdrawal')
    
    context = {
        'transactions': transactions,
        'audit_logs': audit_logs,
        'filter_type': filter_type
    }
    return render(request, 'app/transactions.html', context)

# ====================================================================================================
@login_required
def withdraw_view(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)

    # Verify if user is a leader of this chama
    member = Member.objects.filter(user=request.user, chama=chama, role='leader').first()
    if not member:
        return render(request, "payments/withdraw_form.html", {
            "chama": chama,
            "error_message": "Only chama leaders can withdraw funds."
        })

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount'))
            phone = request.POST.get('phone_number')

            # Ensure valid amount
            if amount <= 0:
                return render(request, "payments/withdraw_form.html", {
                    "chama": chama,
                    "error_message": "Invalid withdrawal amount."
                })

            # Use atomic block to ensure balance + transaction integrity
            with transaction.atomic():
                account = VirtualAccount.objects.filter(chama=chama, member=None).select_for_update().first()
                if not account or account.balance < amount:
                    return render(request, "payments/withdraw_form.html", {
                        "chama": chama,
                        "error_message": "Insufficient balance."
                    })

                # Deduct from chama account
                account.balance -= amount
                account.save()

                # Record withdrawal transaction
                txn = Transaction.objects.create(
                    chama=chama,
                    member = member,
                    initiated_by = request.user.username,
                    amount=amount,
                    checkout_id=f"WITHDRAW-{chama.id}-{request.user.id}-{Transaction.objects.count()+1}",
                    mpesa_code=f"WDR{Transaction.objects.count()+1}",
                    phone_number=phone,
                    status="Simulated",
                    transaction_type="withdrawal",
                )
                # AuditLog auto-created by signal, no manual log needed

            # Redirect to transaction list after success
            return redirect('transactions')

        except Exception as e:
            return render(request, "payments/withdraw_form.html", {
                "chama": chama,
                "error_message": f"Withdrawal failed: {str(e)}"
            })

    return render(request, "payments/withdraw_form.html", {"chama": chama})

# ====================================================================================================
def transaction_list(request):
    # get all chamas the user belongs to
    memberships = Member.objects.filter(user=request.user)
    chama_ids = memberships.values_list('chama_id', flat=True)

    # filter transactions for these chamas
    transactions = Transaction.objects.filter(chama_id__in=chama_ids).order_by('-timestamp')
    return render(request, "app/transactions.html", {"transactions": transactions})

# ====================================================================================================
def accounts_view(request):
    memberships = Member.objects.filter(user=request.user)
    chamas = [m.chama for m in memberships]
    accounts = []

    for chama in chamas:
        # get the chama's main account
        main_account = VirtualAccount.objects.filter(chama=chama, member=None).first()

        # check if the currrent user is the leader of this chama
        is_leader = Member.objects.filter(
            user = request.user,
            chama = chama,
            role = 'leader'
        ).exists()

        accounts.append({
            "chama": chama,
            "account_number": main_account.account_number if main_account else chama.account_number,
            "balance": main_account.balance if main_account else 0,
            "is_leader": is_leader,
        })
    return render(request, "app/accounts.html", {"accounts": accounts})

# ====================================================================================================
@login_required
def members_home(request):
    # get all memberships for this user (so you can access chama + role)
    memberships = Member.objects.filter(user=request.user).select_related("chama")

    context = {
        'memberships': memberships
    }
    return render(request, 'app/members_home.html', context)

# ====================================================================================================
@login_required
def chama_members(request, chama_id):
    # Ensure user belongs to this chama before showing members
    chama = get_object_or_404(Chama, id=chama_id, members__user=request.user)
    members = Member.objects.filter(chama=chama).select_related('user')

    # Get the current user's membership in this chama
    current_member = Member.objects.get(chama=chama, user=request.user)

    context = {
        'chama': chama,
        'members': members,
        'current_member': current_member,
    }

    return render(request, 'app/chama_members.html', context)


# ====================================================================================================
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
        form = ContributionForm(request.POST, chama=chama)
        if form.is_valid():
            contribution = form.save()
            return redirect('dashboard')
    else:
        form = ContributionForm(chama=chama)

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
def about_view(request):
    return render(request, 'app/about.html')

# ====================================================================================================
def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

# ====================================================================================================
@login_required
def dashboard_view(request):
    memberships = Member.objects.filter(user=request.user).select_related('chama')

    # Separate leader and member chamas
    leader_chamas = []
    member_chamas = []

    for m in memberships:
        chama = m.chama

        # Safely get chama balance
        first_account = chama.virtual_accounts.first()
        chama.balance_display = first_account.balance if first_account else 0

        # Sort into leader/member lists
        if m.role == 'leader':
            leader_chamas.append(chama)
        else:
            member_chamas.append(chama)

    # Summary statistics
    total_chamas = memberships.count()
    total_members = Member.objects.filter(chama__in=[m.chama for m in memberships]).count()

    # Calculate total balance across user’s chamas
    total_balance = sum(
        chama.balance_display for chama in leader_chamas + member_chamas
    )

    # Recent transactions (latest 5)
    recent_transactions = (
        Contribution.objects.filter(member__user=request.user)
        .select_related('member', 'member__user')
        .order_by('-date')[:5]
    )

    context = {
        'leader_chamas': leader_chamas,
        'member_chamas': member_chamas,
        'total_chamas': total_chamas,
        'total_members': total_members,
        'total_balance': total_balance,
        'recent_transactions': recent_transactions,
    }
    print("Context leader chamas:", leader_chamas)


    return render(request, 'app/dashboard.html', context)
# ====================================================================================================
@login_required
def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        user_form = UpdateUserForm(request.POST or None, instance=current_user)

        if user_form.is_valid():
            user_form.save()

            login(request, current_user)
            messages.success(request, "User Has Been updated successfully!!")
            return redirect('dashboard')
        return render(request, 'app/update_user.html', {'user_form': user_form})
    else:
        messages.error(request, "You must be logged in to update your profile.")
        return redirect('login')

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
            messages.success(request, "You have being logged in successfully.")
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