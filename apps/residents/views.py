
# import datetime
# # pyrefly: ignore [missing-import]
# from django.shortcuts import render

# # Create your views here.

# def add_resident(request):
#     return render(request, "residents/add_resident.html")


from django.shortcuts import render



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *
from apps.rooms.models import Facility
from django.shortcuts import get_object_or_404
from django.http import JsonResponse


def add_resident(request):
    return render(request, "residents/add_resident.html")

def resident_list(request):
    return render(request, "residents/resident_list.html")
  
def add_resident(request):
    return render(request, "residents/add_resident.html")


def resident_list(request):
    return render(request, "residents/list.html")

# Resident detail
class ResidentDetail(View):

    def get(self, request, pk):
        resident = Resident.objects.get(pk=pk)
        
        # distinguish each type of Contact
        self_contact = resident.residentcontact_set.filter(relationship_type='Self').first()
        if self_contact == None:
            self_contact = resident.residentcontact_set.exclude(relationship_type='POA').first()

        emergency_contact = resident.residentcontact_set.filter(is_emergency_contact=True).first()
        
        poa_contact = resident.residentcontact_set.filter(is_guarantor=True).first()
        if not poa_contact:
            poa_contact = resident.residentcontact_set.exclude(relationship_type='Self').exclude(is_emergency_contact=True).first()
        
        return render(request, "residents/resident_detail.html", {
            'resident': resident,
            'self_contact': self_contact,
            'emergency_contact': emergency_contact,
            'poa_contact': poa_contact,
        })
class ResidentEdit(View):
    def get(self, request, pk):
        
        resident = get_object_or_404(Resident, pk=pk)
        
        initial_data = {}
        
        # Address
        if resident.address:
            initial_data['address_line1'] = resident.address.street_line1
            initial_data['address_line2'] = resident.address.street_line2
            initial_data['address_city'] = resident.address.city
            initial_data['address_state'] = resident.address.state
            initial_data['address_zip_code'] = resident.address.zip_code
            
        # SSN
        if hasattr(resident, 'residentsensitiveinfo'):
            initial_data['ssn'] = resident.residentsensitiveinfo.ssn_encrypted
            
        # Admission / Referral Source
        admission = resident.admission_set.first()
        if admission:
            initial_data['referral_source'] = admission.referral_source
            
        # Contacts
        self_contact = resident.residentcontact_set.filter(relationship_type='Self').first()
        if self_contact:
            initial_data['phone_primary'] = self_contact.contact.phone_primary
            initial_data['phone_secondary'] = self_contact.contact.phone_secondary
            
        emergency_rc = resident.residentcontact_set.filter(is_emergency_contact=True).first()
        if emergency_rc:
            initial_data['emergency_first_name'] = emergency_rc.contact.first_name
            initial_data['emergency_last_name'] = emergency_rc.contact.last_name
            initial_data['emergency_phone_primary'] = emergency_rc.contact.phone_primary
            initial_data['emergency_phone_secondary'] = emergency_rc.contact.phone_secondary
            
        poa_rc = resident.residentcontact_set.filter(is_guarantor=True).first()
        if not poa_rc:
            poa_rc = resident.residentcontact_set.exclude(relationship_type='Self').exclude(is_emergency_contact=True).first()
        if poa_rc:
            initial_data['poa_on_file'] = True
            initial_data['poa_first_name'] = poa_rc.contact.first_name
            initial_data['poa_last_name'] = poa_rc.contact.last_name
            initial_data['poa_phone_primary'] = poa_rc.contact.phone_primary
            initial_data['poa_phone_secondary'] = poa_rc.contact.phone_secondary
            initial_data['poa_relationship'] = poa_rc.relationship_type
            
        # Insurance
        policy = resident.residentinsurancepolicy_set.first()
        if policy:
            initial_data['policy_number'] = policy.policy_number_encrypted
            initial_data['policy_effective_from'] = policy.effective_from
            initial_data['policy_effective_to'] = policy.effective_to
            initial_data['auth_number'] = policy.auth_number
            if policy.insurance_provider:
                initial_data['insurance_provider_name'] = policy.insurance_provider.provider_name
                initial_data['insurance_provider_type'] = policy.insurance_provider.provider_type
        
        form = ResidentForm(instance=resident, initial=initial_data)
        return render(request, "residents/resident_form.html", {'form': form, 'resident': resident, 'is_edit': True})
    
    def post(self, request, pk):
        resident = get_object_or_404(Resident, pk=pk)
        form = ResidentForm(request.POST, instance=resident)
        
        if form.is_valid():
            resident = form.save()
            
            # --- EXTRACT DATA ---
            ssn = form.cleaned_data.get('ssn')
            referral_source = form.cleaned_data.get('referral_source')
            
            address_line1 = form.cleaned_data.get('address_line1')
            address_line2 = form.cleaned_data.get('address_line2')
            address_city = form.cleaned_data.get('address_city')
            address_state = form.cleaned_data.get('address_state')
            address_zip_code = form.cleaned_data.get('address_zip_code')
            
            phone_primary = form.cleaned_data.get('phone_primary')
            phone_secondary = form.cleaned_data.get('phone_secondary')
            
            emergency_first_name = form.cleaned_data.get('emergency_first_name')
            emergency_last_name = form.cleaned_data.get('emergency_last_name')
            emergency_phone_primary = form.cleaned_data.get('emergency_phone_primary')
            emergency_phone_secondary = form.cleaned_data.get('emergency_phone_secondary')
            
            poa_first_name = form.cleaned_data.get('poa_first_name')
            poa_last_name = form.cleaned_data.get('poa_last_name')
            poa_phone_primary = form.cleaned_data.get('poa_phone_primary')
            poa_phone_secondary = form.cleaned_data.get('poa_phone_secondary')
            poa_relationship = form.cleaned_data.get('poa_relationship')
            poa_on_file = form.cleaned_data.get('poa_on_file')
            
            insurance_provider_name = form.cleaned_data.get('insurance_provider_name')
            insurance_provider_type = form.cleaned_data.get('insurance_provider_type')
            policy_number = form.cleaned_data.get('policy_number')
            policy_effective_from = form.cleaned_data.get('policy_effective_from')
            policy_effective_to = form.cleaned_data.get('policy_effective_to')
            auth_number = form.cleaned_data.get('auth_number')

            # --- UPDATE ADDRESS ---
            if address_line1 is not None or address_city is not None or address_state is not None:
                if resident.address:
                    if address_line1 is not None: resident.address.street_line1 = address_line1
                    if address_line2 is not None: resident.address.street_line2 = address_line2
                    if address_city is not None: resident.address.city = address_city
                    if address_state is not None: resident.address.state = address_state
                    if address_zip_code is not None: resident.address.zip_code = address_zip_code
                    resident.address.save()
                else:
                    addr = Address.objects.create(
                        street_line1=address_line1 or '',
                        street_line2=address_line2 or '',
                        city=address_city or '',
                        state=address_state or '',
                        zip_code=address_zip_code or '',
                        address_type='HOME'
                    )
                    resident.address = addr
                    resident.save()

            # --- UPDATE SENSITIVE INFO ---
            if ssn:
                info, _ = ResidentSensitiveInfo.objects.get_or_create(resident=resident)
                info.ssn_encrypted = ssn
                info.save()

            # --- UPDATE ADMISSION (Referral) ---
            if referral_source is not None:
                admission = resident.admission_set.first()
                if admission:
                    admission.referral_source = referral_source
                    admission.save()
                else:
                    from apps.rooms.models import Facility
                    facility = Facility.objects.first()
                    if facility:
                        Admission.objects.create(
                            resident=resident, facility=facility, 
                            referral_source=referral_source, admission_date=resident.date_of_birth
                        )

            # --- UPDATE SELF CONTACT ---
            if phone_primary is not None or phone_secondary is not None:
                self_rc = resident.residentcontact_set.filter(relationship_type='Self').first()
                if self_rc:
                    if phone_primary is not None: self_rc.contact.phone_primary = phone_primary
                    if phone_secondary is not None: self_rc.contact.phone_secondary = phone_secondary
                    self_rc.contact.save()
                else:
                    c_self = Contact.objects.create(
                        first_name=resident.first_name,
                        last_name=resident.last_name,
                        phone_primary=phone_primary or '',
                        phone_secondary=phone_secondary or ''
                    )
                    ResidentContact.objects.create(resident=resident, contact=c_self, relationship_type='Self')

            # --- UPDATE EMERGENCY CONTACT ---
            if emergency_first_name is not None or emergency_last_name is not None or emergency_phone_primary is not None:
                em_rc = resident.residentcontact_set.filter(is_emergency_contact=True).first()
                if em_rc:
                    if emergency_first_name is not None: em_rc.contact.first_name = emergency_first_name
                    if emergency_last_name is not None: em_rc.contact.last_name = emergency_last_name
                    if emergency_phone_primary is not None: em_rc.contact.phone_primary = emergency_phone_primary
                    if emergency_phone_secondary is not None: em_rc.contact.phone_secondary = emergency_phone_secondary
                    em_rc.contact.save()
                else:
                    c_em = Contact.objects.create(
                        first_name=emergency_first_name or '',
                        last_name=emergency_last_name or '',
                        phone_primary=emergency_phone_primary or '',
                        phone_secondary=emergency_phone_secondary or ''
                    )
                    ResidentContact.objects.create(resident=resident, contact=c_em, relationship_type='Emergency', is_emergency_contact=True)

            # --- UPDATE POA CONTACT ---
            poa_rc = resident.residentcontact_set.filter(is_guarantor=True).first()
            if not poa_rc:
                poa_rc = resident.residentcontact_set.exclude(relationship_type='Self').exclude(is_emergency_contact=True).first()
            
            if poa_on_file:
                if poa_rc:
                    poa_rc.is_guarantor = True
                    if poa_first_name is not None: poa_rc.contact.first_name = poa_first_name
                    if poa_last_name is not None: poa_rc.contact.last_name = poa_last_name
                    if poa_phone_primary is not None: poa_rc.contact.phone_primary = poa_phone_primary
                    if poa_phone_secondary is not None: poa_rc.contact.phone_secondary = poa_phone_secondary
                    if poa_relationship:
                        poa_rc.relationship_type = poa_relationship
                    poa_rc.save()
                    poa_rc.contact.save()
                else:
                    c_poa = Contact.objects.create(
                        first_name=poa_first_name or '',
                        last_name=poa_last_name or '',
                        phone_primary=poa_phone_primary or '',
                        phone_secondary=poa_phone_secondary or ''
                    )
                    ResidentContact.objects.create(resident=resident, contact=c_poa, relationship_type=poa_relationship or 'POA', is_guarantor=True)
            else:
                if poa_rc:
                    poa_rc.delete()

            # --- UPDATE INSURANCE ---
            if insurance_provider_name or policy_number or policy_effective_from or policy_effective_to:
                policy = resident.residentinsurancepolicy_set.first()
                provider = None
                from apps.billing.models import InsuranceProvider, ResidentInsurancePolicy
                if insurance_provider_name:
                    provider, _ = InsuranceProvider.objects.get_or_create(
                        provider_name=insurance_provider_name, 
                        defaults={'provider_type': insurance_provider_type or 'OTHER'}
                    )
                elif insurance_provider_type:
                    provider = InsuranceProvider.objects.filter(provider_type=insurance_provider_type).first()
                    
                if policy:
                    if provider: policy.insurance_provider = provider
                    if policy_number is not None: policy.policy_number_encrypted = policy_number
                    if policy_effective_from is not None: policy.effective_from = policy_effective_from
                    if policy_effective_to is not None: policy.effective_to = policy_effective_to
                    if auth_number is not None: policy.auth_number = auth_number
                    policy.save()
                elif provider:
                    ResidentInsurancePolicy.objects.create(
                        resident=resident,
                        insurance_provider=provider,
                        policy_number_encrypted=policy_number or '',
                        effective_from=policy_effective_from or resident.date_of_birth,
                        effective_to=policy_effective_to,
                        auth_number=auth_number
                    )
            messages.success(request, f'Resident {resident.first_name} {resident.last_name} updated successfully.')
            return redirect('residents:resident_detail', pk=resident.pk)
        
        return render(request, 'residents/resident_form.html', {'form': form, 'resident': resident, 'is_edit': True})

class ResidentCreate(View):
    def get(self, request):
        form = ResidentForm()
        return render(request, "residents/resident_form.html", {'form': form, 'is_edit': False})
        
    def post(self, request):
        form = ResidentForm(request.POST)
        
        if form.is_valid():
            resident = form.save()
            
            # --- EXTRACT DATA ---
            ssn = form.cleaned_data.get('ssn')
            referral_source = form.cleaned_data.get('referral_source')
            
            address_line1 = form.cleaned_data.get('address_line1')
            address_line2 = form.cleaned_data.get('address_line2')
            address_city = form.cleaned_data.get('address_city')
            address_state = form.cleaned_data.get('address_state')
            address_zip_code = form.cleaned_data.get('address_zip_code')
            
            phone_primary = form.cleaned_data.get('phone_primary')
            phone_secondary = form.cleaned_data.get('phone_secondary')
            
            emergency_first_name = form.cleaned_data.get('emergency_first_name')
            emergency_last_name = form.cleaned_data.get('emergency_last_name')
            emergency_phone_primary = form.cleaned_data.get('emergency_phone_primary')
            emergency_phone_secondary = form.cleaned_data.get('emergency_phone_secondary')
            
            poa_first_name = form.cleaned_data.get('poa_first_name')
            poa_last_name = form.cleaned_data.get('poa_last_name')
            poa_phone_primary = form.cleaned_data.get('poa_phone_primary')
            poa_phone_secondary = form.cleaned_data.get('poa_phone_secondary')
            poa_relationship = form.cleaned_data.get('poa_relationship')
            poa_on_file = form.cleaned_data.get('poa_on_file')
            
            insurance_provider_name = form.cleaned_data.get('insurance_provider_name')
            insurance_provider_type = form.cleaned_data.get('insurance_provider_type')
            policy_number = form.cleaned_data.get('policy_number')
            policy_effective_from = form.cleaned_data.get('policy_effective_from')
            policy_effective_to = form.cleaned_data.get('policy_effective_to')
            auth_number = form.cleaned_data.get('auth_number')

            # --- CREATE ADDRESS ---
            if address_line1 is not None or address_city is not None or address_state is not None:
                addr = Address.objects.create(
                    street_line1=address_line1 or '',
                    street_line2=address_line2 or '',
                    city=address_city or '',
                    state=address_state or '',
                    zip_code=address_zip_code or '',
                    address_type='HOME'
                )
                resident.address = addr
                resident.save()

            # --- CREATE SENSITIVE INFO ---
            if ssn:
                ResidentSensitiveInfo.objects.create(resident=resident, ssn_encrypted=ssn)

            # --- CREATE ADMISSION (Referral) ---
            if referral_source is not None:
                from apps.rooms.models import Facility
                facility = Facility.objects.first()
                if facility:
                    Admission.objects.create(
                        resident=resident, facility=facility, 
                        referral_source=referral_source, admission_date=resident.date_of_birth
                    )

            # --- CREATE SELF CONTACT ---
            if phone_primary is not None or phone_secondary is not None:
                c_self = Contact.objects.create(
                    first_name=resident.first_name,
                    last_name=resident.last_name,
                    phone_primary=phone_primary or '',
                    phone_secondary=phone_secondary or ''
                )
                ResidentContact.objects.create(resident=resident, contact=c_self, relationship_type='Self')

            # --- CREATE EMERGENCY CONTACT ---
            if emergency_first_name is not None or emergency_last_name is not None or emergency_phone_primary is not None:
                c_em = Contact.objects.create(
                    first_name=emergency_first_name or '',
                    last_name=emergency_last_name or '',
                    phone_primary=emergency_phone_primary or '',
                    phone_secondary=emergency_phone_secondary or ''
                )
                ResidentContact.objects.create(resident=resident, contact=c_em, relationship_type='Emergency', is_emergency_contact=True)

            # --- CREATE POA CONTACT ---
            if poa_on_file:
                c_poa = Contact.objects.create(
                    first_name=poa_first_name or '',
                    last_name=poa_last_name or '',
                    phone_primary=poa_phone_primary or '',
                    phone_secondary=poa_phone_secondary or ''
                )
                ResidentContact.objects.create(resident=resident, contact=c_poa, relationship_type=poa_relationship or 'POA', is_guarantor=True)

            # --- CREATE INSURANCE ---
            if insurance_provider_name or policy_number or policy_effective_from or policy_effective_to:
                provider = None
                from apps.billing.models import InsuranceProvider, ResidentInsurancePolicy
                if insurance_provider_name:
                    provider, _ = InsuranceProvider.objects.get_or_create(
                        provider_name=insurance_provider_name, 
                        defaults={'provider_type': insurance_provider_type or 'OTHER'}
                    )
                elif insurance_provider_type:
                    provider = InsuranceProvider.objects.filter(provider_type=insurance_provider_type).first()
                    
                if provider:
                    ResidentInsurancePolicy.objects.create(
                        resident=resident,
                        insurance_provider=provider,
                        policy_number_encrypted=policy_number or '',
                        effective_from=policy_effective_from or resident.date_of_birth,
                        effective_to=policy_effective_to,
                        auth_number=auth_number
                    )
                    
            messages.success(request, f'Resident {resident.first_name} {resident.last_name} created successfully.')
            return redirect('residents:resident_detail', pk=resident.pk)
        
        return render(request, 'residents/resident_form.html', {'form': form, 'is_edit': False})



def check_similar_resident(request):
    first_name = request.GET.get('first_name', '').strip()
    last_name = request.GET.get('last_name', '').strip()
    exclude_id = request.GET.get('exclude_id')
    
    if len(first_name) > 1 and len(last_name) > 1:
        qs = Resident.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name)
        if exclude_id and exclude_id.isdigit():
            qs = qs.exclude(pk=int(exclude_id))
        return JsonResponse({'exists': qs.exists()})
    return JsonResponse({'exists': False})




