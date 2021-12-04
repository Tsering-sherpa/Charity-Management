from datetime import date

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
import requests
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, DeleteView, DetailView, UpdateView, CreateView
from django.contrib.auth.forms import PasswordChangeForm
from django.views.generic.base import View
from field_history.models import FieldHistory
from notifications.signals import notify
from twilio.rest import Client

from .forms import NgoCreationForm, BusinessForm, DonorCreationForm, DonorForm, CauseForm, UserForm, DonationForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from .decorators import unauthenticated_user
from .models import UserProfile, Causes, CustomerProfile, Donation


def index(request):
    causes = Causes.objects.all()
    donations = Donation.objects.all().order_by('date_donated')
    context = {'causes': causes, 'donations':donations}
    return render(request, 'account/index.html', context)


# for the admin dashboard
# @method_decorator(permission_required('is_superuser'), name='dispatch')
class Dashboard(TemplateView):
    template_name = 'account/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # for status in admin dashboard
        today = date.today()
        context["today_request"] = UserProfile.objects.filter(user__is_active="False",
                                                              user__date_joined__year=today.year,
                                                              user__date_joined__month=today.month
                                                              )
        context["accepted"] = UserProfile.objects.filter(user__is_active="True").count()
        context["pending"] = UserProfile.objects.filter(user__is_active="False").count()
        # for customer and worker ratio
        context["donor"] = CustomerProfile.objects.all().count()
        context["ngo"] = UserProfile.objects.all().count()
        return context


# This is for the seller registeration form
@unauthenticated_user  # using decorators here
def ngosignup(request):
    if request.method == 'POST':
        form = NgoCreationForm(request.POST)
        business_form = BusinessForm(request.POST, request.FILES)

        if form.is_valid() and business_form.is_valid():
            user = form.save()
            business = business_form.save(commit=False)
            business.user = user
            business.save()

            return redirect('login')
    else:
        form = NgoCreationForm()
        business_form = BusinessForm()

    context = {'form': form, 'business_from': business_form}
    return render(request, 'account/register.html', context)


# this is for the customer creation form
@unauthenticated_user  # using decorators here
def register(request):
    if request.method == 'POST':
        customer = DonorCreationForm(request.POST)
        customer_form = DonorForm(request.POST)

        if customer.is_valid() and customer_form.is_valid():
            # user = get_user_model().objects.create(customer.first_name, customer.last_name, customer.username, customer.password1, customer.password2. customer.email)

            user = customer.save()
            # sendConfirm(user)
            # to register seller in seller group
            customer = customer_form.save(commit=False)
            customer.user = user
            customer.save()
            return redirect('login')
    else:
        customer = DonorCreationForm()
        customer_form = DonorForm()

    context = {'customer': customer, 'customer_form': customer_form}
    return render(request, 'account/userregister.html', context)


# For the login
@unauthenticated_user  # using decorators here
def login_home(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('dashboard')
        elif user is not None and user.is_staff and not user.is_superuser:
            login(request, user)
            return redirect('dashboard')
        elif user is not None and not user.is_staff and not user.is_superuser:
            login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'Username OR Password is Incorrect')
    context = {}
    return render(request, 'account/login.html', context)


# for user logout
def logoutUser(request):
    logout(request)
    return redirect('index')


# for social account login
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "account/index.html"


# for list view of ngo
# for delete view of causes
@method_decorator(permission_required('is_superuser'), name='dispatch')
@method_decorator(login_required, name='dispatch')
class NGOListView(ListView):
    model = UserProfile
    template_name = 'account/ngo_listview.html'
    context_object_name = 'ngo'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(NGOListView, self).get_context_data(**kwargs)
        ngo = self.get_queryset()
        page = self.request.GET.get('page')
        paginator = Paginator(ngo, self.paginate_by)
        try:
            ngo = paginator.page(page)
        except PageNotAnInteger:
            ngo = paginator.page(1)
        except EmptyPage:
            ngo = paginator.page(paginator.num_pages)
        context['ngo'] = ngo
        return context


# for delete view of ngo
@method_decorator(permission_required('is_superuser'), name='dispatch')
@method_decorator(login_required, name='dispatch')
class NGODeleteView(DeleteView):
    model = UserProfile
    template_name = 'account/basetemplates/delete.html'
    success_url = reverse_lazy('list_ngo')


# for the detail view of ngo
# for delete view of ngo
@method_decorator(permission_required('is_staff'), name='dispatch')
@method_decorator(login_required, name='dispatch')
class NGODetailView(DetailView):
    model = UserProfile
    template_name = 'account/ngo_detailview.html'
    context_object_name = 'ngo_detail'


# for the update view of ngo
# for delete view of ngo
@method_decorator(login_required, name='dispatch')
class NGORequestUpdateView(UpdateView):
    model = UserProfile
    fields = ['ngo_name', 'location', 'pan', 'phone', 'document']
    template_name = 'account/ngorequest_update.html'
    success_url = reverse_lazy('list_ngo')


# for the update view of ngo
@method_decorator(login_required, name='dispatch')
class NGOProfileUpdateView(LoginRequiredMixin, TemplateView):
    user_form = UserForm
    profile_form = BusinessForm
    template_name = 'account/profile_updateview.html'

    def post(self, request):
        post_data = request.POST or None
        file_data = request.FILES or None

        user_form = UserForm(post_data, instance=request.user)
        profile_form = BusinessForm(post_data, file_data, instance=request.user.userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.error(request, 'Your profile is updated successfully!')
            return HttpResponseRedirect(reverse_lazy('profile'))

        context = self.get_context_data(
            user_form=user_form,
            profile_form=profile_form
        )

        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

# for the update view of ngo
@method_decorator(login_required, name='dispatch')
class DonorProfileUpdateView(LoginRequiredMixin, TemplateView):
    user_form = UserForm
    profile_form = DonorForm
    template_name = 'account/profile_updateview.html'

    def post(self, request):
        post_data = request.POST or None
        file_data = request.FILES or None

        user_form = UserForm(post_data, instance=request.user)
        profile_form = DonorForm(post_data, file_data, instance=request.user.customerprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.error(request, 'Your profile is updated successfully!')
            return HttpResponseRedirect(reverse_lazy('profile'))

        context = self.get_context_data(
            user_form=user_form,
            profile_form=profile_form
        )

        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# for list view of donor
@method_decorator(permission_required('is_superuser'), name='dispatch')
@method_decorator(login_required, name='dispatch')
class DonorListView(ListView):
    model = CustomerProfile
    template_name = 'account/donor_listview.html'
    context_object_name = 'donor'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(DonorListView, self).get_context_data(**kwargs)
        donor = self.get_queryset()
        page = self.request.GET.get('page')
        paginator = Paginator(donor, self.paginate_by)
        try:
            donor = paginator.page(page)
        except PageNotAnInteger:
            donor = paginator.page(1)
        except EmptyPage:
            donor = paginator.page(paginator.num_pages)
        context['donor'] = donor
        return context


# for delete view of donor
@method_decorator(permission_required('is_superuser'), name='dispatch')
@method_decorator(login_required, name='dispatch')
class DonorDeleteView(DeleteView):
    model = CustomerProfile
    template_name = 'account/basetemplates/delete.html'
    success_url = reverse_lazy('list_donor')


# for the detail view of donor
@method_decorator(permission_required('is_superuser'), name='dispatch')
@method_decorator(login_required, name='dispatch')
class DonorDetailView(DetailView):
    model = CustomerProfile
    template_name = 'account/donor_detailview.html'
    context_object_name = 'donor_detail'


# for password change
@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, ('Your password was successfully updated!'))
            return redirect('index')
        else:
            messages.error(request, ('Please correct the error below.'))
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'account/password_change_form.html', {
        'form': form
    })


# for the customer profile
@login_required(login_url='login')
def profile(request):
    context = {}
    return render(request, 'account/profile.html', context)


# for cause create view
@method_decorator(login_required, name='dispatch')
class CreateCauseView(View):
    def get(self, request):
        causecreationform = CauseForm()
        context = {
            'causecreationform': causecreationform
        }
        return render(request, 'account/cause_createview.html', context)

    def post(self, request):
        causecreationform = CauseForm(request.POST, request.FILES)
        if causecreationform.is_valid():
            causeform = causecreationform.save(commit=False)
            causeform.save()
            messages.success(request, ('Your request is created successfully'), fail_silently=True)
            return redirect('list_cause')

        context = {'causecreationform': causecreationform}
        return render(request, 'account/cause_createview.html', context)


# for list view of causes

class CausesListView(ListView):
    model = Causes
    template_name = 'account/causes_listview.html'
    context_object_name = 'causes'
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super(CausesListView, self).get_context_data(**kwargs)
        causes = self.get_queryset()
        page = self.request.GET.get('page')
        paginator = Paginator(causes, self.paginate_by)
        try:
            causes = paginator.page(page)
        except PageNotAnInteger:
            causes = paginator.page(1)
        except EmptyPage:
            causes = paginator.page(paginator.num_pages)
        context['causes'] = causes
        return context


# for delete view of causes
@method_decorator(permission_required('is_staff'), name='dispatch')
@method_decorator(login_required, name='dispatch')
class CausesDeleteView(DeleteView):
    model = Causes
    template_name = 'account/basetemplates/delete.html'
    success_url = reverse_lazy('list_cause')


# for the detail view of cause
class CausesDetailView(DetailView):
    model = Causes
    template_name = 'account/causes_detailview.html'
    context_object_name = 'cause'


# for the update view of cause
@method_decorator(login_required, name='dispatch')
class CauseUpdateView(UpdateView):
    model = Causes
    fields = ['title', 'description', 'amount_required', 'cause_image', 'status', 'priority']
    template_name = 'account/cause_updateview.html'
    success_url = reverse_lazy('list_cause')


# for the donation create view
@method_decorator(login_required, name='dispatch')
class DonationCreateView(View):
    def get(self, request):
        donationform = DonationForm()
        context = {
            'donationform': donationform
        }
        return render(request, 'account/donation_createview.html', context)

    def post(self, request):
        username = request.user
        causeId = request.POST.get('cause')
        cause = Causes.objects.get(id=causeId)
        donationform = DonationForm(request.POST)
        if donationform.is_valid():
            donationform = donationform.save(commit=False)
            donationform.save()
            messages.success(request, ('Your donation is created successfully'), fail_silently=True)
            return redirect(reverse("esewarequest") + "?o_id=" + str(donationform.id))
        print(cause)
        print(username)
        context = {'donationform': donationform, 'username': username}
        return render(request, 'account/donation_createview.html', context)


@method_decorator(login_required, name='dispatch')
class DonationListView(ListView):
    model = Donation
    template_name = 'account/donation_listview.html'
    context_object_name = 'donation'
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super(DonationListView, self).get_context_data(**kwargs)
        donation = self.get_queryset()
        page = self.request.GET.get('page')
        paginator = Paginator(donation, self.paginate_by)
        try:
            donation = paginator.page(page)
        except PageNotAnInteger:
            donation = paginator.page(1)
        except EmptyPage:
            donation = paginator.page(paginator.num_pages)
        context['donation'] = donation
        return context


# for the detail view of cause
@method_decorator(permission_required('is_staff'), name='dispatch')
class DonationDetailView(DetailView):
    model = Donation
    template_name = 'account/donation_detailview.html'
    context_object_name = 'donation'


# for the esewa payment gateway
class EsewaRequest(View):
    def get(self, request, *args, **kwargs):
        o_id = request.GET.get("o_id")
        order = Donation.objects.get(id=o_id)
        context = {'order': order}
        return render(request, 'account/esewa.html', context)


class EsewaVerifyView(View):
    def get(self, request, *args, **kwargs):
        import xml.etree.ElementTree as ET
        oid = request.GET.get("oid")
        amt = request.GET.get("amt")
        refId = request.GET.get("refId")

        url = "https://uat.esewa.com.np/epay/transrec"
        d = {
            'amt': amt,
            'scd': 'epay_payment',
            'rid': refId,
            'pid': oid,
        }
        resp = requests.post(url, d)
        root = ET.fromstring(resp.content)
        status = root[0].text.strip()

        order_id = oid.split("_")[1]
        order_obj = Donation.objects.get(id=order_id)
        if status == "Success":
            order_obj.payment_completed = True
            order_obj.save()

            # for sending system notifications this notification sends only after payment is done successfully
            sender = User.objects.get(username=self.request.user)
            receiver = User.objects.get(username=order_obj.cause.ngo.user.username)
            notify.send(sender, recipient=receiver, verb='Message', description=f"{self.request.user.first_name}"
                                                                                f"{self.request.user.last_name} donated NRP "
                                                                                f"{amt} for {order_obj.cause}")

            # for twilio SMS notification
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID')
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN')
            client = Client(account_sid, auth_token)

            message = client.messages \
                .create(
                body=f"{self.request.user.first_name}"
                     f"{self.request.user.last_name} donated NRP "
                     f"{amt} for {order_obj.cause}",
                from_=getattr(settings, 'TWILIO_NUMBER'),
                to=f'+977{order_obj.cause.ngo.phone}'
            )
            print(message.sid)
            return redirect("/")
        else:
            return redirect("/esewa-request/?o_id=" + order_id)


# for the history list veiw
@method_decorator(login_required, name='dispatch')
class HistoryListView(ListView):
    model = FieldHistory
    template_name = 'account/history_listview.html'
    context_object_name = 'history'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super(HistoryListView, self).get_context_data(**kwargs)
        histories = self.get_queryset()
        page = self.request.GET.get('page')
        paginator = Paginator(histories, self.paginate_by)
        try:
            histories = paginator.page(page)
        except PageNotAnInteger:
            histories = paginator.page(1)
        except EmptyPage:
            histories = paginator.page(paginator.num_pages)
        context['histories'] = histories
        return context


# to delete the history
@method_decorator(login_required, name='dispatch')
class HistoryDeleteView(DeleteView):
    model = FieldHistory
    template_name = 'account/basetemplates/delete.html'
    success_url = reverse_lazy('list_history')


@method_decorator(login_required, name='dispatch')
class NGORequestUpdateView(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'username', 'email', 'is_active', 'is_staff']
    template_name = 'account/ngorequest_update.html'
    success_url = reverse_lazy('list_ngo')

