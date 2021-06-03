from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q, F
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.generic import ListView
import io
from xlsxwriter.workbook import Workbook

from .models import Consumption, Category, God, Polugodie, Month, \
    AddressOfTheMunicipalOrganizations, AddressGroup, Address, MunicipalOrganizations, Quarter
from website.forms import UserRegisterForm, UserLoginForm, AddDataForm, MonthYear, OrganizationsForm

from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin


def index(request):
    return render(request, 'website/main.html')


class AdressList(LoginRequiredMixin, generic.ListView):
    model = Consumption
    template_name = 'website/main.html'
    context_object_name = 'adress'

    def get_queryset(self):
        return Consumption.objects.all()


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # авто логин в систему
            messages.success(request, 'Вы успешно зарегистрировались')
            return redirect('index')
        else:
            messages.error(request, 'Ошибка регистрации')
    else:
        form = UserRegisterForm()
    return render(request, 'website/registration.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = UserLoginForm()
    return render(request, 'website/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


def add_data_adress(request, category_id):
    adress_list = AddressOfTheMunicipalOrganizations.objects.filter(
        municipalOrganization__title=request.user.profile.organization.title)
    print(adress_list, 99)
    str_adress_list = []
    for i in adress_list:
        str_adress_list.append(str(i))

    x = len(adress_list)
    FS = formset_factory(AddDataForm, extra=x)
    category_for_post = Category.objects.get(pk=category_id)
    if request.method == 'POST':
        form = FS(request.POST, request.FILES)
        m_y_form = MonthYear(request.POST)
        zip_list = zip(adress_list, form)
        if all([form.is_valid(), m_y_form.is_valid()]):
            i = 0
            month = m_y_form.cleaned_data['month']
            god = m_y_form.cleaned_data['god']
            for form in form:
                if form.cleaned_data:
                    fact = form.cleaned_data['fact']
                    adress = adress_list[i]
                    limit = form.cleaned_data['limit']
                    explanatory_note = form.cleaned_data['explanatory_note']
                    if fact > limit and not explanatory_note:
                        print(888)
                        messages.error(request,
                                       'Внимание по одному из адресов факт превышает лимит, необходимо прикрепить пояснительную записку!')
                        return redirect(request.path)
                    note = form.cleaned_data['note']
                    data = Consumption(address_of_the_municipal_organization=adress, fact=fact, limit=limit,
                                       category=category_for_post, month=month, god=god,
                                       explanatory_note=explanatory_note,
                                       note=note)
                    data.save()
                    i = i + 1
            messages.success(request, 'Данные успешно добавлены')
            return redirect(request.path)
        else:
            messages.error(request, 'Ошибка! Данные не отправлены')
    else:
        form = FS()
        m_y_form = MonthYear()
        zip_list = zip(adress_list, form)
    context = {'form': form, 'm_y_form': m_y_form, 'adress_list': str_adress_list, 'category': category_for_post,
               'zip_list': zip_list}
    return render(request, 'website/add_data_adress.html', context)


def view_data_adress(request, category_id, year_id, month_id):
    year = God.objects.get(pk=year_id)
    month = Month.objects.get(pk=month_id)
    sum_data = Consumption.objects.filter(category=category_id).filter(
        god=year_id).filter(month=month_id).filter(
        address_of_the_municipal_organization__municipalOrganization=request.user.profile.organization)
    sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                        otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))

    category = Category.objects.get(pk=category_id)
    adress_list = AddressOfTheMunicipalOrganizations.objects.filter(
        municipalOrganization__title=request.user.profile.organization.title)

    all_address_of_the_municipal_organizations = AddressOfTheMunicipalOrganizations.objects.filter(
        municipalOrganization=request.user.profile.organization)

    filtered_group_data = AddressGroup.objects.filter(
        TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization__title=request.user.
            profile.organization.title).distinct()
    group_data_filtered = filtered_group_data.annotate(
        fact=Sum('TheAddressGroup__consumption__fact',
                 filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
        limit=Sum('TheAddressGroup__consumption__limit',
                  filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
        otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                       filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                                TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
        otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                               filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                                        TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                        TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
        sum=Sum('TheAddressGroup__consumption__sum',
                filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                         TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')
    group_data_3 = group_data_filtered.annotate(otklonenie_new=F('limit') - F('fact'))
    group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

    list_group_data = []
    # for one_address in all_address_of_the_municipal_organizations:
    #     if (one_address.group is None):
    #         table_address_without_group_data = Consumption.objects.filter(
    #             address_of_the_municipal_organization=one_address).filter(god=God.objects.get(pk=year_id)).filter(
    #             month=Month.objects.get(
    #                 pk=month_id)).filter(category=Category.objects.get(pk=category_id))
    #         for one_table_address_without_group_data in table_address_without_group_data:
    #             list_group_data.append(one_table_address_without_group_data)
    #     elif one_address.group not in list_group_data:
    for one_group_data in group_data_4:
        list_group_data.append(one_group_data)
        table_address_with_group_data = Consumption.objects.filter(
            address_of_the_municipal_organization__group=one_group_data).filter(
            god=God.objects.get(pk=year_id)).filter(month=Month.objects.get(
            pk=month_id)).filter(category=Category.objects.get(pk=category_id))
        for one_table_address_with_group_data in table_address_with_group_data:
            list_group_data.append(one_table_address_with_group_data)
    # print(list_group_data, 444)

    return render(request, 'website/view_consumption.html',
                  {'all_address': all_address_of_the_municipal_organizations,
                   'list_group_data': list_group_data, 'category': category,
                   'year': year, 'month': month, 'sum_data_final': sum_data_final})


def view_data_adress_admin(request, category_id, year_id, month_id):
    year = God.objects.get(pk=year_id)
    month = Month.objects.get(pk=month_id)
    category = Category.objects.get(pk=category_id)

    sum_data = Consumption.objects.filter(category=category_id).filter(
        god=year_id).filter(month=month_id)
    # print(sum_data)
    sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                        otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))
    # print(sum_data_final)

    if request.method == 'POST':
        form = OrganizationsForm(request.POST)
        if form.is_valid():
            organization = form.cleaned_data['organizations']
            all_address_of_the_municipal_organizations = AddressOfTheMunicipalOrganizations.objects.filter(
                municipalOrganization=organization).order_by('address')
            filtered_group_data = AddressGroup.objects.filter(
                TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization__title=organization).distinct()
            group_data_filtered = filtered_group_data.annotate(
                fact=Sum('TheAddressGroup__consumption__fact',
                         filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                                  TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                  TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
                limit=Sum('TheAddressGroup__consumption__limit',
                          filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
                otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                               filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                                        TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                        TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
                otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                                       filter=Q(
                                           TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(
                                               pk=category_id))),
                sum=Sum('TheAddressGroup__consumption__sum',
                        filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                                 TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                 TheAddressGroup__consumption__category=Category.objects.get(
                                     pk=category_id)))).order_by('TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')
            # print(group_data_filtered)

            list_group_data = []
            for one_address in all_address_of_the_municipal_organizations:
                if (one_address.group is None):
                    table_address_without_group_data = Consumption.objects.filter(
                        address_of_the_municipal_organization=one_address).filter(
                        god=God.objects.get(pk=year_id)).filter(
                        month=Month.objects.get(
                            pk=month_id)).filter(category=Category.objects.get(pk=category_id))
                    for one_table_address_without_group_data in table_address_without_group_data:
                        list_group_data.append(one_table_address_without_group_data)
                elif one_address.group not in list_group_data:
                    for one_group_data in group_data_filtered:
                        list_group_data.append(one_group_data)
                        table_address_with_group_data = Consumption.objects.filter(
                            address_of_the_municipal_organization__group=one_group_data).filter(
                            god=God.objects.get(pk=year_id)).filter(month=Month.objects.get(
                            pk=month_id)).filter(category=Category.objects.get(pk=category_id))
                        for one_table_address_with_group_data in table_address_with_group_data:
                            list_group_data.append(one_table_address_with_group_data)
            # print(list_group_data, 444)

            return render(request, 'website/view_consumption.html',
                          {'all_address': all_address_of_the_municipal_organizations,
                           'list_group_data': list_group_data, 'category': category,
                           'year': year, 'month': month, 'form': form, 'sum_data_final': sum_data_final})
    else:
        form = OrganizationsForm()
        all_address_of_the_municipal_organizations = AddressOfTheMunicipalOrganizations.objects.all().order_by('address')
        print(all_address_of_the_municipal_organizations, 555555555)
        filtered_group_data = AddressGroup.objects.all().distinct()
        group_data_filtered = filtered_group_data.annotate(
            fact=Sum('TheAddressGroup__consumption__fact',
                     filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
            limit=Sum('TheAddressGroup__consumption__limit',
                      filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
            otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                           filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
            otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                                   filter=Q(
                                       TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                                       TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                       TheAddressGroup__consumption__category=Category.objects.get(
                                           pk=category_id))),
            sum=Sum('TheAddressGroup__consumption__sum',
                    filter=Q(TheAddressGroup__consumption__month__name=Month.objects.get(pk=month_id),
                             TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                             TheAddressGroup__consumption__category=Category.objects.get(
                                 pk=category_id)))).order_by('TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')
        group_data_3 = group_data_filtered.annotate(otklonenie_new=F('limit') - F('fact'))
        group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

        list_group_data = []
        for one_address in all_address_of_the_municipal_organizations:
            if (one_address.group is None):
                table_address_without_group_data = Consumption.objects.filter(
                    address_of_the_municipal_organization=one_address).filter(
                    god=God.objects.get(pk=year_id)).filter(
                    month=Month.objects.get(
                        pk=month_id)).filter(category=Category.objects.get(pk=category_id))
                for one_table_address_without_group_data in table_address_without_group_data:
                    list_group_data.append(one_table_address_without_group_data)
            elif one_address.group not in list_group_data:
                for one_group_data in group_data_4:
                    list_group_data.append(one_group_data)
                    table_address_with_group_data = Consumption.objects.filter(
                        address_of_the_municipal_organization__group=one_group_data).filter(
                        god=God.objects.get(pk=year_id)).filter(month=Month.objects.get(
                        pk=month_id)).filter(category=Category.objects.get(pk=category_id))
                    for one_table_address_with_group_data in table_address_with_group_data:
                        list_group_data.append(one_table_address_with_group_data)
        # print(list_group_data, 444)

        return render(request, 'website/view_consumption.html',
                      {'all_address': all_address_of_the_municipal_organizations,
                       'list_group_data': list_group_data, 'category': category,
                       'year': year, 'month': month, 'form': form, 'sum_data_final': sum_data_final})
#Доделать
# def view_data_adress_admin(request, category_id, year_id, month_id):
#     year = God.objects.get(pk=year_id)
#     month = Month.objects.get(pk=month_id)
#     category = Category.objects.get(pk=category_id)
#
#     sum_data = Consumption.objects.filter(category=category_id).filter(
#         god=year_id).filter(month=month_id)
#     # print(sum_data)
#     sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
#                                         otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))
#     # print(sum_data_final)
#
#     if request.method == 'POST':
#         form = OrganizationsForm(request.POST)
#         if form.is_valid():
#             organization = form.cleaned_data['organizations']
#             group_data_1 = AddressGroup.objects.all().distinct()
#
#             all_address_1 = AddressOfTheMunicipalOrganizations.objects.all()
#
#             all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
#                                                             filter=(Q(consumption__month=Month.objects.get(pk=month_id),
#                                                                       consumption__god=God.objects.get(pk=year_id),
#                                                                       consumption__category=Category.objects.get(
#                                                                           pk=category_id),
#                                                                       consumption__address_of_the_municipal_organization__municipalOrganization=organization))),
#                                                    limit=Sum('consumption__limit',
#                                                              filter=(
#                                                                  Q(consumption__month=Month.objects.get(pk=month_id),
#                                                                    consumption__god=God.objects.get(pk=year_id),
#                                                                    consumption__category=Category.objects.get(
#                                                                        pk=category_id),
#                                                                    consumption__address_of_the_municipal_organization__municipalOrganization=organization))),
#                                                    otklonenie=Sum('consumption__otklonenie',
#                                                                   filter=(
#                                                                       Q(consumption__month=Month.objects.get(
#                                                                           pk=month_id),
#                                                                           consumption__god=God.objects.get(pk=year_id),
#                                                                           consumption__category=Category.objects.get(
#                                                                               pk=category_id),
#                                                                           consumption__address_of_the_municipal_organization__municipalOrganization=organization))),
#                                                    otklonenie_percent=Sum('consumption__otklonenie_percent',
#                                                                           filter=(
#                                                                               Q(consumption__month=Month.objects.get(
#                                                                                   pk=month_id),
#                                                                                   consumption__god=God.objects.get(
#                                                                                       pk=year_id),
#                                                                                   consumption__category=Category.objects.get(
#                                                                                       pk=category_id),
#                                                                                   consumption__address_of_the_municipal_organization__municipalOrganization=organization))),
#                                                    sum=Sum('consumption__sum',
#                                                            filter=(Q(consumption__month=Month.objects.get(pk=month_id),
#                                                                      consumption__god=God.objects.get(pk=year_id),
#                                                                      consumption__category=Category.objects.get(
#                                                                          pk=category_id),
#                                                                      consumption__address_of_the_municipal_organization__municipalOrganization=organization)))).order_by(
#                 'address')
#
#             # all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
#             # all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))
#
#             group_data_2 = group_data_1.annotate(
#                 fact=Sum('TheAddressGroup__consumption__fact',
#                          filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
#                                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
#                                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
#                 limit=Sum('TheAddressGroup__consumption__limit',
#                           filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
#                                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
#                                     TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
#                 otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
#                                filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
#                                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
#                                          TheAddressGroup__consumption__category=Category.objects.get(
#                                              pk=category_id)))),
#                 otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
#                                        filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
#                                                  TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
#                                                  TheAddressGroup__consumption__category=Category.objects.get(
#                                                      pk=category_id)))),
#                 sum=Sum('TheAddressGroup__consumption__sum',
#                         filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
#                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
#                                   TheAddressGroup__consumption__category=Category.objects.get(
#                                       pk=category_id))))).order_by(
#                 'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')
#
#             group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
#             group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))
#
#             list_group_data = []
#             for one_address in all_address_2:
#                 if (one_address.group is None):
#                     list_group_data.append(one_address)
#                 elif one_address.group not in list_group_data:
#                     for one_group_data in group_data_2:
#                         list_group_data.append(one_group_data)
#                         table_address_with_group_data = all_address_2.filter(
#                             group=one_group_data)
#                         for k in table_address_with_group_data:
#                             list_group_data.append(k)
#             return render(request, 'website/view_consumption.html',
#                           {'all_address': all_address_2,
#                            'list_group_data': list_group_data, 'category': category,
#                            'year': year, 'month': month, 'form': form, 'sum_data_final': sum_data_final})
#     else:
#         form = OrganizationsForm()
#
#         group_data_1 = AddressGroup.objects.all().distinct()
#         all_address_1 = AddressOfTheMunicipalOrganizations.objects.all()
#
#         all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
#                                                         filter=(Q(consumption__month=Month.objects.get(pk=month_id),
#                                                                   consumption__god=God.objects.get(pk=year_id),
#                                                                   consumption__category=Category.objects.get(
#                                                                       pk=category_id)))),
#                                                limit=Sum('consumption__limit',
#                                                          filter=(Q(consumption__month=Month.objects.get(pk=month_id),
#                                                                    consumption__god=God.objects.get(pk=year_id),
#                                                                    consumption__category=Category.objects.get(
#                                                                        pk=category_id)))),
#                                                otklonenie=Sum('consumption__otklonenie',
#                                                               filter=(
#                                                                   Q(consumption__month=Month.objects.get(pk=month_id),
#                                                                     consumption__god=God.objects.get(pk=year_id),
#                                                                     consumption__category=Category.objects.get(
#                                                                         pk=category_id)))),
#                                                otklonenie_percent=Sum('consumption__otklonenie_percent',
#                                                                       filter=(
#                                                                           Q(consumption__month=Month.objects.get(
#                                                                               pk=month_id),
#                                                                               consumption__god=God.objects.get(
#                                                                                   pk=year_id),
#                                                                               consumption__category=Category.objects.get(
#                                                                                   pk=category_id)))),
#                                                sum=Sum('consumption__sum',
#                                                        filter=(Q(consumption__month=Month.objects.get(pk=month_id),
#                                                                  consumption__god=God.objects.get(pk=year_id),
#                                                                  consumption__category=Category.objects.get(
#                                                                      pk=category_id))))).order_by('address')
#
#         # all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
#         # all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))
#
#         group_data_2 = group_data_1.annotate(
#             fact=Sum('TheAddressGroup__consumption__fact',
#                      filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
#                                TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
#                                TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
#             limit=Sum('TheAddressGroup__consumption__limit',
#                       filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
#                                 TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
#                                 TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
#             otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
#                            filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
#                                      TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
#                                      TheAddressGroup__consumption__category=Category.objects.get(
#                                          pk=category_id)))),
#             otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
#                                    filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
#                                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
#                                              TheAddressGroup__consumption__category=Category.objects.get(
#                                                  pk=category_id)))),
#             sum=Sum('TheAddressGroup__consumption__sum',
#                     filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
#                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
#                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))))).order_by(
#             'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')
#
#         group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
#         group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))
#
#         list_group_data = []
#         for one_address in all_address_2:
#             if (one_address.group is None):
#                 list_group_data.append(one_address)
#             elif one_address.group not in list_group_data:
#                 for one_group_data in group_data_2:
#                     list_group_data.append(one_group_data)
#                     table_address_with_group_data = all_address_2.filter(
#                         group=one_group_data)
#                     for k in table_address_with_group_data:
#                         list_group_data.append(k)
#         return render(request, 'website/view_consumption.html',
#                       {'all_address': all_address_2,
#                        'list_group_data': list_group_data, 'category': category,
#                        'year': year, 'month': month, 'form': form, 'sum_data_final': sum_data_final})


def view_quarter_adress_admin(request, category_id, year_id, quarter_id):
    year = God.objects.get(pk=year_id)
    new_month = Month.objects.filter(quarter_id=quarter_id)
    one_m = new_month[0]
    two_m = new_month[1]
    three_m = new_month[2]
    quarter = Quarter.objects.get(id=quarter_id)
    category = Category.objects.get(pk=category_id)

    # sum_data = Consumption.objects.filter(category=category_id).filter(
    #     god=year_id).filter(Q(month=one_m) | Q(month=two_m) | Q(month=three_m))
    # sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
    #                                     otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))

    if request.method == 'POST':
        form = OrganizationsForm(request.POST)
        if form.is_valid():
            organization = form.cleaned_data['organizations']
            sum_data = Consumption.objects.filter(category=category_id).filter(
                god=year_id).filter(Q(month=one_m) | Q(month=two_m) | Q(month=three_m)).filter(
                address_of_the_municipal_organization__municipalOrganization=organization)
            sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                                otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))

            all_address_1 = AddressOfTheMunicipalOrganizations.objects.filter(
                municipalOrganization=organization)
            group_data_1 = AddressGroup.objects.filter(
                TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization__title=organization).distinct()

            all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
                                                            filter=(Q(consumption__month=Month.objects.get(
                                                                name=one_m),
                                                                consumption__god=God.objects.get(pk=year_id),
                                                                consumption__category=Category.objects.get(
                                                                    pk=category_id))) | Q(
                                                                consumption__month=Month.objects.get(name=two_m),
                                                                consumption__god=God.objects.get(pk=year_id),
                                                                consumption__category=Category.objects.get(
                                                                    pk=category_id)
                                                            ) | Q(consumption__month=Month.objects.get(name=three_m),
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id))),
                                                   limit=Sum('consumption__limit',
                                                             filter=(Q(consumption__month=Month.objects.get(
                                                                 name=one_m),
                                                                 consumption__god=God.objects.get(pk=year_id),
                                                                 consumption__category=Category.objects.get(
                                                                     pk=category_id))) | Q(
                                                                 consumption__month=Month.objects.get(name=two_m),
                                                                 consumption__god=God.objects.get(pk=year_id),
                                                                 consumption__category=Category.objects.get(
                                                                     pk=category_id)
                                                             ) | Q(consumption__month=Month.objects.get(name=three_m),
                                                                   consumption__god=God.objects.get(pk=year_id),
                                                                   consumption__category=Category.objects.get(
                                                                       pk=category_id))),
                                                   otklonenie=Sum('consumption__otklonenie',
                                                                  filter=(Q(consumption__month=Month.objects.get(
                                                                      name=one_m),
                                                                      consumption__god=God.objects.get(pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id))) | Q(
                                                                      consumption__month=Month.objects.get(
                                                                          name=two_m),
                                                                      consumption__god=God.objects.get(pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id)
                                                                  ) | Q(
                                                                      consumption__month=Month.objects.get(
                                                                          name=three_m),
                                                                      consumption__god=God.objects.get(pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id))),
                                                   otklonenie_percent=Sum('consumption__otklonenie_percent',
                                                                          filter=(
                                                                                     Q(consumption__month=Month.objects.get(
                                                                                         name=one_m),
                                                                                         consumption__god=God.objects.get(
                                                                                             pk=year_id),
                                                                                         consumption__category=Category.objects.get(
                                                                                             pk=category_id))) | Q(
                                                                              consumption__month=Month.objects.get(
                                                                                  name=two_m),
                                                                              consumption__god=God.objects.get(
                                                                                  pk=year_id),
                                                                              consumption__category=Category.objects.get(
                                                                                  pk=category_id)
                                                                          ) | Q(consumption__month=Month.objects.get(
                                                                              name=three_m),
                                                                              consumption__god=God.objects.get(
                                                                                  pk=year_id),
                                                                              consumption__category=Category.objects.get(
                                                                                  pk=category_id))),
                                                   sum=Sum('consumption__sum',
                                                           filter=(Q(consumption__month=Month.objects.get(
                                                               name=one_m),
                                                               consumption__god=God.objects.get(
                                                                   pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id))) | Q(
                                                               consumption__month=Month.objects.get(
                                                                   name=two_m),
                                                               consumption__god=God.objects.get(
                                                                   pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id)
                                                           ) | Q(consumption__month=Month.objects.get(
                                                               name=three_m),
                                                               consumption__god=God.objects.get(
                                                                   pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id)))).order_by(
                'consumption__address_of_the_municipal_organization__group')

            all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
            all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

            group_data_2 = group_data_1.annotate(
                fact=Sum('TheAddressGroup__consumption__fact',
                         filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                             TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                             TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                             TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                             TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                             TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                             TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
                limit=Sum('TheAddressGroup__consumption__limit',
                          filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                              TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                              TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
                otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                               filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                         TheAddressGroup__consumption__category=Category.objects.get(
                                             pk=category_id))) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
                otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                                       filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(
                                           name=one_m),
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(
                                               pk=category_id))) | Q(
                                           TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(
                                               pk=category_id)) | Q(
                                           TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(
                                               pk=category_id))),
                sum=Sum('TheAddressGroup__consumption__sum',
                        filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                  TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                  TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                            TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                            TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')
            group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
            group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

            list_group_data = []
            for one_address in all_address_4:
                if (one_address.group is None):
                    list_group_data.append(one_address)
                elif one_address.group not in list_group_data:
                    for one_group_data in group_data_4:
                        list_group_data.append(one_group_data)
                        table_address_with_group_data = all_address_4.filter(
                            group=one_group_data)
                        for k in table_address_with_group_data:
                            list_group_data.append(k)

            return render(request, 'website/view_consumption_quarter.html',
                          {'all_address': all_address_2,
                           'list_group_data': list_group_data, 'category': category,
                           'year': year, 'quarter': quarter, 'form': form, 'sum_data_final': sum_data_final})
    else:
        form = OrganizationsForm()
        sum_data = Consumption.objects.filter(category=category_id).filter(
            god=year_id).filter(Q(month=one_m) | Q(month=two_m) | Q(month=three_m))
        sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                            otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))
        group_data_1 = AddressGroup.objects.all().distinct()
        all_address_1 = AddressOfTheMunicipalOrganizations.objects.all()

        all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
                                                        filter=(Q(consumption__month=Month.objects.get(name=one_m),
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id))) | Q(
                                                            consumption__month=Month.objects.get(name=two_m),
                                                            consumption__god=God.objects.get(pk=year_id),
                                                            consumption__category=Category.objects.get(
                                                                pk=category_id)
                                                        ) | Q(consumption__month=Month.objects.get(name=three_m),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id))),
                                               limit=Sum('consumption__limit',
                                                         filter=(Q(consumption__month=Month.objects.get(name=one_m),
                                                                   consumption__god=God.objects.get(pk=year_id),
                                                                   consumption__category=Category.objects.get(
                                                                       pk=category_id))) | Q(
                                                             consumption__month=Month.objects.get(name=two_m),
                                                             consumption__god=God.objects.get(pk=year_id),
                                                             consumption__category=Category.objects.get(
                                                                 pk=category_id)
                                                         ) | Q(consumption__month=Month.objects.get(name=three_m),
                                                               consumption__god=God.objects.get(pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id))),
                                               otklonenie=Sum('consumption__otklonenie',
                                                              filter=(Q(consumption__month=Month.objects.get(
                                                                  name=one_m),
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id))) | Q(
                                                                  consumption__month=Month.objects.get(name=two_m),
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id)
                                                              ) | Q(
                                                                  consumption__month=Month.objects.get(name=three_m),
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id))),
                                               otklonenie_percent=Sum('consumption__otklonenie_percent',
                                                                      filter=(Q(consumption__month=Month.objects.get(
                                                                          name=one_m),
                                                                          consumption__god=God.objects.get(
                                                                              pk=year_id),
                                                                          consumption__category=Category.objects.get(
                                                                              pk=category_id))) | Q(
                                                                          consumption__month=Month.objects.get(
                                                                              name=two_m),
                                                                          consumption__god=God.objects.get(
                                                                              pk=year_id),
                                                                          consumption__category=Category.objects.get(
                                                                              pk=category_id)
                                                                      ) | Q(consumption__month=Month.objects.get(
                                                                          name=three_m),
                                                                          consumption__god=God.objects.get(
                                                                              pk=year_id),
                                                                          consumption__category=Category.objects.get(
                                                                              pk=category_id))),
                                               sum=Sum('consumption__sum',
                                                       filter=(Q(consumption__month=Month.objects.get(
                                                           name=one_m),
                                                           consumption__god=God.objects.get(
                                                               pk=year_id),
                                                           consumption__category=Category.objects.get(
                                                               pk=category_id))) | Q(
                                                           consumption__month=Month.objects.get(
                                                               name=two_m),
                                                           consumption__god=God.objects.get(
                                                               pk=year_id),
                                                           consumption__category=Category.objects.get(
                                                               pk=category_id)
                                                       ) | Q(consumption__month=Month.objects.get(
                                                           name=three_m),
                                                           consumption__god=God.objects.get(
                                                               pk=year_id),
                                                           consumption__category=Category.objects.get(
                                                               pk=category_id)))).order_by(
                'consumption__address_of_the_municipal_organization__group')

        all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
        all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))
        # for i in all_address_2:
        #     print(i, 'Адрес')

        group_data_2 = group_data_1.annotate(
            fact=Sum('TheAddressGroup__consumption__fact',
                     filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                         TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                         TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                         TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                         TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
            limit=Sum('TheAddressGroup__consumption__limit',
                      filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                          TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                          TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
            otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                           filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                     TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                               TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                               TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
            otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                                   filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                             TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                             TheAddressGroup__consumption__category=Category.objects.get(
                                                 pk=category_id))) | Q(
                                       TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                                       TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                       TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                                       TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                                       TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                       TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
            sum=Sum('TheAddressGroup__consumption__sum',
                    filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                        TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                        TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                        TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                        TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                        TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                        TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')

        group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
        group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))
        # for i in group_data_4:
        #     print(i, 'Main address')

        list_group_data = []
        # for one_address in all_address_4:
        #     if one_address.group is None:
        #         list_group_data.append(one_address)
        #     elif one_address.group not in list_group_data:
        for one_group_data in group_data_4:
            list_group_data.append(one_group_data)
            table_address_with_group_data = all_address_4.filter(
                group=one_group_data)
            for k in table_address_with_group_data:
                list_group_data.append(k)


        return render(request, 'website/view_consumption_quarter.html',
                      {'all_address': all_address_2,
                       'list_group_data': list_group_data, 'category': category,
                       'year': year, 'quarter': quarter, 'form': form, 'sum_data_final': sum_data_final})


def view_polugodie_adress_admin(request, category_id, year_id, polugodie_id):
    year = God.objects.get(pk=year_id)
    new_month = Month.objects.filter(polugodie_id=polugodie_id)
    one_m = new_month[0]
    two_m = new_month[1]
    three_m = new_month[2]
    four_m = new_month[3]
    five_m = new_month[4]
    six_m = new_month[5]
    polugodie = Polugodie.objects.get(id=polugodie_id)
    category = Category.objects.get(pk=category_id)

    # sum_data = Consumption.objects.filter(category=category_id).filter(
    #     god=year_id).filter(
    #     Q(month=one_m) | Q(month=two_m) | Q(month=three_m) | Q(month=four_m) | Q(month=five_m) | Q(month=six_m))
    # sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
    #                                     otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))

    if request.method == 'POST':
        form = OrganizationsForm(request.POST)
        if form.is_valid():
            organization = form.cleaned_data['organizations']
            sum_data = Consumption.objects.filter(category=category_id).filter(
                god=year_id).filter(
                Q(month=one_m) | Q(month=two_m) | Q(month=three_m) | Q(month=four_m) | Q(month=five_m) | Q(
                    month=six_m)).filter(address_of_the_municipal_organization__municipalOrganization=organization)
            sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                                otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))

            all_address_1 = AddressOfTheMunicipalOrganizations.objects.filter(
                municipalOrganization=organization)
            group_data_1 = AddressGroup.objects.filter(
                TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization__title=organization).distinct()

            all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
                                                            filter=(Q(consumption__month=Month.objects.get(
                                                                name=one_m),
                                                                consumption__god=God.objects.get(pk=year_id),
                                                                consumption__category=Category.objects.get(
                                                                    pk=category_id))) |
                                                                   Q(consumption__month=Month.objects.get(name=two_m),
                                                                     consumption__god=God.objects.get(pk=year_id),
                                                                     consumption__category=Category.objects.get(
                                                                         pk=category_id)) |
                                                                   Q(consumption__month=Month.objects.get(name=three_m),
                                                                     consumption__god=God.objects.get(pk=year_id),
                                                                     consumption__category=Category.objects.get(
                                                                         pk=category_id)) |
                                                                   Q(consumption__month=Month.objects.get(
                                                                       name=four_m),
                                                                       consumption__god=God.objects.get(pk=year_id),
                                                                       consumption__category=Category.objects.get(
                                                                           pk=category_id)) |
                                                                   Q(consumption__month=Month.objects.get(
                                                                       name=five_m),
                                                                       consumption__god=God.objects.get(pk=year_id),
                                                                       consumption__category=Category.objects.get(
                                                                           pk=category_id)) |
                                                                   Q(consumption__month=Month.objects.get(
                                                                       name=six_m),
                                                                       consumption__god=God.objects.get(pk=year_id),
                                                                       consumption__category=Category.objects.get(
                                                                           pk=category_id))),
                                                   limit=Sum('consumption__limit',
                                                             filter=(Q(consumption__month=Month.objects.get(
                                                                 name=one_m),
                                                                 consumption__god=God.objects.get(pk=year_id),
                                                                 consumption__category=Category.objects.get(
                                                                     pk=category_id))) |
                                                                    Q(consumption__month=Month.objects.get(
                                                                        name=two_m),
                                                                        consumption__god=God.objects.get(pk=year_id),
                                                                        consumption__category=Category.objects.get(
                                                                            pk=category_id)) |
                                                                    Q(consumption__month=Month.objects.get(
                                                                        name=three_m),
                                                                        consumption__god=God.objects.get(pk=year_id),
                                                                        consumption__category=Category.objects.get(
                                                                            pk=category_id)) |
                                                                    Q(consumption__month=Month.objects.get(
                                                                        name=four_m),
                                                                        consumption__god=God.objects.get(pk=year_id),
                                                                        consumption__category=Category.objects.get(
                                                                            pk=category_id)) |
                                                                    Q(consumption__month=Month.objects.get(
                                                                        name=five_m),
                                                                        consumption__god=God.objects.get(pk=year_id),
                                                                        consumption__category=Category.objects.get(
                                                                            pk=category_id)) |
                                                                    Q(consumption__month=Month.objects.get(
                                                                        name=six_m),
                                                                        consumption__god=God.objects.get(pk=year_id),
                                                                        consumption__category=Category.objects.get(
                                                                            pk=category_id))),
                                                   otklonenie=Sum('consumption__otklonenie',
                                                                  filter=(Q(consumption__month=Month.objects.get(
                                                                      name=one_m),
                                                                      consumption__god=God.objects.get(pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id))) |
                                                                         Q(consumption__month=Month.objects.get(
                                                                             name=two_m),
                                                                             consumption__god=God.objects.get(
                                                                                 pk=year_id),
                                                                             consumption__category=Category.objects.get(
                                                                                 pk=category_id)) |
                                                                         Q(consumption__month=Month.objects.get(
                                                                             name=three_m),
                                                                             consumption__god=God.objects.get(
                                                                                 pk=year_id),
                                                                             consumption__category=Category.objects.get(
                                                                                 pk=category_id)) |
                                                                         Q(consumption__month=Month.objects.get(
                                                                             name=four_m),
                                                                             consumption__god=God.objects.get(
                                                                                 pk=year_id),
                                                                             consumption__category=Category.objects.get(
                                                                                 pk=category_id)) |
                                                                         Q(consumption__month=Month.objects.get(
                                                                             name=five_m),
                                                                             consumption__god=God.objects.get(
                                                                                 pk=year_id),
                                                                             consumption__category=Category.objects.get(
                                                                                 pk=category_id)) |
                                                                         Q(consumption__month=Month.objects.get(
                                                                             name=six_m),
                                                                             consumption__god=God.objects.get(
                                                                                 pk=year_id),
                                                                             consumption__category=Category.objects.get(
                                                                                 pk=category_id))),
                                                   otklonenie_percent=Sum('consumption__otklonenie_percent',
                                                                          filter=(
                                                                                     Q(consumption__month=Month.objects.get(
                                                                                         name=one_m),
                                                                                         consumption__god=God.objects.get(
                                                                                             pk=year_id),
                                                                                         consumption__category=Category.objects.get(
                                                                                             pk=category_id))) |
                                                                                 Q(consumption__month=Month.objects.get(
                                                                                     name=two_m),
                                                                                     consumption__god=God.objects.get(
                                                                                         pk=year_id),
                                                                                     consumption__category=Category.objects.get(
                                                                                         pk=category_id)) |
                                                                                 Q(consumption__month=Month.objects.get(
                                                                                     name=three_m),
                                                                                     consumption__god=God.objects.get(
                                                                                         pk=year_id),
                                                                                     consumption__category=Category.objects.get(
                                                                                         pk=category_id)) |
                                                                                 Q(consumption__month=Month.objects.get(
                                                                                     name=four_m),
                                                                                     consumption__god=God.objects.get(
                                                                                         pk=year_id),
                                                                                     consumption__category=Category.objects.get(
                                                                                         pk=category_id)) |
                                                                                 Q(consumption__month=Month.objects.get(
                                                                                     name=five_m),
                                                                                     consumption__god=God.objects.get(
                                                                                         pk=year_id),
                                                                                     consumption__category=Category.objects.get(
                                                                                         pk=category_id)) |
                                                                                 Q(consumption__month=Month.objects.get(
                                                                                     name=six_m),
                                                                                     consumption__god=God.objects.get(
                                                                                         pk=year_id),
                                                                                     consumption__category=Category.objects.get(
                                                                                         pk=category_id))),
                                                   sum=Sum('consumption__sum',
                                                           filter=(Q(consumption__month=Month.objects.get(
                                                               name=one_m),
                                                               consumption__god=God.objects.get(pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id))) |
                                                                  Q(consumption__month=Month.objects.get(name=two_m),
                                                                    consumption__god=God.objects.get(pk=year_id),
                                                                    consumption__category=Category.objects.get(
                                                                        pk=category_id)) |
                                                                  Q(consumption__month=Month.objects.get(
                                                                      name=three_m),
                                                                      consumption__god=God.objects.get(pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id)) |
                                                                  Q(consumption__month=Month.objects.get(
                                                                      name=four_m),
                                                                      consumption__god=God.objects.get(pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id)) |
                                                                  Q(consumption__month=Month.objects.get(
                                                                      name=five_m),
                                                                      consumption__god=God.objects.get(pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id)) |
                                                                  Q(consumption__month=Month.objects.get(
                                                                      name=six_m),
                                                                      consumption__god=God.objects.get(pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id)))).order_by(
                'consumption__address_of_the_municipal_organization__group')

            all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
            all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

            group_data_2 = group_data_1.annotate(
                fact=Sum('TheAddressGroup__consumption__fact',
                         filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                             TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                             TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                             TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                             TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                             TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                             TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                             TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                             TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                             TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                             TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                             TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                             TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                             TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                             TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                             TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                         ),
                limit=Sum('TheAddressGroup__consumption__limit',
                          filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                              TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                              TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                              TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                              TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                              TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                          ),
                otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                               filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                         TheAddressGroup__consumption__category=Category.objects.get(
                                             pk=category_id))) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                               ),
                otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                                       filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(
                                           name=one_m),
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(
                                               pk=category_id))) | Q(
                                           TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(
                                               pk=category_id)) | Q(
                                           TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(
                                               pk=category_id)) | Q(
                                           TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(
                                               pk=category_id)) | Q(
                                           TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(
                                               pk=category_id)) | Q(
                                           TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                                       ),
                sum=Sum('TheAddressGroup__consumption__sum',
                        filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                  TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                  TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                            TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                            TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                            TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                            TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                            TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')

            group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
            group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

            list_group_data = []
            # for one_address in all_address_4:
            #     if (one_address.group is None):
            #         list_group_data.append(one_address)
            #     elif one_address.group not in list_group_data:
            for one_group_data in group_data_4:
                list_group_data.append(one_group_data)
                table_address_with_group_data = all_address_4.filter(
                    group=one_group_data)
                for k in table_address_with_group_data:
                    list_group_data.append(k)

            return render(request, 'website/new_consumption_polugodie.html',
                          {'all_address': all_address_2,
                           'list_group_data': list_group_data, 'category': category,
                           'year': year, 'form': form, 'sum_data_final': sum_data_final, 'polugodie': polugodie})
    else:
        form = OrganizationsForm()
        sum_data = Consumption.objects.filter(category=category_id).filter(
            god=year_id).filter(
            Q(month=one_m) | Q(month=two_m) | Q(month=three_m) | Q(month=four_m) | Q(month=five_m) | Q(month=six_m))
        sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                            otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))
        group_data_1 = AddressGroup.objects.all().distinct()
        all_address_1 = AddressOfTheMunicipalOrganizations.objects.all()

        all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
                                                        filter=(Q(consumption__month=Month.objects.get(
                                                            name=one_m),
                                                            consumption__god=God.objects.get(pk=year_id),
                                                            consumption__category=Category.objects.get(
                                                                pk=category_id))) |
                                                               Q(consumption__month=Month.objects.get(name=two_m),
                                                                 consumption__god=God.objects.get(pk=year_id),
                                                                 consumption__category=Category.objects.get(
                                                                     pk=category_id)) |
                                                               Q(consumption__month=Month.objects.get(name=three_m),
                                                                 consumption__god=God.objects.get(pk=year_id),
                                                                 consumption__category=Category.objects.get(
                                                                     pk=category_id)) |
                                                               Q(consumption__month=Month.objects.get(
                                                                   name=four_m),
                                                                   consumption__god=God.objects.get(pk=year_id),
                                                                   consumption__category=Category.objects.get(
                                                                       pk=category_id)) |
                                                               Q(consumption__month=Month.objects.get(
                                                                   name=five_m),
                                                                   consumption__god=God.objects.get(pk=year_id),
                                                                   consumption__category=Category.objects.get(
                                                                       pk=category_id)) |
                                                               Q(consumption__month=Month.objects.get(
                                                                   name=six_m),
                                                                   consumption__god=God.objects.get(pk=year_id),
                                                                   consumption__category=Category.objects.get(
                                                                       pk=category_id))),
                                               limit=Sum('consumption__limit',
                                                         filter=(Q(consumption__month=Month.objects.get(
                                                             name=one_m),
                                                             consumption__god=God.objects.get(pk=year_id),
                                                             consumption__category=Category.objects.get(
                                                                 pk=category_id))) |
                                                                Q(consumption__month=Month.objects.get(
                                                                    name=two_m),
                                                                    consumption__god=God.objects.get(pk=year_id),
                                                                    consumption__category=Category.objects.get(
                                                                        pk=category_id)) |
                                                                Q(consumption__month=Month.objects.get(
                                                                    name=three_m),
                                                                    consumption__god=God.objects.get(pk=year_id),
                                                                    consumption__category=Category.objects.get(
                                                                        pk=category_id)) |
                                                                Q(consumption__month=Month.objects.get(
                                                                    name=four_m),
                                                                    consumption__god=God.objects.get(pk=year_id),
                                                                    consumption__category=Category.objects.get(
                                                                        pk=category_id)) |
                                                                Q(consumption__month=Month.objects.get(
                                                                    name=five_m),
                                                                    consumption__god=God.objects.get(pk=year_id),
                                                                    consumption__category=Category.objects.get(
                                                                        pk=category_id)) |
                                                                Q(consumption__month=Month.objects.get(
                                                                    name=six_m),
                                                                    consumption__god=God.objects.get(pk=year_id),
                                                                    consumption__category=Category.objects.get(
                                                                        pk=category_id))),
                                               otklonenie=Sum('consumption__otklonenie',
                                                              filter=(Q(consumption__month=Month.objects.get(
                                                                  name=one_m),
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id))) |
                                                                     Q(consumption__month=Month.objects.get(
                                                                         name=two_m),
                                                                         consumption__god=God.objects.get(
                                                                             pk=year_id),
                                                                         consumption__category=Category.objects.get(
                                                                             pk=category_id)) |
                                                                     Q(consumption__month=Month.objects.get(
                                                                         name=three_m),
                                                                         consumption__god=God.objects.get(
                                                                             pk=year_id),
                                                                         consumption__category=Category.objects.get(
                                                                             pk=category_id)) |
                                                                     Q(consumption__month=Month.objects.get(
                                                                         name=four_m),
                                                                         consumption__god=God.objects.get(
                                                                             pk=year_id),
                                                                         consumption__category=Category.objects.get(
                                                                             pk=category_id)) |
                                                                     Q(consumption__month=Month.objects.get(
                                                                         name=five_m),
                                                                         consumption__god=God.objects.get(
                                                                             pk=year_id),
                                                                         consumption__category=Category.objects.get(
                                                                             pk=category_id)) |
                                                                     Q(consumption__month=Month.objects.get(
                                                                         name=six_m),
                                                                         consumption__god=God.objects.get(
                                                                             pk=year_id),
                                                                         consumption__category=Category.objects.get(
                                                                             pk=category_id))),
                                               otklonenie_percent=Sum('consumption__otklonenie_percent',
                                                                      filter=(
                                                                                 Q(consumption__month=Month.objects.get(
                                                                                     name=one_m),
                                                                                     consumption__god=God.objects.get(
                                                                                         pk=year_id),
                                                                                     consumption__category=Category.objects.get(
                                                                                         pk=category_id))) |
                                                                             Q(consumption__month=Month.objects.get(
                                                                                 name=two_m),
                                                                                 consumption__god=God.objects.get(
                                                                                     pk=year_id),
                                                                                 consumption__category=Category.objects.get(
                                                                                     pk=category_id)) |
                                                                             Q(consumption__month=Month.objects.get(
                                                                                 name=three_m),
                                                                                 consumption__god=God.objects.get(
                                                                                     pk=year_id),
                                                                                 consumption__category=Category.objects.get(
                                                                                     pk=category_id)) |
                                                                             Q(consumption__month=Month.objects.get(
                                                                                 name=four_m),
                                                                                 consumption__god=God.objects.get(
                                                                                     pk=year_id),
                                                                                 consumption__category=Category.objects.get(
                                                                                     pk=category_id)) |
                                                                             Q(consumption__month=Month.objects.get(
                                                                                 name=five_m),
                                                                                 consumption__god=God.objects.get(
                                                                                     pk=year_id),
                                                                                 consumption__category=Category.objects.get(
                                                                                     pk=category_id)) |
                                                                             Q(consumption__month=Month.objects.get(
                                                                                 name=six_m),
                                                                                 consumption__god=God.objects.get(
                                                                                     pk=year_id),
                                                                                 consumption__category=Category.objects.get(
                                                                                     pk=category_id))),
                                               sum=Sum('consumption__sum',
                                                       filter=(Q(consumption__month=Month.objects.get(
                                                           name=one_m),
                                                           consumption__god=God.objects.get(pk=year_id),
                                                           consumption__category=Category.objects.get(
                                                               pk=category_id))) |
                                                              Q(consumption__month=Month.objects.get(name=two_m),
                                                                consumption__god=God.objects.get(pk=year_id),
                                                                consumption__category=Category.objects.get(
                                                                    pk=category_id)) |
                                                              Q(consumption__month=Month.objects.get(
                                                                  name=three_m),
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id)) |
                                                              Q(consumption__month=Month.objects.get(
                                                                  name=four_m),
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id)) |
                                                              Q(consumption__month=Month.objects.get(
                                                                  name=five_m),
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id)) |
                                                              Q(consumption__month=Month.objects.get(
                                                                  name=six_m),
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id)))).order_by(
                'consumption__address_of_the_municipal_organization__group')

        all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
        all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

        group_data_2 = group_data_1.annotate(
            fact=Sum('TheAddressGroup__consumption__fact',
                     filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                         TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                         TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                         TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                         TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                         TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                         TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                         TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                         TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                         TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                         TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                     ),
            limit=Sum('TheAddressGroup__consumption__limit',
                      filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                          TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                          TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                          TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                          TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                          TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                      ),
            otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                           filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                     TheAddressGroup__consumption__category=Category.objects.get(
                                         pk=category_id))) | Q(
                               TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                               TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                               TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                               TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                               TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                           ),
            otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                                   filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(
                                       name=one_m),
                                       TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                       TheAddressGroup__consumption__category=Category.objects.get(
                                           pk=category_id))) | Q(
                                       TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                                       TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                       TheAddressGroup__consumption__category=Category.objects.get(
                                           pk=category_id)) | Q(
                                       TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                                       TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                       TheAddressGroup__consumption__category=Category.objects.get(
                                           pk=category_id)) | Q(
                                       TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                                       TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                       TheAddressGroup__consumption__category=Category.objects.get(
                                           pk=category_id)) | Q(
                                       TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                                       TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                       TheAddressGroup__consumption__category=Category.objects.get(
                                           pk=category_id)) | Q(
                                       TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                                       TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                       TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                                   ),
            sum=Sum('TheAddressGroup__consumption__sum',
                    filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                        TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                        TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                        TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                        TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                        TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                        TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                        TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                        TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                        TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                        TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                        TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                        TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                        TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                        TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                        TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')

        group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
        group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

        list_group_data = []
        # for one_address in all_address_4:
        #     if (one_address.group is None):
        #         list_group_data.append(one_address)
        #     elif one_address.group not in list_group_data:
        for one_group_data in group_data_4:
            list_group_data.append(one_group_data)
            table_address_with_group_data = all_address_4.filter(
                group=one_group_data)
            for k in table_address_with_group_data:
                list_group_data.append(k)

        return render(request, 'website/new_consumption_polugodie.html',
                      {'all_address': all_address_2,
                       'list_group_data': list_group_data, 'category': category,
                       'year': year, 'form': form, 'sum_data_final': sum_data_final, 'polugodie': polugodie})


def view_god_adress_admin(request, category_id, year_id):
    year = God.objects.get(pk=year_id)
    category = Category.objects.get(pk=category_id)

    # sum_data = Consumption.objects.filter(category=category_id).filter(
    #     god=year_id)
    # sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
    #                                     otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))

    if request.method == 'POST':
        form = OrganizationsForm(request.POST)
        if form.is_valid():
            organization = form.cleaned_data['organizations']
            sum_data = Consumption.objects.filter(category=category_id).filter(
                god=year_id).filter(address_of_the_municipal_organization__municipalOrganization=organization)
            sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                                otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))

            all_address_1 = AddressOfTheMunicipalOrganizations.objects.filter(
                municipalOrganization=organization)
            group_data_1 = AddressGroup.objects.filter(
                TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization__title=organization).distinct()

            all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
                                                            filter=(Q(
                                                                consumption__god=God.objects.get(pk=year_id),
                                                                consumption__category=Category.objects.get(
                                                                    pk=category_id)))),
                                                   limit=Sum('consumption__limit',
                                                             filter=(Q(
                                                                 consumption__god=God.objects.get(pk=year_id),
                                                                 consumption__category=Category.objects.get(
                                                                     pk=category_id)))),
                                                   otklonenie=Sum('consumption__otklonenie',
                                                                  filter=(Q(
                                                                      consumption__god=God.objects.get(
                                                                          pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id)))),
                                                   otklonenie_percent=Sum('consumption__otklonenie_percent',
                                                                          filter=(
                                                                              Q(
                                                                                  consumption__god=God.objects.get(
                                                                                      pk=year_id),
                                                                                  consumption__category=Category.objects.get(
                                                                                      pk=category_id)))),
                                                   sum=Sum('consumption__sum',
                                                           filter=(Q(
                                                               consumption__god=God.objects.get(pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id))))).order_by(
                'consumption__address_of_the_municipal_organization__group')

            all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
            all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))
            # for i in all_address_4:
            #     print(i, i.fact)

            group_data_2 = group_data_1.annotate(
                fact=Sum('TheAddressGroup__consumption__fact',
                         filter=(Q(
                             TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                             TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
                limit=Sum('TheAddressGroup__consumption__limit',
                          filter=(Q(
                              TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                              TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
                otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                               filter=(Q(
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(
                                       pk=category_id)))),
                otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                                       filter=(Q(
                                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                           TheAddressGroup__consumption__category=Category.objects.get(
                                               pk=category_id)))),
                sum=Sum('TheAddressGroup__consumption__sum',
                        filter=(Q(
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(
                                pk=category_id))))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')

            group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
            group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

            list_group_data = []
            for one_address in all_address_4:
                if (one_address.group is None):
                    list_group_data.append(one_address)
                elif one_address.group not in list_group_data:
                    for one_group_data in group_data_4:
                        list_group_data.append(one_group_data)
                        table_address_with_group_data = all_address_4.filter(
                            group=one_group_data)
                        for k in table_address_with_group_data:
                            list_group_data.append(k)

            return render(request, 'website/new_consumption_god.html',
                          {'all_address': all_address_2,
                           'list_group_data': list_group_data, 'category': category,
                           'year': year, 'form': form, 'sum_data_final': sum_data_final})
    else:
        form = OrganizationsForm()
        group_data_1 = AddressGroup.objects.all().distinct()
        all_address_1 = AddressOfTheMunicipalOrganizations.objects.all()
        sum_data = Consumption.objects.filter(category=category_id).filter(
            god=year_id)
        sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                            otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))

        all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
                                                        filter=(Q(
                                                            consumption__god=God.objects.get(pk=year_id),
                                                            consumption__category=Category.objects.get(
                                                                pk=category_id)))),
                                               limit=Sum('consumption__limit',
                                                         filter=(Q(
                                                             consumption__god=God.objects.get(pk=year_id),
                                                             consumption__category=Category.objects.get(
                                                                 pk=category_id)))),
                                               otklonenie=Sum('consumption__otklonenie',
                                                              filter=(Q(
                                                                  consumption__god=God.objects.get(pk=year_id),
                                                                  consumption__category=Category.objects.get(
                                                                      pk=category_id)))),
                                               otklonenie_percent=Sum('consumption__otklonenie_percent',
                                                                      filter=(
                                                                          Q(
                                                                              consumption__god=God.objects.get(
                                                                                  pk=year_id),
                                                                              consumption__category=Category.objects.get(
                                                                                  pk=category_id)))),
                                               sum=Sum('consumption__sum',
                                                       filter=(Q(
                                                           consumption__god=God.objects.get(pk=year_id),
                                                           consumption__category=Category.objects.get(
                                                               pk=category_id))))).order_by(
                'consumption__address_of_the_municipal_organization__group')

        all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
        all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

        group_data_2 = group_data_1.annotate(
            fact=Sum('TheAddressGroup__consumption__fact',
                     filter=(Q(
                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                         TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
            limit=Sum('TheAddressGroup__consumption__limit',
                      filter=(Q(
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
            otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                           filter=(Q(
                               TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                               TheAddressGroup__consumption__category=Category.objects.get(
                                   pk=category_id)))),
            otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                                   filter=(Q(
                                       TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                       TheAddressGroup__consumption__category=Category.objects.get(
                                           pk=category_id)))),
            sum=Sum('TheAddressGroup__consumption__sum',
                    filter=(Q(
                        TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                        TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')

        group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
        group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

        list_group_data = []
        for one_address in all_address_4:
            if (one_address.group is None):
                list_group_data.append(one_address)
            elif one_address.group not in list_group_data:
                for one_group_data in group_data_4:
                    list_group_data.append(one_group_data)
                    table_address_with_group_data = all_address_4.filter(
                        group=one_group_data)
                    for k in table_address_with_group_data:
                        list_group_data.append(k)

        return render(request, 'website/new_consumption_god.html',
                      {'all_address': all_address_2,
                       'list_group_data': list_group_data, 'category': category,
                       'year': year, 'form': form, 'sum_data_final': sum_data_final})


def write_quarter(year_id, category_id, quarter_id, worksheet, colonna, num_color, num_color_bold, num_color_cut2,
                  num_color_cut3, num_color_bold_cut2, num_color_bold_cut3):
    year = God.objects.get(pk=year_id)
    new_month = Month.objects.filter(quarter_id=quarter_id)
    one_m = new_month[0]
    two_m = new_month[1]
    three_m = new_month[2]
    quarter = Quarter.objects.get(id=quarter_id)
    category = Category.objects.get(pk=category_id)

    sum_data = Consumption.objects.filter(category=category_id).filter(
        god=year_id).filter(Q(month=one_m) | Q(month=two_m) | Q(month=three_m))
    sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                        otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))

    group_data_1 = AddressGroup.objects.all().distinct()
    all_address_1 = AddressOfTheMunicipalOrganizations.objects.all()

    all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
                                                    filter=(Q(consumption__month=Month.objects.get(name=one_m),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id))) | Q(
                                                        consumption__month=Month.objects.get(name=two_m),
                                                        consumption__god=God.objects.get(pk=year_id),
                                                        consumption__category=Category.objects.get(
                                                            pk=category_id)
                                                    ) | Q(consumption__month=Month.objects.get(name=three_m),
                                                          consumption__god=God.objects.get(pk=year_id),
                                                          consumption__category=Category.objects.get(
                                                              pk=category_id))),
                                           limit=Sum('consumption__limit',
                                                     filter=(Q(consumption__month=Month.objects.get(name=one_m),
                                                               consumption__god=God.objects.get(pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id))) | Q(
                                                         consumption__month=Month.objects.get(name=two_m),
                                                         consumption__god=God.objects.get(pk=year_id),
                                                         consumption__category=Category.objects.get(
                                                             pk=category_id)
                                                     ) | Q(consumption__month=Month.objects.get(name=three_m),
                                                           consumption__god=God.objects.get(pk=year_id),
                                                           consumption__category=Category.objects.get(
                                                               pk=category_id))),
                                           otklonenie=Sum('consumption__otklonenie',
                                                          filter=(Q(consumption__month=Month.objects.get(
                                                              name=one_m),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id))) | Q(
                                                              consumption__month=Month.objects.get(name=two_m),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id)
                                                          ) | Q(
                                                              consumption__month=Month.objects.get(name=three_m),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id))),
                                           otklonenie_percent=Sum('consumption__otklonenie_percent',
                                                                  filter=(Q(consumption__month=Month.objects.get(
                                                                      name=one_m),
                                                                      consumption__god=God.objects.get(
                                                                          pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id))) | Q(
                                                                      consumption__month=Month.objects.get(
                                                                          name=two_m),
                                                                      consumption__god=God.objects.get(
                                                                          pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id)
                                                                  ) | Q(consumption__month=Month.objects.get(
                                                                      name=three_m),
                                                                      consumption__god=God.objects.get(
                                                                          pk=year_id),
                                                                      consumption__category=Category.objects.get(
                                                                          pk=category_id))),
                                           sum=Sum('consumption__sum',
                                                   filter=(Q(consumption__month=Month.objects.get(
                                                       name=one_m),
                                                       consumption__god=God.objects.get(
                                                           pk=year_id),
                                                       consumption__category=Category.objects.get(
                                                           pk=category_id))) | Q(
                                                       consumption__month=Month.objects.get(
                                                           name=two_m),
                                                       consumption__god=God.objects.get(
                                                           pk=year_id),
                                                       consumption__category=Category.objects.get(
                                                           pk=category_id)
                                                   ) | Q(consumption__month=Month.objects.get(
                                                       name=three_m),
                                                       consumption__god=God.objects.get(
                                                           pk=year_id),
                                                       consumption__category=Category.objects.get(
                                                           pk=category_id)))).order_by(
        'consumption__address_of_the_municipal_organization__group')


    all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
    all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

    group_data_2 = group_data_1.annotate(
        fact=Sum('TheAddressGroup__consumption__fact',
                 filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                     TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                     TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                     TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                     TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
        limit=Sum('TheAddressGroup__consumption__limit',
                  filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                      TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                      TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                      TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                      TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                      TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                      TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
        otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                       filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                 TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                 TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                           TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                           TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
        otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                               filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                         TheAddressGroup__consumption__category=Category.objects.get(
                                             pk=category_id))) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))),
        sum=Sum('TheAddressGroup__consumption__sum',
                filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                    TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                    TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')

    group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
    group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

    list_group_data = []
    row = 3
    col = colonna
    # for one_address in all_address_4:
    #     if (one_address.group is None):
    #         list_group_data.append(one_address)
    #         worksheet.write(row, col, one_address.fact, num_color)
    #         worksheet.write(row, col + 1, one_address.limit, num_color)
    #         worksheet.write(row, col + 2, one_address.otklonenie_new, num_color_cut2)
    #         worksheet.write(row, col + 3, one_address.otklonenie_percent_new, num_color_cut2)
    #         worksheet.write(row, col + 4, one_address.sum, num_color_cut3)
    #         row = row + 1
    #     elif one_address.group not in list_group_data:
    for one_group_data in group_data_4:
        list_group_data.append(one_group_data)
        worksheet.write(row, col, one_group_data.fact, num_color_bold)
        worksheet.write(row, col + 1, one_group_data.limit, num_color_bold)
        worksheet.write(row, col + 2, one_group_data.otklonenie_new, num_color_bold_cut2)
        worksheet.write(row, col + 3, one_group_data.otklonenie_percent_new, num_color_bold_cut2)
        worksheet.write(row, col + 4, one_group_data.sum, num_color_bold_cut3)
        row = row + 1
        table_address_with_group_data = all_address_4.filter(
            group=one_group_data)
        for k in table_address_with_group_data:
            list_group_data.append(k)
            worksheet.write(row, col, k.fact, num_color)
            worksheet.write(row, col + 1, k.limit, num_color)
            worksheet.write(row, col + 2, k.otklonenie_new, num_color_cut2)
            worksheet.write(row, col + 3, k.otklonenie_percent_new, num_color_cut2)
            worksheet.write(row, col + 4, k.sum, num_color_cut3)
            row = row + 1
    worksheet.write(row, col, sum_data_final['fact'], num_color)
    worksheet.write(row, col + 1, sum_data_final['limit'], num_color)
    worksheet.write(row, col + 2, sum_data_final['otklonenie'], num_color)
    worksheet.write(row, col + 3, '-', num_color)
    worksheet.write(row, col + 4, sum_data_final['sum'], num_color)


def write_polugodie(year_id, polugodie_id, category_id, worksheet, colonnna, num_color, num_color_bold, num_color_cut2,
                    num_color_cut3, num_color_bold_cut2, num_color_bold_cut3):
    year = God.objects.get(pk=year_id)
    new_month = Month.objects.filter(polugodie_id=polugodie_id)
    one_m = new_month[0]
    two_m = new_month[1]
    three_m = new_month[2]
    four_m = new_month[3]
    five_m = new_month[4]
    six_m = new_month[5]
    polugodie = Polugodie.objects.get(id=polugodie_id)
    category = Category.objects.get(pk=category_id)

    sum_data = Consumption.objects.filter(category=category_id).filter(
        god=year_id).filter(
        Q(month=one_m) | Q(month=two_m) | Q(month=three_m) | Q(month=four_m) | Q(month=five_m) | Q(month=six_m))
    sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                        otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))

    group_data_1 = AddressGroup.objects.all().distinct()
    all_address_1 = AddressOfTheMunicipalOrganizations.objects.all()

    all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
                                                    filter=(Q(consumption__month=Month.objects.get(
                                                        name=one_m),
                                                        consumption__god=God.objects.get(pk=year_id),
                                                        consumption__category=Category.objects.get(
                                                            pk=category_id))) |
                                                           Q(consumption__month=Month.objects.get(name=two_m),
                                                             consumption__god=God.objects.get(pk=year_id),
                                                             consumption__category=Category.objects.get(
                                                                 pk=category_id)) |
                                                           Q(consumption__month=Month.objects.get(name=three_m),
                                                             consumption__god=God.objects.get(pk=year_id),
                                                             consumption__category=Category.objects.get(
                                                                 pk=category_id)) |
                                                           Q(consumption__month=Month.objects.get(
                                                               name=four_m),
                                                               consumption__god=God.objects.get(pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id)) |
                                                           Q(consumption__month=Month.objects.get(
                                                               name=five_m),
                                                               consumption__god=God.objects.get(pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id)) |
                                                           Q(consumption__month=Month.objects.get(
                                                               name=six_m),
                                                               consumption__god=God.objects.get(pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id))),
                                           limit=Sum('consumption__limit',
                                                     filter=(Q(consumption__month=Month.objects.get(
                                                         name=one_m),
                                                         consumption__god=God.objects.get(pk=year_id),
                                                         consumption__category=Category.objects.get(
                                                             pk=category_id))) |
                                                            Q(consumption__month=Month.objects.get(
                                                                name=two_m),
                                                                consumption__god=God.objects.get(pk=year_id),
                                                                consumption__category=Category.objects.get(
                                                                    pk=category_id)) |
                                                            Q(consumption__month=Month.objects.get(
                                                                name=three_m),
                                                                consumption__god=God.objects.get(pk=year_id),
                                                                consumption__category=Category.objects.get(
                                                                    pk=category_id)) |
                                                            Q(consumption__month=Month.objects.get(
                                                                name=four_m),
                                                                consumption__god=God.objects.get(pk=year_id),
                                                                consumption__category=Category.objects.get(
                                                                    pk=category_id)) |
                                                            Q(consumption__month=Month.objects.get(
                                                                name=five_m),
                                                                consumption__god=God.objects.get(pk=year_id),
                                                                consumption__category=Category.objects.get(
                                                                    pk=category_id)) |
                                                            Q(consumption__month=Month.objects.get(
                                                                name=six_m),
                                                                consumption__god=God.objects.get(pk=year_id),
                                                                consumption__category=Category.objects.get(
                                                                    pk=category_id))),
                                           otklonenie=Sum('consumption__otklonenie',
                                                          filter=(Q(consumption__month=Month.objects.get(
                                                              name=one_m),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id))) |
                                                                 Q(consumption__month=Month.objects.get(
                                                                     name=two_m),
                                                                     consumption__god=God.objects.get(
                                                                         pk=year_id),
                                                                     consumption__category=Category.objects.get(
                                                                         pk=category_id)) |
                                                                 Q(consumption__month=Month.objects.get(
                                                                     name=three_m),
                                                                     consumption__god=God.objects.get(
                                                                         pk=year_id),
                                                                     consumption__category=Category.objects.get(
                                                                         pk=category_id)) |
                                                                 Q(consumption__month=Month.objects.get(
                                                                     name=four_m),
                                                                     consumption__god=God.objects.get(
                                                                         pk=year_id),
                                                                     consumption__category=Category.objects.get(
                                                                         pk=category_id)) |
                                                                 Q(consumption__month=Month.objects.get(
                                                                     name=five_m),
                                                                     consumption__god=God.objects.get(
                                                                         pk=year_id),
                                                                     consumption__category=Category.objects.get(
                                                                         pk=category_id)) |
                                                                 Q(consumption__month=Month.objects.get(
                                                                     name=six_m),
                                                                     consumption__god=God.objects.get(
                                                                         pk=year_id),
                                                                     consumption__category=Category.objects.get(
                                                                         pk=category_id))),
                                           otklonenie_percent=Sum('consumption__otklonenie_percent',
                                                                  filter=(
                                                                             Q(consumption__month=Month.objects.get(
                                                                                 name=one_m),
                                                                                 consumption__god=God.objects.get(
                                                                                     pk=year_id),
                                                                                 consumption__category=Category.objects.get(
                                                                                     pk=category_id))) |
                                                                         Q(consumption__month=Month.objects.get(
                                                                             name=two_m),
                                                                             consumption__god=God.objects.get(
                                                                                 pk=year_id),
                                                                             consumption__category=Category.objects.get(
                                                                                 pk=category_id)) |
                                                                         Q(consumption__month=Month.objects.get(
                                                                             name=three_m),
                                                                             consumption__god=God.objects.get(
                                                                                 pk=year_id),
                                                                             consumption__category=Category.objects.get(
                                                                                 pk=category_id)) |
                                                                         Q(consumption__month=Month.objects.get(
                                                                             name=four_m),
                                                                             consumption__god=God.objects.get(
                                                                                 pk=year_id),
                                                                             consumption__category=Category.objects.get(
                                                                                 pk=category_id)) |
                                                                         Q(consumption__month=Month.objects.get(
                                                                             name=five_m),
                                                                             consumption__god=God.objects.get(
                                                                                 pk=year_id),
                                                                             consumption__category=Category.objects.get(
                                                                                 pk=category_id)) |
                                                                         Q(consumption__month=Month.objects.get(
                                                                             name=six_m),
                                                                             consumption__god=God.objects.get(
                                                                                 pk=year_id),
                                                                             consumption__category=Category.objects.get(
                                                                                 pk=category_id))),
                                           sum=Sum('consumption__sum',
                                                   filter=(Q(consumption__month=Month.objects.get(
                                                       name=one_m),
                                                       consumption__god=God.objects.get(pk=year_id),
                                                       consumption__category=Category.objects.get(
                                                           pk=category_id))) |
                                                          Q(consumption__month=Month.objects.get(name=two_m),
                                                            consumption__god=God.objects.get(pk=year_id),
                                                            consumption__category=Category.objects.get(
                                                                pk=category_id)) |
                                                          Q(consumption__month=Month.objects.get(
                                                              name=three_m),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id)) |
                                                          Q(consumption__month=Month.objects.get(
                                                              name=four_m),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id)) |
                                                          Q(consumption__month=Month.objects.get(
                                                              name=five_m),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id)) |
                                                          Q(consumption__month=Month.objects.get(
                                                              name=six_m),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id)))).order_by(
        'consumption__address_of_the_municipal_organization__group')

    all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
    all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

    group_data_2 = group_data_1.annotate(
        fact=Sum('TheAddressGroup__consumption__fact',
                 filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                     TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                     TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                     TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                     TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                     TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                     TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                     TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                     TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                     TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                     TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                 ),
        limit=Sum('TheAddressGroup__consumption__limit',
                  filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                      TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                      TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                      TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                      TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                      TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                      TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                      TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                      TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                      TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                      TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                      TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                      TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                      TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                      TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                      TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                  ),
        otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                       filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                                 TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                 TheAddressGroup__consumption__category=Category.objects.get(
                                     pk=category_id))) | Q(
                           TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                           TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                           TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                           TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                           TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                       ),
        otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                               filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(
                                   name=one_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(
                                       pk=category_id))) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(
                                       pk=category_id)) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(
                                       pk=category_id)) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(
                                       pk=category_id)) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(
                                       pk=category_id)) | Q(
                                   TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))
                               ),
        sum=Sum('TheAddressGroup__consumption__sum',
                filter=(Q(TheAddressGroup__consumption__month__name=Month.objects.get(name=one_m),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))) | Q(
                    TheAddressGroup__consumption__month__name=Month.objects.get(name=two_m),
                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                    TheAddressGroup__consumption__month__name=Month.objects.get(name=three_m),
                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                    TheAddressGroup__consumption__month__name=Month.objects.get(name=four_m),
                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                    TheAddressGroup__consumption__month__name=Month.objects.get(name=five_m),
                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)) | Q(
                    TheAddressGroup__consumption__month__name=Month.objects.get(name=six_m),
                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')

    group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
    group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

    list_group_data = []
    row = 3
    col = colonnna
    # for one_address in all_address_4:
    #     if (one_address.group is None):
    #         list_group_data.append(one_address)
    #         worksheet.write(row, col, one_address.fact, num_color)
    #         worksheet.write(row, col + 1, one_address.limit, num_color)
    #         worksheet.write(row, col + 2, one_address.otklonenie_new, num_color_cut2)
    #         worksheet.write(row, col + 3, one_address.otklonenie_percent_new, num_color_cut2)
    #         worksheet.write(row, col + 4, one_address.sum, num_color_cut3)
    #         row = row + 1
    #     elif one_address.group not in list_group_data:
    for one_group_data in group_data_4:
        list_group_data.append(one_group_data)
        worksheet.write(row, col, one_group_data.fact, num_color_bold)
        worksheet.write(row, col + 1, one_group_data.limit, num_color_bold)
        worksheet.write(row, col + 2, one_group_data.otklonenie_new, num_color_bold_cut2)
        worksheet.write(row, col + 3, one_group_data.otklonenie_percent_new, num_color_bold_cut2)
        worksheet.write(row, col + 4, one_group_data.sum, num_color_bold_cut3)
        row = row + 1
        table_address_with_group_data = all_address_4.filter(
            group=one_group_data)
        for k in table_address_with_group_data:
            list_group_data.append(k)
            worksheet.write(row, col, k.fact, num_color)
            worksheet.write(row, col + 1, k.limit, num_color)
            worksheet.write(row, col + 2, k.otklonenie_new, num_color_cut2)
            worksheet.write(row, col + 3, k.otklonenie_percent_new, num_color_cut2)
            worksheet.write(row, col + 4, k.sum, num_color_cut3)
            row = row + 1
    worksheet.write(row, col, sum_data_final['fact'], num_color)
    worksheet.write(row, col + 1, sum_data_final['limit'], num_color)
    worksheet.write(row, col + 2, sum_data_final['otklonenie'], num_color)
    worksheet.write(row, col + 3, '-', num_color)
    worksheet.write(row, col + 4, sum_data_final['sum'], num_color)


def write_month(year_id, month_id, category_id, worksheet, colonna, num_color, num_color_bold, num_color_cut2,
                num_color_cut3, num_color_bold_cut2, num_color_bold_cut3):
    sum_data = Consumption.objects.filter(category=category_id).filter(
        god=year_id).filter(month=month_id)
    sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                        otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))
    # print(sum_data_final['fact'], sum_data_final['limit'])

    group_data_1 = AddressGroup.objects.all().distinct()
    all_address_1 = AddressOfTheMunicipalOrganizations.objects.all()

    all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
                                                    filter=(Q(consumption__month=Month.objects.get(pk=month_id),
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id)))),
                                           limit=Sum('consumption__limit',
                                                     filter=(Q(consumption__month=Month.objects.get(pk=month_id),
                                                               consumption__god=God.objects.get(pk=year_id),
                                                               consumption__category=Category.objects.get(
                                                                   pk=category_id)))),
                                           otklonenie=Sum('consumption__otklonenie',
                                                          filter=(Q(consumption__month=Month.objects.get(pk=month_id),
                                                                    consumption__god=God.objects.get(pk=year_id),
                                                                    consumption__category=Category.objects.get(
                                                                        pk=category_id)))),
                                           otklonenie_percent=Sum('consumption__otklonenie_percent',
                                                                  filter=(
                                                                      Q(consumption__month=Month.objects.get(
                                                                          pk=month_id),
                                                                        consumption__god=God.objects.get(
                                                                            pk=year_id),
                                                                        consumption__category=Category.objects.get(
                                                                            pk=category_id)))),
                                           sum=Sum('consumption__sum',
                                                   filter=(Q(consumption__month=Month.objects.get(pk=month_id),
                                                             consumption__god=God.objects.get(pk=year_id),
                                                             consumption__category=Category.objects.get(
                                                                 pk=category_id))))).order_by(
        'consumption__address_of_the_municipal_organization__group')

    all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
    all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

    group_data_2 = group_data_1.annotate(
        fact=Sum('TheAddressGroup__consumption__fact',
                 filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
        limit=Sum('TheAddressGroup__consumption__limit',
                  filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
                            TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                            TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
        otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                       filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
                                 TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                 TheAddressGroup__consumption__category=Category.objects.get(
                                     pk=category_id)))),
        otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                               filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
                                         TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                         TheAddressGroup__consumption__category=Category.objects.get(
                                             pk=category_id)))),
        sum=Sum('TheAddressGroup__consumption__sum',
                filter=(Q(TheAddressGroup__consumption__month=Month.objects.get(pk=month_id),
                          TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                          TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')

    group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
    group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

    list_group_data = []
    row = 3
    col = colonna
    # worksheet.write(35, 2, sum_data_final['fact'], num_color)
    # for one_address in all_address_4:
    #     if (one_address.group is None):
    #         list_group_data.append(one_address)
    #         worksheet.write(row, col, one_address.fact, num_color)
    #         worksheet.write(row, col + 1, one_address.limit, num_color)
    #         worksheet.write(row, col + 2, one_address.otklonenie, num_color_cut2)
    #         worksheet.write(row, col + 3, one_address.otklonenie_percent, num_color_cut2)
    #         worksheet.write(row, col + 4, one_address.sum, num_color_cut3)
    #         row = row + 1
    #     elif one_address.group not in list_group_data:
    for one_group_data in group_data_4:
        list_group_data.append(one_group_data)
        worksheet.write(row, col, one_group_data.fact, num_color_bold)
        worksheet.write(row, col + 1, one_group_data.limit, num_color_bold)
        worksheet.write(row, col + 2, one_group_data.otklonenie, num_color_bold_cut2)
        worksheet.write(row, col + 3, one_group_data.otklonenie_percent, num_color_bold_cut2)
        worksheet.write(row, col + 4, one_group_data.sum, num_color_bold_cut3)
        row = row + 1
        table_address_with_group_data = all_address_4.filter(
            group=one_group_data)
        for k in table_address_with_group_data:
            list_group_data.append(k)
            worksheet.write(row, col, k.fact, num_color)
            worksheet.write(row, col + 1, k.limit, num_color)
            worksheet.write(row, col + 2, k.otklonenie, num_color_cut2)
            worksheet.write(row, col + 3, k.otklonenie_percent, num_color_cut2)
            worksheet.write(row, col + 4, k.sum, num_color_cut3)
            row = row + 1
    worksheet.write(row, col, sum_data_final['fact'], num_color)
    worksheet.write(row, col + 1, sum_data_final['limit'], num_color)
    worksheet.write(row, col + 2, sum_data_final['otklonenie'], num_color)
    worksheet.write(row, col + 3, '-', num_color)
    worksheet.write(row, col + 4, sum_data_final['sum'], num_color)


def write_year(year_id, category_id, worksheet, colonnna, f_address, f_address_bold, num_color, num_color_bold,
               num_color_cut2,
               num_color_cut3, num_color_bold_cut2, num_color_bold_cut3, f_address_italic_underline):
    sum_data = Consumption.objects.filter(category=category_id).filter(
        god=year_id)
    # sum_data = Consumption.objects.filter(category=category_id).filter(
    #     god=year_id).filter(
    #     address_of_the_municipal_organization__municipalOrganization__title='УОиДО')
    sum_data_final = sum_data.aggregate(fact=Sum('fact'), limit=Sum('limit'), otklonenie=Sum('otklonenie'),
                                        otklonenie_percent=Sum('otklonenie_percent'), sum=Sum('sum'))




    print(sum_data_final['fact'], sum_data_final['limit'])
    group_data_1 = AddressGroup.objects.all().distinct()
    all_address_1 = AddressOfTheMunicipalOrganizations.objects.all()

    all_address_2 = all_address_1.annotate(fact=Sum('consumption__fact',
                                                    filter=(Q(
                                                        consumption__god=God.objects.get(pk=year_id),
                                                        consumption__category=Category.objects.get(
                                                            pk=category_id)))),
                                           limit=Sum('consumption__limit',
                                                     filter=(Q(
                                                         consumption__god=God.objects.get(pk=year_id),
                                                         consumption__category=Category.objects.get(
                                                             pk=category_id)))),
                                           otklonenie=Sum('consumption__otklonenie',
                                                          filter=(Q(
                                                              consumption__god=God.objects.get(pk=year_id),
                                                              consumption__category=Category.objects.get(
                                                                  pk=category_id)))),
                                           otklonenie_percent=Sum('consumption__otklonenie_percent',
                                                                  filter=(
                                                                      Q(
                                                                          consumption__god=God.objects.get(
                                                                              pk=year_id),
                                                                          consumption__category=Category.objects.get(
                                                                              pk=category_id)))),
                                           sum=Sum('consumption__sum',
                                                   filter=(Q(
                                                       consumption__god=God.objects.get(pk=year_id),
                                                       consumption__category=Category.objects.get(
                                                           pk=category_id))))).order_by(
        'consumption__address_of_the_municipal_organization__group')
    # for i in all_address_2:
    #     print(i, 'Адрес')

    all_address_3 = all_address_2.annotate(otklonenie_new=F('limit') - F('fact'))
    all_address_4 = all_address_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

    group_data_2 = group_data_1.annotate(
        fact=Sum('TheAddressGroup__consumption__fact',
                 filter=(Q(
                     TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                     TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
        limit=Sum('TheAddressGroup__consumption__limit',
                  filter=(Q(
                      TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                      TheAddressGroup__consumption__category=Category.objects.get(pk=category_id)))),
        otklonenie=Sum('TheAddressGroup__consumption__otklonenie',
                       filter=(Q(
                           TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                           TheAddressGroup__consumption__category=Category.objects.get(
                               pk=category_id)))),
        otklonenie_percent=Sum('TheAddressGroup__consumption__otklonenie_percent',
                               filter=(Q(
                                   TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                                   TheAddressGroup__consumption__category=Category.objects.get(
                                       pk=category_id)))),
        sum=Sum('TheAddressGroup__consumption__sum',
                filter=(Q(
                    TheAddressGroup__consumption__god=God.objects.get(pk=year_id),
                    TheAddressGroup__consumption__category=Category.objects.get(pk=category_id))))).order_by(
        'TheAddressGroup__consumption__address_of_the_municipal_organization__municipalOrganization')
    # for j in group_data_2:
    #     print('year')
    #     print(j)

    group_data_3 = group_data_2.annotate(otklonenie_new=F('limit') - F('fact'))
    group_data_4 = group_data_3.annotate(otklonenie_percent_new=F('otklonenie_new') / F('limit'))

    list_group_data = []
    row = 3
    row_address = 3
    col = colonnna
    # for one_address in all_address_4:
    #     if (one_address.group is None):
    #         print(1)
    #         worksheet.write(row, 0, str(one_address.municipalOrganization), f_address_bold)
    #         # list_group_data.append(one_address)
    #         # # print(one_address, 'Просто адрес')
    #         # worksheet.write(row, 0, str(one_address.municipalOrganization), f_address_italic_underline)
    #         # worksheet.write(row, 1, str(one_address.address), f_address_italic_underline)
    #         # worksheet.write(row, col, one_address.fact, num_color)
    #         # worksheet.write(row, col + 1, one_address.limit, num_color)
    #         # worksheet.write(row, col + 2, one_address.otklonenie_new, num_color_cut2)
    #         # worksheet.write(row, col + 3, one_address.otklonenie_percent_new, num_color_cut2)
    #         # worksheet.write(row, col + 4, one_address.sum, num_color_cut3)
    #         # row = row + 1
    #     elif one_address.group not in list_group_data:

    for one_group_data in group_data_4:
        # print(one_group_data, 'Главный адрес')
        list_group_data.append(one_group_data)
        # worksheet.write(row, 0, str(one_address.municipalOrganization), f_address_bold)
        worksheet.write(row, 0, 'Группа адресов', f_address_bold)
        worksheet.write(row, 1, str(one_group_data.titleOfTheAddressGroup), f_address_bold)
        # worksheet.write(row, col, sum_data_final['fact'], num_color_bold)
        worksheet.write(row, col, one_group_data.fact, num_color_bold)
        worksheet.write(row, col + 1, one_group_data.limit, num_color_bold)
        worksheet.write(row, col + 2, one_group_data.otklonenie_new, num_color_bold_cut2)
        worksheet.write(row, col + 3, one_group_data.otklonenie_percent_new, num_color_bold_cut2)
        worksheet.write(row, col + 4, one_group_data.sum, num_color_bold_cut3)
        row = row + 1
        table_address_with_group_data = all_address_4.filter(
            group=one_group_data)
        for k in table_address_with_group_data:
            list_group_data.append(k)
            worksheet.write(row, 0, str(k.municipalOrganization), f_address_bold)
            worksheet.write(row, 1, str(k.address), f_address)
            worksheet.write(row, col, k.fact, num_color)
            worksheet.write(row, col + 1, k.limit, num_color)
            worksheet.write(row, col + 2, k.otklonenie_new, num_color_cut2)
            worksheet.write(row, col + 3, k.otklonenie_percent_new, num_color_cut2)
            worksheet.write(row, col + 4, k.sum, num_color_cut3)
            row = row + 1
    worksheet.merge_range(row, 0, row, 1, '', f_address_bold)
    worksheet.write(row, 0, 'Итог', f_address_bold)
    worksheet.write(row, col, sum_data_final['fact'], num_color)
    worksheet.write(row, col + 1, sum_data_final['limit'], num_color)
    worksheet.write(row, col + 2, sum_data_final['otklonenie'], num_color)
    worksheet.write(row, col + 3, '-', num_color)
    worksheet.write(row, col + 4, sum_data_final['sum'], num_color)
    # for j in list_group_data:
    #     print('write year')
    #     print(j, j.fact, j.limit)


def excel_test(request, year_id):
    year_name = God.objects.get(pk=year_id)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f"attachment; filename=Year {year_name.name}.xlsx"

    workbook = Workbook(response, {'in_memory': True})
    format_color_1 = workbook.add_format({'bg_color': '#FFFFCC'})

    worksheet_1 = workbook.add_worksheet('Отопление')
    worksheet_1.freeze_panes(3, 2)
    worksheet_1.set_row(2, 60)
    worksheet_1.write('C3', '', format_color_1)

    worksheet_2 = workbook.add_worksheet('Компонент, Гкал')
    worksheet_2.freeze_panes(3, 2)
    worksheet_2.set_row(2, 60)
    worksheet_2.write('C3', '', format_color_1)

    worksheet_3 = workbook.add_worksheet('Компонент, тыс.м3')
    worksheet_3.freeze_panes(3, 2)
    worksheet_3.set_row(2, 60)
    worksheet_3.write('C3', '', format_color_1)

    worksheet_4 = workbook.add_worksheet('ХВС')
    worksheet_4.freeze_panes(3, 2)
    worksheet_4.set_row(2, 60)
    worksheet_4.write('C3', '', format_color_1)

    worksheet_5 = workbook.add_worksheet('ВО')
    worksheet_5.freeze_panes(3, 2)
    worksheet_5.set_row(2, 60)
    worksheet_5.write('C3', '', format_color_1)

    worksheet_6 = workbook.add_worksheet('Электричество')
    worksheet_6.freeze_panes(3, 2)
    worksheet_6.set_row(2, 60)
    worksheet_6.write('C3', '', format_color_1)

    format_default = workbook.add_format({
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'border': 1})

    format_default_values = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'border': 1})

    f_address = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'border': 1})

    f_address_bold = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'border': 1,
        'bold': 1})

    f_address_italic_underline = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'border': 1,
        'italic': 1})

    # No color
    format_noc = workbook.add_format({
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'border': 1})

    format_noc_values = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'border': 1})

    format_noc_values_bold = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'border': 1,
        'bold': 1})

    format_noc_values_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'border': 1,
        'num_format': '#####0.00'})

    format_noc_values_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'border': 1,
        'num_format': '#####0.000'})

    format_noc_values_bold_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'border': 1,
        'bold': 1,
        'num_format': '#####0.00'})

    format_noc_values_bold_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'border': 1,
        'bold': 1,
        'num_format': '#####0.000'})

    # Yellow
    format_yellow = workbook.add_format({
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'bg_color': '#FFFFCC',
        'border': 1})

    format_yellow_values = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#FFFFCC',
        'border': 1})

    format_yellow_values_bold = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#FFFFCC',
        'border': 1,
        'bold': 1})

    format_yellow_values_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#FFFFCC',
        'border': 1,
        'num_format': '#####0.00'})

    format_yellow_values_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#FFFFCC',
        'border': 1,
        'num_format': '#####0.000'})

    format_yellow_values_bold_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#FFFFCC',
        'border': 1,
        'bold': 1,
        'num_format': '#####0.00'})

    format_yellow_values_bold_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#FFFFCC',
        'border': 1,
        'bold': 1,
        'num_format': '#####0.000'})

    # Blue
    format_blue = workbook.add_format({
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'bg_color': '#DCE6F1',
        'border': 1})

    format_blue_values = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DCE6F1',
        'border': 1})

    format_blue_values_bold = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DCE6F1',
        'border': 1,
        'bold': 1})

    format_blue_values_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DCE6F1',
        'border': 1,
        'num_format': '#####0.00'})

    format_blue_values_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DCE6F1',
        'border': 1,
        'num_format': '#####0.000'})

    format_blue_values_bold_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DCE6F1',
        'border': 1,
        'bold': 1,
        'num_format': '#####0.00'})

    format_blue_values_bold_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DCE6F1',
        'border': 1,
        'bold': 1,
        'num_format': '#####0.000'})

    # Green
    format_green = workbook.add_format({
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'bg_color': '#D8E4BC',
        'border': 1})

    format_green_values = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#D8E4BC',
        'border': 1})

    format_green_values_bold = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#D8E4BC',
        'border': 1,
        'bold': 1})

    format_green_values_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#D8E4BC',
        'border': 1,
        'num_format': '#####0.00'})

    format_green_values_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#D8E4BC',
        'border': 1,
        'num_format': '#####0.000'})

    format_green_values_bold_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#D8E4BC',
        'border': 1,
        'bold': 1,
        'num_format': '#####0.00'})

    format_green_values_bold_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#D8E4BC',
        'border': 1,
        'bold': 1,
        'num_format': '#####0.000'})

    # Aqua
    format_aqua = workbook.add_format({
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'bg_color': '#DAEEF3',
        'border': 1})

    format_aqua_values = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DAEEF3',
        'border': 1})

    format_aqua_values_bold = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DAEEF3',
        'border': 1,
        'bold': 1})

    format_aqua_values_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DAEEF3',
        'border': 1,
        'num_format': '#####0.00'})

    format_aqua_values_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DAEEF3',
        'border': 1,
        'num_format': '#####0.000'})

    format_aqua_values_bold_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DAEEF3',
        'border': 1,
        'bold': 1,
        'num_format': '#####0.00'})

    format_aqua_values_bold_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#DAEEF3',
        'border': 1,
        'bold': 1,
        'num_format': '#####0.000'})

    # Red
    format_red = workbook.add_format({
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'bg_color': '#F2DCDB',
        'border': 1})

    format_red_values = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#F2DCDB',
        'border': 1})

    format_red_values_bold = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#F2DCDB',
        'border': 1,
        'bold': 1})

    format_red_values_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#F2DCDB',
        'border': 1,
        'num_format': '#####0.00'})

    format_red_values_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#F2DCDB',
        'border': 1,
        'num_format': '#####0.000'})

    format_red_values_bold_cut2 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#F2DCDB',
        'border': 1,
        'bold': 1,
        'num_format': '#####0.00'})

    format_red_values_bold_cut3 = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'bg_color': '#F2DCDB',
        'border': 1,
        'bold': 1,
        'num_format': '#####0.000'})

    # Month
    month_format_default = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'border': 1})

    month_format_yellow = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'bg_color': '#FFFFCC',
        'border': 1})

    month_format_blue = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'bg_color': '#DCE6F1',
        'border': 1})

    month_format_green = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'bg_color': '#D8E4BC',
        'border': 1})

    month_format_aqua = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'bg_color': '#DAEEF3',
        'border': 1})

    month_format_red = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 1,
        'font_name': 'Times New Roman',
        'bg_color': '#F2DCDB',
        'border': 1})

    # Шапка таблицы
    # Общие колонки
    worksheet_1.merge_range('A1:B2', '')
    worksheet_1.set_column(0, 0, 25)
    worksheet_1.set_column(1, 1, 35)
    worksheet_1.write('A3', '№ п/п', format_default)
    worksheet_1.write('B3', 'Наименование учреждения/ адрес                      расположение объекта', format_default)

    worksheet_2.merge_range('A1:B2', '')
    worksheet_2.set_column(0, 0, 25)
    worksheet_2.set_column(1, 1, 35)
    worksheet_2.write('A3', '№ п/п', format_default)
    worksheet_2.write('B3', 'Наименование учреждения/ адрес                      расположение объекта', format_default)

    worksheet_3.merge_range('A1:B2', '')
    worksheet_3.set_column(0, 0, 25)
    worksheet_3.set_column(1, 1, 35)
    worksheet_3.write('A3', '№ п/п', format_default)
    worksheet_3.write('B3', 'Наименование учреждения/ адрес                      расположение объекта', format_default)

    worksheet_4.merge_range('A1:B2', '')
    worksheet_4.set_column(0, 0, 25)
    worksheet_4.set_column(1, 1, 35)
    worksheet_4.write('A3', '№ п/п', format_default)
    worksheet_4.write('B3', 'Наименование учреждения/ адрес                      расположение объекта', format_default)

    worksheet_5.merge_range('A1:B2', '')
    worksheet_5.set_column(0, 0, 25)
    worksheet_5.set_column(1, 1, 35)
    worksheet_5.write('A3', '№ п/п', format_default)
    worksheet_5.write('B3', 'Наименование учреждения/ адрес                      расположение объекта', format_default)

    worksheet_6.merge_range('A1:B2', '')
    worksheet_6.set_column(0, 0, 25)
    worksheet_6.set_column(1, 1, 35)
    worksheet_6.write('A3', '№ п/п', format_default)
    worksheet_6.write('B3', 'Наименование учреждения/ адрес                      расположение объекта', format_default)

    list = [worksheet_1, worksheet_2, worksheet_3, worksheet_4, worksheet_5, worksheet_6]
    categories = Category.objects.all().order_by('pk')
    categories1 = Category.objects.all()
    for i in list:
        # Январь
        i.merge_range('C1:G1', '', month_format_yellow)
        i.merge_range('C2:G2', 'Январь', month_format_yellow)
        i.set_column(2, 6, 11.22)
        i.write('C3', 'Фактическое потребление ', format_yellow)
        i.write('D3', 'Установленный лимит  ', format_yellow)
        i.write('E3', 'отклонение               (лимит-факт) ', format_yellow)
        i.write('F3', 'отклонение               %', format_yellow)
        i.write('G3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_yellow)
        # Февраль
        i.merge_range('H1:L1', '', month_format_blue)
        i.merge_range('H2:L2', 'Февраль', month_format_blue)
        i.set_column(7, 12, 11.22)
        i.write('H3', 'Фактическое потребление ', format_blue)
        i.write('I3', 'Установленный лимит  ', format_blue)
        i.write('J3', 'отклонение               (лимит-факт) ', format_blue)
        i.write('K3', 'отклонение               %', format_blue)
        i.write('L3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_blue)
        # Март
        i.merge_range('M1:Q1', '', month_format_green)
        i.merge_range('M2:Q2', 'Март', month_format_green)
        i.set_column(13, 18, 11.22)
        i.write('M3', 'Фактическое потребление ', format_green)
        i.write('N3', 'Установленный лимит  ', format_green)
        i.write('O3', 'отклонение               (лимит-факт) ', format_green)
        i.write('P3', 'отклонение               %', format_green)
        i.write('Q3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_green)
        # 1 Квартал
        i.merge_range('R1:V1', '', month_format_default)
        i.merge_range('R2:V2', '1 Квартал', month_format_default)
        i.set_column(19, 24, 11.22)
        i.write('R3', 'Фактическое потребление ', format_default)
        i.write('S3', 'Установленный лимит  ', format_default)
        i.write('T3', 'отклонение               (лимит-факт) ', format_default)
        i.write('U3', 'отклонение               %', format_default)
        i.write('V3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_default)
        # Апрель
        i.merge_range('W1:AA1', '', month_format_yellow)
        i.merge_range('W2:AA2', 'Апрель', month_format_yellow)
        i.set_column(25, 30, 11.22)
        i.write('W3', 'Фактическое потребление ', format_yellow)
        i.write('X3', 'Установленный лимит  ', format_yellow)
        i.write('Y3', 'отклонение               (лимит-факт) ', format_yellow)
        i.write('Z3', 'отклонение               %', format_yellow)
        i.write('AA3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_yellow)
        # Май
        i.merge_range('AB1:AF1', '', month_format_blue)
        i.merge_range('AB2:AF2', 'Май', month_format_blue)
        i.set_column(31, 36, 11.22)
        i.write('AB3', 'Фактическое потребление ', format_blue)
        i.write('AC3', 'Установленный лимит  ', format_blue)
        i.write('AD3', 'отклонение               (лимит-факт) ', format_blue)
        i.write('AE3', 'отклонение               %', format_blue)
        i.write('AF3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_blue)
        # Июнь
        i.merge_range('AG1:AK1', '', month_format_green)
        i.merge_range('AG2:AK2', 'Июнь', month_format_green)
        i.set_column(37, 42, 11.22)
        i.write('AG3', 'Фактическое потребление ', format_green)
        i.write('AH3', 'Установленный лимит  ', format_green)
        i.write('AI3', 'отклонение               (лимит-факт) ', format_green)
        i.write('AJ3', 'отклонение               %', format_green)
        i.write('AK3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_green)
        # 2 Квартал
        i.merge_range('AL1:AP1', '', month_format_default)
        i.merge_range('AL2:AP2', '2 Квартал', month_format_default)
        i.set_column(43, 48, 11.22)
        i.write('AL3', 'Фактическое потребление ', format_default)
        i.write('AM3', 'Установленный лимит  ', format_default)
        i.write('AN3', 'отклонение               (лимит-факт) ', format_default)
        i.write('AO3', 'отклонение               %', format_default)
        i.write('AP3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_default)
        # 1 Полугодие
        i.merge_range('AQ1:AU1', '', month_format_aqua)
        i.merge_range('AQ2:AU2', '1 Полугодие', month_format_aqua)
        i.set_column(49, 54, 11.22)
        i.write('AQ3', 'Фактическое потребление ', format_aqua)
        i.write('AR3', 'Установленный лимит  ', format_aqua)
        i.write('AS3', 'отклонение               (лимит-факт) ', format_aqua)
        i.write('AT3', 'отклонение               %', format_aqua)
        i.write('AU3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_aqua)
        # Июль
        i.merge_range('AV1:AZ1', '', month_format_yellow)
        i.merge_range('AV2:AZ2', 'Июль', month_format_yellow)
        i.set_column(49, 54, 11.22)
        i.write('AV3', 'Фактическое потребление ', format_yellow)
        i.write('AW3', 'Установленный лимит  ', format_yellow)
        i.write('AX3', 'отклонение               (лимит-факт) ', format_yellow)
        i.write('AY3', 'отклонение               %', format_yellow)
        i.write('AZ3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_yellow)
        # Август
        i.merge_range('BA1:BE1', '', month_format_blue)
        i.merge_range('BA2:BE2', 'Август', month_format_blue)
        i.set_column(55, 60, 11.22)
        i.write('BA3', 'Фактическое потребление ', format_blue)
        i.write('BB3', 'Установленный лимит  ', format_blue)
        i.write('BC3', 'отклонение               (лимит-факт) ', format_blue)
        i.write('BD3', 'отклонение               %', format_blue)
        i.write('BE3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_blue)
        # Сентябрь
        i.merge_range('BF1:BJ1', '', month_format_green)
        i.merge_range('BF2:BJ2', 'Сентябрь', month_format_green)
        i.set_column(61, 66, 11.22)
        i.write('BF3', 'Фактическое потребление ', format_green)
        i.write('BG3', 'Установленный лимит  ', format_green)
        i.write('BH3', 'отклонение               (лимит-факт) ', format_green)
        i.write('BI3', 'отклонение               %', format_green)
        i.write('BJ3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_green)
        # 3 Квартал
        i.merge_range('BK1:BO1', '', month_format_default)
        i.merge_range('BK2:BO2', '3 Квартал', month_format_default)
        i.set_column(67, 72, 11.22)
        i.write('BK3', 'Фактическое потребление ', format_default)
        i.write('BL3', 'Установленный лимит  ', format_default)
        i.write('BM3', 'отклонение               (лимит-факт) ', format_default)
        i.write('BN3', 'отклонение               %', format_default)
        i.write('BO3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_default)
        # Октябрь
        i.merge_range('BP1:BT1', '', month_format_yellow)
        i.merge_range('BP2:BT2', 'Октябрь', month_format_yellow)
        i.set_column(73, 78, 11.22)
        i.write('BP3', 'Фактическое потребление ', format_yellow)
        i.write('BQ3', 'Установленный лимит  ', format_yellow)
        i.write('BR3', 'отклонение               (лимит-факт) ', format_yellow)
        i.write('BS3', 'отклонение               %', format_yellow)
        i.write('BT3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_yellow)
        # Ноябрь
        i.merge_range('BU1:BY1', '', month_format_blue)
        i.merge_range('BU2:BY2', 'Ноябрь', month_format_blue)
        i.set_column(79, 84, 11.22)
        i.write('BU3', 'Фактическое потребление ', format_blue)
        i.write('BV3', 'Установленный лимит  ', format_blue)
        i.write('BW3', 'отклонение               (лимит-факт) ', format_blue)
        i.write('BX3', 'отклонение               %', format_blue)
        i.write('BY3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_blue)
        # Декабрь
        i.merge_range('BZ1:CD1', '', month_format_green)
        i.merge_range('BZ2:CD2', 'Декабрь', month_format_green)
        i.set_column(85, 90, 11.22)
        i.write('BZ3', 'Фактическое потребление ', format_green)
        i.write('CA3', 'Установленный лимит  ', format_green)
        i.write('CB3', 'отклонение               (лимит-факт) ', format_green)
        i.write('CC3', 'отклонение               %', format_green)
        i.write('CD3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_green)
        # 4 Квартал
        i.merge_range('CE1:CI1', '', month_format_default)
        i.merge_range('CE2:CI2', '4 Квартал', month_format_default)
        i.set_column(91, 96, 11.22)
        i.write('CE3', 'Фактическое потребление ', format_default)
        i.write('CF3', 'Установленный лимит  ', format_default)
        i.write('CG3', 'отклонение               (лимит-факт) ', format_default)
        i.write('CH3', 'отклонение               %', format_default)
        i.write('CI3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_default)
        # Год
        i.merge_range('CJ1:CN1', '', month_format_red)
        i.merge_range('CJ2:CN2', 'Год', month_format_red)
        i.set_column(97, 102, 11.22)
        i.write('CJ3', 'Фактическое потребление ', format_red)
        i.write('CK3', 'Установленный лимит  ', format_red)
        i.write('CL3', 'отклонение               (лимит-факт) ', format_red)
        i.write('CM3', 'отклонение               %', format_red)
        i.write('CN3', 'Сумма, выставленная по счетам, тыс.руб. (с НДС)', format_red)

    for sheet, category in zip(list, categories):
        write_year(year_id=year_id, category_id=category.id, worksheet=sheet, colonnna=87, f_address=f_address,
                   f_address_bold=f_address_bold,
                   num_color=format_red_values, num_color_bold=format_red_values_bold,
                   num_color_cut2=format_red_values_cut2,
                   num_color_cut3=format_red_values_cut3, num_color_bold_cut2=format_red_values_bold_cut2,
                   num_color_bold_cut3=format_red_values_bold_cut3, f_address_italic_underline=f_address_italic_underline)
        write_polugodie(year_id=year_id, polugodie_id=1, category_id=category.id, worksheet=sheet, colonnna=42,
                        num_color=format_aqua_values, num_color_bold=format_aqua_values_bold, num_color_cut2=format_aqua_values_cut2,
                    num_color_cut3=format_aqua_values_cut3, num_color_bold_cut2=format_aqua_values_bold_cut2,
                    num_color_bold_cut3=format_aqua_values_bold_cut3)
        # Январь
        write_month(year_id=year_id, month_id=1, category_id=category.id, worksheet=sheet, colonna=2,
                    num_color=format_yellow_values, num_color_bold=format_yellow_values_bold,
                    num_color_cut2=format_yellow_values_cut2,
                    num_color_cut3=format_yellow_values_cut3, num_color_bold_cut2=format_yellow_values_bold_cut2,
                    num_color_bold_cut3=format_yellow_values_bold_cut3)
        # Февраль
        write_month(year_id=year_id, month_id=2, category_id=category.id, worksheet=sheet, colonna=7, num_color=format_blue_values,
                    num_color_bold=format_blue_values_bold, num_color_cut2=format_blue_values_cut2,
                    num_color_cut3=format_blue_values_cut3, num_color_bold_cut2=format_blue_values_bold_cut2,
                    num_color_bold_cut3=format_blue_values_bold_cut3)
        # # Март
        write_month(year_id=year_id, month_id=3, category_id=category.id, worksheet=sheet, colonna=12,
                    num_color=format_green_values, num_color_bold=format_green_values_bold, num_color_cut2=format_green_values_cut2,
                    num_color_cut3=format_green_values_cut3, num_color_bold_cut2=format_green_values_bold_cut2,
                    num_color_bold_cut3=format_green_values_bold_cut3)
        # # Апрель
        write_month(year_id=year_id, month_id=4, category_id=category.id, worksheet=sheet, colonna=22,
                    num_color=format_yellow_values, num_color_bold=format_yellow_values_bold, num_color_cut2=format_yellow_values_cut2,
                    num_color_cut3=format_yellow_values_cut3, num_color_bold_cut2=format_yellow_values_bold_cut2,
                    num_color_bold_cut3=format_yellow_values_bold_cut3)
        # # Май
        write_month(year_id=year_id, month_id=5, category_id=category.id, worksheet=sheet, colonna=27, num_color=format_blue_values,
                    num_color_bold=format_blue_values_bold, num_color_cut2=format_blue_values_cut2,
                    num_color_cut3=format_blue_values_cut3, num_color_bold_cut2=format_blue_values_bold_cut2,
                    num_color_bold_cut3=format_blue_values_bold_cut3)
        # # Июнь
        write_month(year_id=year_id, month_id=6, category_id=category.id, worksheet=sheet, colonna=32,
                    num_color=format_green_values, num_color_bold=format_green_values_bold, num_color_cut2=format_green_values_cut2,
                    num_color_cut3=format_green_values_cut3, num_color_bold_cut2=format_green_values_bold_cut2,
                    num_color_bold_cut3=format_green_values_bold_cut3)
        # # Июль
        write_month(year_id=year_id, month_id=7, category_id=category.id, worksheet=sheet, colonna=47,
                    num_color=format_yellow_values, num_color_bold=format_yellow_values_bold, num_color_cut2=format_yellow_values_cut2,
                    num_color_cut3=format_yellow_values_cut3, num_color_bold_cut2=format_yellow_values_bold_cut2,
                    num_color_bold_cut3=format_yellow_values_bold_cut3)
        # # Август
        write_month(year_id=year_id, month_id=8, category_id=category.id, worksheet=sheet, colonna=52, num_color=format_blue_values,
                    num_color_bold=format_blue_values_bold, num_color_cut2=format_blue_values_cut2,
                    num_color_cut3=format_blue_values_cut3, num_color_bold_cut2=format_blue_values_bold_cut2,
                    num_color_bold_cut3=format_blue_values_bold_cut3)
        # # Сентябрь
        write_month(year_id=year_id, month_id=9, category_id=category.id, worksheet=sheet, colonna=57,
                    num_color=format_green_values, num_color_bold=format_green_values_bold, num_color_cut2=format_green_values_cut2,
                    num_color_cut3=format_green_values_cut3, num_color_bold_cut2=format_green_values_bold_cut2,
                    num_color_bold_cut3=format_green_values_bold_cut3)
        # # Октябрь
        write_month(year_id=year_id, month_id=10, category_id=category.id, worksheet=sheet, colonna=67,
                    num_color=format_yellow_values, num_color_bold=format_yellow_values_bold, num_color_cut2=format_yellow_values_cut2,
                    num_color_cut3=format_yellow_values_cut3, num_color_bold_cut2=format_yellow_values_bold_cut2,
                    num_color_bold_cut3=format_yellow_values_bold_cut3)
        # # Ноябрь
        write_month(year_id=year_id, month_id=11, category_id=category.id, worksheet=sheet, colonna=72,
                    num_color=format_blue_values, num_color_bold=format_blue_values_bold, num_color_cut2=format_blue_values_cut2,
                    num_color_cut3=format_blue_values_cut3, num_color_bold_cut2=format_blue_values_bold_cut2,
                    num_color_bold_cut3=format_blue_values_bold_cut3)
        # # Декабрь
        write_month(year_id=year_id, month_id=12, category_id=category.id, worksheet=sheet, colonna=77,
                    num_color=format_green_values, num_color_bold=format_green_values_bold, num_color_cut2=format_green_values_cut2,
                    num_color_cut3=format_green_values_cut3, num_color_bold_cut2=format_green_values_bold_cut2,
                    num_color_bold_cut3=format_green_values_bold_cut3)
        # 1 Квартал
        write_quarter(year_id=year_id, category_id=category.id, quarter_id=3, worksheet=sheet, colonna=17,
                      num_color=format_noc_values, num_color_bold=format_noc_values_bold,
                      num_color_cut2=format_noc_values_cut2,
                      num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
                      num_color_bold_cut3=format_noc_values_bold_cut3)
        # 2 Квартал
        write_quarter(year_id=year_id, category_id=category.id, quarter_id=4, worksheet=sheet, colonna=37,
                      num_color=format_noc_values, num_color_bold=format_noc_values_bold,
                      num_color_cut2=format_noc_values_cut2,
                      num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
                      num_color_bold_cut3=format_noc_values_bold_cut3)
        # 3 Квартал
        write_quarter(year_id=year_id, category_id=category.id, quarter_id=5, worksheet=sheet, colonna=62,
                      num_color=format_noc_values, num_color_bold=format_noc_values_bold,
                      num_color_cut2=format_noc_values_cut2,
                      num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
                      num_color_bold_cut3=format_noc_values_bold_cut3)
        # 4 Квартал
        write_quarter(year_id=year_id, category_id=category.id, quarter_id=6, worksheet=sheet, colonna=82,
                      num_color=format_noc_values, num_color_bold=format_noc_values_bold,
                      num_color_cut2=format_noc_values_cut2,
                      num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
                      num_color_bold_cut3=format_noc_values_bold_cut3)



    # write_year(year_id=year_id, category_id=1, worksheet=worksheet_1, colonnna=87, f_address=f_address,
    #            f_address_bold=f_address_bold,
    #            num_color=format_red_values, num_color_bold=format_red_values_bold,
    #            num_color_cut2=format_red_values_cut2,
    #            num_color_cut3=format_red_values_cut3, num_color_bold_cut2=format_red_values_bold_cut2,
    #            num_color_bold_cut3=format_red_values_bold_cut3, f_address_italic_underline=f_address_italic_underline)
    # write_year(year_id=year_id, category_id=2, worksheet=worksheet_2, colonnna=87, f_address=f_address,
    #            f_address_bold=f_address_bold,
    #            num_color=format_red_values, num_color_bold=format_red_values_bold,
    #            num_color_cut2=format_red_values_cut2,
    #            num_color_cut3=format_red_values_cut3, num_color_bold_cut2=format_red_values_bold_cut2,
    #            num_color_bold_cut3=format_red_values_bold_cut3, f_address_italic_underline=f_address_italic_underline)

    # write_polugodie(year_id=year_id, polugodie_id=1, category_id=2, worksheet=worksheet_2, colonnna=42,
    #                 num_color=format_aqua_values, num_color_bold=format_aqua_values_bold, num_color_cut2=format_aqua_values_cut2,
    #             num_color_cut3=format_aqua_values_cut3, num_color_bold_cut2=format_aqua_values_bold_cut2,
    #             num_color_bold_cut3=format_aqua_values_bold_cut3)
    # # 1 Квартал
    # write_quarter(year_id=year_id, category_id=1, quarter_id=3, worksheet=worksheet_1, colonna=17,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold, num_color_cut2=format_noc_values_cut2,
    #             num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #             num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=2, quarter_id=3, worksheet=worksheet_2, colonna=17,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=3, quarter_id=3, worksheet=worksheet_3, colonna=17,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=4, quarter_id=3, worksheet=worksheet_4, colonna=17,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=5, quarter_id=3, worksheet=worksheet_5, colonna=17,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=6, quarter_id=3, worksheet=worksheet_6, colonna=17,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # # 2 Квартал
    # write_quarter(year_id=year_id, category_id=1, quarter_id=4, worksheet=worksheet_1, colonna=37,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=2, quarter_id=4, worksheet=worksheet_2, colonna=37,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=3, quarter_id=4, worksheet=worksheet_3, colonna=37,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=4, quarter_id=4, worksheet=worksheet_4, colonna=37,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=5, quarter_id=4, worksheet=worksheet_5, colonna=37,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=6, quarter_id=4, worksheet=worksheet_6, colonna=37,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # # 3 Квартал
    # write_quarter(year_id=year_id, category_id=1, quarter_id=5, worksheet=worksheet_1, colonna=62,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=2, quarter_id=5, worksheet=worksheet_2, colonna=62,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=3, quarter_id=5, worksheet=worksheet_3, colonna=62,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=4, quarter_id=5, worksheet=worksheet_4, colonna=62,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=5, quarter_id=5, worksheet=worksheet_5, colonna=62,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=6, quarter_id=5, worksheet=worksheet_6, colonna=62,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # # 4 Квартал
    # write_quarter(year_id=year_id, category_id=1, quarter_id=6, worksheet=worksheet_1, colonna=82,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=2, quarter_id=6, worksheet=worksheet_2, colonna=82,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=3, quarter_id=6, worksheet=worksheet_3, colonna=82,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=4, quarter_id=6, worksheet=worksheet_4, colonna=82,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=5, quarter_id=6, worksheet=worksheet_5, colonna=82,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)
    # write_quarter(year_id=year_id, category_id=6, quarter_id=6, worksheet=worksheet_6, colonna=82,
    #               num_color=format_noc_values, num_color_bold=format_noc_values_bold,
    #               num_color_cut2=format_noc_values_cut2,
    #               num_color_cut3=format_noc_values_cut3, num_color_bold_cut2=format_noc_values_bold_cut2,
    #               num_color_bold_cut3=format_noc_values_bold_cut3)

    workbook.close()
    return response
