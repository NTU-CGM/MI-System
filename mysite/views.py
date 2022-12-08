from django.shortcuts import render
from mysite import models, forms
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from wsgiref.util import FileWrapper
from django.contrib.sessions.models import Session
from django.contrib import messages, auth
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import FileResponse
import shutil
import threading
from asgiref.sync import async_to_sync
from django_q.tasks import async_task
import time
import datetime
import subprocess
import os
import pandas as pd
import codecs
import numpy as np
import matplotlib.pyplot as plt

#restore reference and user data
storage_dir = f"/data/work1782/evan"
#web data
main_dir = f"/home/evan/ch08www"

#core number
SHAPEIT_core = 20
IMPUTE2_core = 8

#first means each chunks use how many core number, second means how many chunks can run per time
IMPUTE5_core = 2
IMPUTE5_core_write = 8

Beagle5_core = 1
Beagle5_core_write = 5

#---function---


#confirm the interger
def is_number(s):
    try:  
        s = float(s)
        if s%1 != 0:
            return False
        else:
            return True
    except ValueError:  # ValueError 傳入無效參數
        pass  
    try:
        import unicodedata 
        for i in s:
            unicodedata.numeric(i)  # 
            #return True
        return True
    except (TypeError, ValueError):
        pass
    return False

#confirm float
def is_float(s):
    try:  
        s = float(s)
        if s > 1:
            return False
        else:
            return True
    except ValueError:  # ValueError 傳入無效參數
        pass  
    try:
        import unicodedata 
        for i in s:
            unicodedata.numeric(i)  # 
            #return True
        return True
    except (TypeError, ValueError):
        pass
    return False


# Create your views here.
# Webpage

#homepage
def index(request, pid=None, del_pass=None):
    if 'username' in request.session:
        username = request.session['username']
    messages.get_messages(request)
    return render(request, 'index.html', locals())
    
#tutorial
def tutorial(request):
    if 'username' in request.session:
        username = request.session['username']
    messages.get_messages(request)
    return render(request, 'tutorial.html', locals())


#original register and login,no use now---------------------------------------------------------------------------------------------------
#register page orgin 
def register(request, pid=None, del_pass=None):
    if request.method =='POST':
        register_form = forms.Registerform(request.POST)
        if register_form.is_valid():
            new_user = register_form.save()
            new_user.set_password(new_user.password)
            new_user.save()
           # authenticated_user = authenticate(username=new_user.username,password=request.POST['password2'])
            auth.login(request, new_user)
            messages.add_message(request, messages.SUCCESS,'Registration complete')
            return HttpResponseRedirect('/')
        else:
            messages.add_message(request, messages.INFO, 'Please check the column content')
    else:
        register_form = forms.Registerform()
    return render(request, 'register.html', locals())
    

#login page_ orgin 
def login(request):
    if request.method =='POST':
        login_form = forms.Loginform(request.POST)
        if login_form.is_valid():
            login_name = request.POST['username'].strip()
            login_password = request.POST['password']
            user = authenticate(username=login_name, password=login_password)
            if user is not None:
                if user.is_active:
                    auth.login(request, user)
                    messages.add_message(request, messages.SUCCESS,'Log in successful')
                    return HttpResponseRedirect('/')
                else:
                    messages.add_message(request, messages.WARNING,'Unactive account')
            else:
                messages.add_message(request, messages.WARNING,'Account not found')
        else:
            messages.add_message(request, messages.INFO, 'Please check the column content')
    else:
        login_form = forms.Loginform()

    return render(request, 'login.html', locals())

#---------------------------------------------------------------------------------------------------

#logout page
def logout(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
    auth.logout(request)
    messages.add_message(request, messages.INFO, "Clean id successful")
    return HttpResponseRedirect('/')

#email register page, also create user dir here
def email(request):
    if request.method =='POST':
        email_form = forms.user_email(request.POST)
        if email_form.is_valid():
            useremail = request.POST['email'].strip()
            request.session['username'] = useremail
            sample_dir = f"{storage_dir}/sample_dir/{useremail}"
            result_dir = f"{storage_dir}/result_data/{useremail}"
            if not os.path.isdir(sample_dir):
                os.mkdir(sample_dir)
            if not os.path.isdir(result_dir):
                os.mkdir(result_dir)                  
            return HttpResponseRedirect('/')
        else:
            messages.add_message(request, messages.INFO, 'Please check the email content')
    else:
        email_form = forms.user_email()

    return render(request, 'get_email.html', locals())

#Function page----------------------------------------------
#imputation page
def imputation_page(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')

    if request.POST:
        form = forms.impute2_form(request.POST, request.FILES)
        if form.is_valid():
             user_dir = f"{storage_dir}/sample_dir/{username}"
             if not os.path.isdir(user_dir):
                 os.mkdir(user_dir)
             project_name = form.cleaned_data['user_name']
             path2 = f"{storage_dir}/sample_dir/{username}/{project_name}"
             num = 2
             #confirm the folder exist
             while os.path.isdir(path2):
                 path2 = f"{storage_dir}/sample_dir/{username}/{project_name}_{str(num)}"
                 num+=1
                 if num > 50 :
                     print('Create folder error')
                     break
             if not os.path.isdir(path2):
                 os.mkdir(path2)
             if num >2:
                 project_name = f"{project_name}_{str(num-1)}"

             use_url = form.cleaned_data['use_url']
             
             if use_url == True:
                 file_url_vcf = form.cleaned_data['file_url_vcf']
                 file_url_bed = form.cleaned_data['file_url_bed']
                 file_url_bim = form.cleaned_data['file_url_bim']
                 file_url_fam = form.cleaned_data['file_url_fam']
                 #print(file_url_vcf)
                 if file_url_vcf != None:
                     vcf_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_vcf} {path2} vcf.gz",shell=True)
                     vcf_download.communicate()
                     file_format = 'vcf'
                 else:
                     if file_url_bed != None and file_url_bim != None and file_url_fam != None:
                         bed_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bed} {path2} bed",shell=True)
                         bed_download.communicate()
                         bim_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bim} {path2} bim",shell=True)
                         bim_download.communicate()
                         fam_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_fam} {path2} fam",shell=True)
                         fam_download.communicate()
                         file_format = 'plink'
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'imputation.html', locals())   
             elif use_url == False:          
                 #file upload region
                 files = request.FILES.getlist('file_field')
                 if len(files) > 3:
                     messages.add_message(request, messages.INFO, 'Upload file number limit in 1 in VCF foramt, 3 in plink file')
                     return render(request, 'imputation.html', locals())                 
                 plink_format = []
                 for f in files:
                     base= str(f)
                     #get the subname of the file
                     sub0 = base[-6:]
                     sub = base[-3:]
                     if sub0 == 'vcf.gz':
                         file_format = 'vcf'
                         with open(f'{path2}/upload.{sub0}', 'wb+') as destination:
                             for chunk in f.chunks():
                                  destination.write(chunk)
                     elif sub in ['bed','bim','fam']:
                         file_format = 'plink'
                         with open(f'{path2}/upload.{sub}', 'wb+') as destination:
                             for chunk in f.chunks():
                                 destination.write(chunk)
                         plink_format.append(sub)
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'imputation.html', locals()) 
                 if file_format =='plink':
                     if sorted(plink_format)== sorted(['bed','bim','fam']):
                         print('OK')
                     else:
                         messages.add_message(request, messages.INFO, 'Plink format need .bed .bim .fam files')
                         return render(request, 'imputation.html', locals())
             
             user_chromosome = form.cleaned_data['user_chromosome']
             user_entirechr = form.cleaned_data['user_entirechr']
             user_position1 = form.cleaned_data['user_position1']
             user_position2 = form.cleaned_data['user_position2']
             user_mafoption = form.cleaned_data['user_mafoption']
             user_genooption = form.cleaned_data['user_genooption']
             user_mindoption = form.cleaned_data['user_mindoption']
             user_hwe = form.cleaned_data['user_hwe']
             user_group = form.cleaned_data['user_group']
             user_group2 = form.cleaned_data['user_group2']
             user_group3 = form.cleaned_data['user_group3']
             
             total_group = ['EUR','SAS','EAS','AMR','AFR','1000G_phase3_total']
             if user_group in total_group:
                 check1 = '1000G'
             else:
                 check1 = user_group
                 
             if check1 == user_group2:
                 messages.add_message(request, messages.INFO, "Two reference need to be different group")
             if check1 == user_group3:
                 messages.add_message(request, messages.INFO, "Two reference need to be different group")
             if user_group2 != 'None' and user_group3 != 'None':
                 messages.add_message(request, messages.INFO, "You must select only one merge reference function")
                 return render(request, 'imputation.html', locals())             
             if user_entirechr == False:
                 if user_position1 == '' or user_position2 =='':
                     message = 'Please check the column of chromosome position'
                     messages.add_message(request, messages.WARNING, message)
                     return HttpResponseRedirect('/imputation/')
                 elif is_number(user_position1) == False or is_number(user_position2) ==False:
                     message = 'Please check the column of chromosome position'
                     messages.add_message(request, messages.WARNING, message)
                     return HttpResponseRedirect('/imputation/')
             if user_hwe != None:
                 if is_float(user_hwe) ==False:
                     message = 'Please check the column of hwe is float'
                     messages.add_message(request, messages.WARNING, message)
                     return HttpResponseRedirect('/imputation/')
             elif user_hwe == None:
                 user_hwe = ''
            
             if user_group == 'Custom' or user_group2 == 'Custom' or user_group3 == 'Custom':
                 files2 = request.FILES.getlist('file_field2')
                 cusref_dir = f'{path2}/cusref_dir'
                 if not os.path.isdir(cusref_dir):
                     os.mkdir(cusref_dir)
                 ref_list = []
                 for f2 in files2:
                     base= str(f2)
                     #get the subname of the file .sample .hap.gz .legend.gz .txt
                     sub0 = base[-6:] #sample
                     sub = base[-6:] #hap.gz
                     sub1 = base[-9:] #legend.gz
                     sub2 = base[-3:] #txt
                     if sub0 == 'sample':
                         with open(f'{cusref_dir}/uploadref.{sub0}', 'wb+') as destination:
                             for chunk in f2.chunks():
                                 destination.write(chunk)
                         ref_list.append(sub0)
                     elif sub == 'hap.gz':
                         with open(f'{cusref_dir}/uploadref.{sub}', 'wb+') as destination:
                             for chunk in f2.chunks():
                                 destination.write(chunk)
                         ref_list.append(sub)
                     elif sub1 == 'legend.gz':
                         with open(f'{cusref_dir}/uploadref.{sub1}', 'wb+') as destination:
                             for chunk in f2.chunks():
                                 destination.write(chunk)
                         ref_list.append(sub1)
                     elif sub2 == 'txt':
                         with open(f'{cusref_dir}/uploadref.{sub2}', 'wb+') as destination:
                             for chunk in f2.chunks():
                                 destination.write(chunk)
                         ref_list.append(sub2)
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of ref file (.sample .legend.gz .hap.gz .txt)')
                         return render(request, 'imputation.html', locals()) 
                 if sorted(ref_list)== sorted(['sample','hap.gz','legend.gz','txt']):                  
                     print('OK')
                 else:
                     messages.add_message(request, messages.INFO, 'reference format need .sample .legend.gz .hap.gz .txt files')
                     return render(request, 'imputation.html', locals())
            
              
#session ------------------------------------------------------
             request.session['select_function'] = 'imputation'
             request.session['project_name'] = project_name
             request.session['file_format'] = file_format
             request.session['user_chromosome'] = user_chromosome
             request.session['user_entirechr'] = user_entirechr
             request.session['user_position1'] = user_position1
             request.session['user_position2'] = user_position2
             request.session['user_mafoption'] = user_mafoption
             request.session['user_genooption'] = user_genooption
             request.session['user_mindoption'] = user_mindoption
             request.session['user_hwe'] = user_hwe
             request.session['user_group'] = user_group
             request.session['user_group2'] = user_group2
             request.session['user_group3'] = user_group3
             
             return HttpResponseRedirect('/submit_page/')
             

            
        else:
             message = "Please check the data"
    else:
        form = forms.impute2_form()
    return render(request, 'imputation.html', locals())
#-------------------------------------------------------------------------------------

#IMPUTE5 page
def imputation_impute5(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')

    if request.POST:
        form = forms.impute5_form(request.POST, request.FILES)
        if form.is_valid():
             user_dir = f"{storage_dir}/sample_dir/{username}"
             if not os.path.isdir(user_dir):
                 os.mkdir(user_dir)
             project_name = form.cleaned_data['user_name']
             path2 = f"{storage_dir}/sample_dir/{username}/{project_name}"
             num = 2
             #confirm the folder exist
             while os.path.isdir(path2):
                 path2 = f"{storage_dir}/sample_dir/{username}/{project_name}_{str(num)}"
                 num+=1
                 if num > 50 :
                     print('Create folder error')
                     break
             if not os.path.isdir(path2):
                 os.mkdir(path2)
             if num >2:
                 project_name = f"{project_name}_{str(num-1)}"
             use_url = form.cleaned_data['use_url']
             
             if use_url == True:
                 file_url_vcf = form.cleaned_data['file_url_vcf']
                 file_url_bed = form.cleaned_data['file_url_bed']
                 file_url_bim = form.cleaned_data['file_url_bim']
                 file_url_fam = form.cleaned_data['file_url_fam']
                 #print(file_url_vcf)
                 if file_url_vcf != None:
                     vcf_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_vcf} {path2} vcf.gz",shell=True)
                     vcf_download.communicate()
                     file_format = 'vcf'
                 else:
                     if file_url_bed != None and file_url_bim != None and file_url_fam != None:
                         bed_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bed} {path2} bed",shell=True)
                         bed_download.communicate()
                         bim_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bim} {path2} bim",shell=True)
                         bim_download.communicate()
                         fam_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_fam} {path2} fam",shell=True)
                         fam_download.communicate()
                         file_format = 'plink'
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'imputation_impute5.html', locals())   
             elif use_url == False:          
                 #file upload region
                 files = request.FILES.getlist('file_field')
                 if len(files) > 3:
                     messages.add_message(request, messages.INFO, 'Upload file number limit in 1 in VCF foramt, 3 in plink file')
                     return render(request, 'imputation_impute5.html', locals())                 
                 plink_format = []
                 for f in files:
                     base= str(f)
                     #get the subname of the file
                     sub0 = base[-6:]
                     sub = base[-3:]
                     if sub0 == 'vcf.gz':
                         file_format = 'vcf'
                         with open(f'{path2}/upload.{sub0}', 'wb+') as destination:
                             for chunk in f.chunks():
                                  destination.write(chunk)
                     elif sub in ['bed','bim','fam']:
                         file_format = 'plink'
                         with open(f'{path2}/upload.{sub}', 'wb+') as destination:
                             for chunk in f.chunks():
                                 destination.write(chunk)
                         plink_format.append(sub)
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'imputation.html', locals()) 
                 if file_format =='plink':
                     if sorted(plink_format)== sorted(['bed','bim','fam']):
                         print('OK')
                     else:
                         messages.add_message(request, messages.INFO, 'Plink format need .bed .bim .fam files')
                         return render(request, 'imputation_impute5.html', locals())
             
             user_chromosome = form.cleaned_data['user_chromosome']
             user_mafoption = form.cleaned_data['user_mafoption']
             user_genooption = form.cleaned_data['user_genooption']
             user_mindoption = form.cleaned_data['user_mindoption']
             user_hwe = form.cleaned_data['user_hwe']
             user_group = form.cleaned_data['user_group']
             
             total_group = ['EUR','SAS','EAS','AMR','AFR','1000G_phase3_total']
             if user_group in total_group:
                 check1 = '1000G'
             else:
                 check1 = user_group
                 
             if user_hwe != None:
                 if is_float(user_hwe) ==False:
                     message = 'Please check the column of hwe is float'
                     messages.add_message(request, messages.WARNING, message)
                     return HttpResponseRedirect('/imputation_impute5/')
             elif user_hwe == None:
                 user_hwe = ''
            
             if user_group == 'Custom':
                 files2 = request.FILES.getlist('file_field2')
                 cusref_dir = f'{path2}/cusref_dir'
                 if not os.path.isdir(cusref_dir):
                     os.mkdir(cusref_dir)
                 ref_list = []
                 for f2 in files2:
                     base= str(f2)
                     #get the subname of the file .sample .hap.gz .legend.gz .txt
                     sub0 = base[-6:] #vcf.gz
                     if sub0 == 'vcf.gz':
                         with open(f'{cusref_dir}/uploadref.{sub0}', 'wb+') as destination:
                             for chunk in f2.chunks():
                                 destination.write(chunk)
                         ref_list.append(sub0)
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of ref file (.sample .legend.gz .hap.gz .txt)')
                         return render(request, 'imputation_impute5.html', locals()) 
                 if sorted(ref_list)== sorted(['vcf.gz']):                  
                     print('OK')
                 else:
                     messages.add_message(request, messages.INFO, 'reference format need phased .vcf.gz files')
                     return render(request, 'imputation_impute5.html', locals())
            
              
#session 測試------------------------------------------------------
             request.session['select_function'] = 'imputation_impute5'
             request.session['project_name'] = project_name
             request.session['file_format'] = file_format
             request.session['user_chromosome'] = user_chromosome
             request.session['user_mafoption'] = user_mafoption
             request.session['user_genooption'] = user_genooption
             request.session['user_mindoption'] = user_mindoption
             request.session['user_hwe'] = user_hwe
             request.session['user_group'] = user_group
             
             return HttpResponseRedirect('/submit_page/')
             

            
        else:
             message = "請確認是否有輸入資料"
    else:
        form = forms.impute5_form()
    return render(request, 'imputation_impute5.html', locals())

#bealge5 page
def imputation_beagle5(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')

    if request.POST:
        form = forms.beagle5_form(request.POST, request.FILES)
        if form.is_valid():
             user_dir = f"{storage_dir}/sample_dir/{username}"
             if not os.path.isdir(user_dir):
                 os.mkdir(user_dir)
             project_name = form.cleaned_data['user_name']
             path2 = f"{storage_dir}/sample_dir/{username}/{project_name}"
             num = 2
             #confirm the folder exist
             while os.path.isdir(path2):
                 path2 = f"{storage_dir}/sample_dir/{username}/{project_name}_{str(num)}"
                 num+=1
                 if num > 50 :
                     print('Create folder error')
                     break
             if not os.path.isdir(path2):
                 os.mkdir(path2)
             if num >2:
                 project_name = f"{project_name}_{str(num-1)}"
             use_url = form.cleaned_data['use_url']
             
             if use_url == True:
                 file_url_vcf = form.cleaned_data['file_url_vcf']
                 file_url_bed = form.cleaned_data['file_url_bed']
                 file_url_bim = form.cleaned_data['file_url_bim']
                 file_url_fam = form.cleaned_data['file_url_fam']
                 #print(file_url_vcf)
                 if file_url_vcf != None:
                     vcf_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_vcf} {path2} vcf.gz",shell=True)
                     vcf_download.communicate()
                     file_format = 'vcf'
                 else:
                     if file_url_bed != None and file_url_bim != None and file_url_fam != None:
                         bed_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bed} {path2} bed",shell=True)
                         bed_download.communicate()
                         bim_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bim} {path2} bim",shell=True)
                         bim_download.communicate()
                         fam_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_fam} {path2} fam",shell=True)
                         fam_download.communicate()
                         file_format = 'plink'
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'imputation_beagle5.html', locals())   
             elif use_url == False:          
                 #file upload region
                 files = request.FILES.getlist('file_field')
                 if len(files) > 3:
                     messages.add_message(request, messages.INFO, 'Upload file number limit in 1 in VCF foramt, 3 in plink file')
                     return render(request, 'imputation_beagle5.html', locals())                 
                 plink_format = []
                 for f in files:
                     base= str(f)
                     #get the subname of the file
                     sub0 = base[-6:]
                     sub = base[-3:]
                     if sub0 == 'vcf.gz':
                         file_format = 'vcf'
                         with open(f'{path2}/upload.{sub0}', 'wb+') as destination:
                             for chunk in f.chunks():
                                  destination.write(chunk)
                     elif sub in ['bed','bim','fam']:
                         file_format = 'plink'
                         with open(f'{path2}/upload.{sub}', 'wb+') as destination:
                             for chunk in f.chunks():
                                 destination.write(chunk)
                         plink_format.append(sub)
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'imputation.html', locals()) 
                 if file_format =='plink':
                     if sorted(plink_format)== sorted(['bed','bim','fam']):
                         print('OK')
                     else:
                         messages.add_message(request, messages.INFO, 'Plink format need .bed .bim .fam files')
                         return render(request, 'imputation_impute5.html', locals())
             
             user_chromosome = form.cleaned_data['user_chromosome']
             user_mafoption = form.cleaned_data['user_mafoption']
             user_genooption = form.cleaned_data['user_genooption']
             user_mindoption = form.cleaned_data['user_mindoption']
             user_hwe = form.cleaned_data['user_hwe']
             user_group = form.cleaned_data['user_group']
             
             total_group = ['EUR','SAS','EAS','AMR','AFR','1000G_phase3_total']
             if user_group in total_group:
                 check1 = '1000G'
             else:
                 check1 = user_group
                 
             if user_hwe != None:
                 if is_float(user_hwe) ==False:
                     message = 'Please check the column of hwe is float'
                     messages.add_message(request, messages.WARNING, message)
                     return HttpResponseRedirect('/imputation_beagle5/')
             elif user_hwe == None:
                 user_hwe = ''
            
             if user_group == 'Custom':
                 files2 = request.FILES.getlist('file_field2')
                 cusref_dir = f'{path2}/cusref_dir'
                 if not os.path.isdir(cusref_dir):
                     os.mkdir(cusref_dir)
                 ref_list = []
                 for f2 in files2:
                     base= str(f2)
                     #get the subname of the file .sample .hap.gz .legend.gz .txt
                     sub0 = base[-6:] #vcf.gz
                     if sub0 == 'vcf.gz':
                         with open(f'{cusref_dir}/uploadref.{sub0}', 'wb+') as destination:
                             for chunk in f2.chunks():
                                 destination.write(chunk)
                         ref_list.append(sub0)
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of ref file (.sample .legend.gz .hap.gz .txt)')
                         return render(request, 'imputation_beagle5.html', locals()) 
                 if sorted(ref_list)== sorted(['vcf.gz']):                  
                     print('OK')
                 else:
                     messages.add_message(request, messages.INFO, 'reference format need phased .vcf.gz files')
                     return render(request, 'imputation_beagle5.html', locals())
            
              
#session 測試------------------------------------------------------
             request.session['select_function'] = 'imputation_beagle5'
             request.session['project_name'] = project_name
             request.session['file_format'] = file_format
             request.session['user_chromosome'] = user_chromosome
             request.session['user_mafoption'] = user_mafoption
             request.session['user_genooption'] = user_genooption
             request.session['user_mindoption'] = user_mindoption
             request.session['user_hwe'] = user_hwe
             request.session['user_group'] = user_group
             
             return HttpResponseRedirect('/submit_page/')
             

            
        else:
             message = "請確認是否有輸入資料"
    else:
        form = forms.impute5_form()
    return render(request, 'imputation_beagle5.html', locals())

def reference_page(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    if request.POST:
        form = forms.Makeref(request.POST, request.FILES)
        if form.is_valid():
             message = "get data"
             #表單資料
             project_name = form.cleaned_data['user_name']
             path2 = f"{storage_dir}/sample_dir/{username}/{project_name}"
             num = 2
             while os.path.isdir(path2):
                 path2 = f"{storage_dir}/sample_dir/{username}/{project_name}_{str(num)}"
                 num+=1
                 if num > 50 :
                     print('error')
                     break
             if not os.path.isdir(path2):
                 os.mkdir(path2)
             if num >2:
                 project_name = f"{project_name}_{str(num-1)}"
             
             use_url = form.cleaned_data['use_url']
             
             if use_url == True:
                 file_url_vcf = form.cleaned_data['file_url_vcf']
                 file_url_bed = form.cleaned_data['file_url_bed']
                 file_url_bim = form.cleaned_data['file_url_bim']
                 file_url_fam = form.cleaned_data['file_url_fam']
                 #print(file_url_vcf)
                 if file_url_vcf != None:
                     vcf_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_vcf} {path2} vcf.gz",shell=True)
                     vcf_download.communicate()
                     file_format = 'vcf'
                 else:
                     if file_url_bed != None and file_url_bim != None and file_url_fam != None:
                         bed_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bed} {path2} bed",shell=True)
                         bed_download.communicate()
                         bim_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bim} {path2} bim",shell=True)
                         bim_download.communicate()
                         fam_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_fam} {path2} fam",shell=True)
                         fam_download.communicate()
                         file_format = 'plink'
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'reference.html', locals())   
             elif use_url == False:          

                 files = request.FILES.getlist('file_field')
                 plink_format = []
                 for f in files:
                     base= str(f)
                     #print(base)
                     sub0 = base[-6:]
                     sub = base[-3:]
                     if sub0 == 'vcf.gz':
                         file_format = 'vcf'
                         with open(f'{path2}/upload.{sub0}', 'wb+') as destination:
                             for chunk in f.chunks():
                                  destination.write(chunk)
                     elif sub in ['bed','bim','fam']:
                         file_format = 'plink'
                         with open(f'{path2}/upload.{sub}', 'wb+') as destination:
                             for chunk in f.chunks():
                                 destination.write(chunk)
                         plink_format.append(sub)
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'reference.html', locals()) 
                 if file_format =='plink':
                     if sorted(plink_format)== sorted(['bed','bim','fam']):
                         print('OK')
                     else:
                         messages.add_message(request, messages.INFO, 'Plink format need .bed .bim .fam files')
                         return render(request, 'reference.html', locals())

             
             user_chromosome = form.cleaned_data['user_chromosome']
             
             #放入session
             request.session['select_function'] = 'reference'
             request.session['project_name'] = project_name
             request.session['file_format'] = file_format
             request.session['user_chromosome'] = user_chromosome
             
             return HttpResponseRedirect('/submit_page/')

            
        else:
             message = "Please check the data"
    else:
        form = forms.Makeref()
    return render(request, 'reference.html', locals())
    
#split--------------------------------------------------------------------------

def split_chr(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')

    if request.POST:
        form = forms.Split(request.POST, request.FILES)
        if form.is_valid():
             #message = "get data"
             #表單資料
             project_name = form.cleaned_data['user_name']
             path2 = f"{storage_dir}/sample_dir/{username}/{project_name}"
             num = 2
             while os.path.isdir(path2):
                 #project_name = project_name+"_"+str(num)
                 path2 = path2 = f"{storage_dir}/sample_dir/{username}/{project_name}_{str(num)}"
                 num+=1
                 if num > 50 :
                     print('error')
                     break
             if not os.path.isdir(path2):
                 os.mkdir(path2)
             if num >2:
                 project_name = f"{project_name}_{str(num-1)}"
             data_name = form.cleaned_data['data_name']
             use_url = form.cleaned_data['use_url']
             
             if use_url == True:
                 file_url_vcf = form.cleaned_data['file_url_vcf']
                 file_url_bed = form.cleaned_data['file_url_bed']
                 file_url_bim = form.cleaned_data['file_url_bim']
                 file_url_fam = form.cleaned_data['file_url_fam']
                 #print(file_url_vcf)
                 if file_url_vcf != None:
                     vcf_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_vcf} {path2} vcf.gz",shell=True)
                     vcf_download.communicate()
                     file_format = 'vcf'
                 else:
                     if file_url_bed != None and file_url_bim != None and file_url_fam != None:
                         bed_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bed} {path2} bed",shell=True)
                         bed_download.communicate()
                         bim_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bim} {path2} bim",shell=True)
                         bim_download.communicate()
                         fam_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_fam} {path2} fam",shell=True)
                         fam_download.communicate()
                         file_format = 'plink'
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'split_chr.html', locals())   
             elif use_url == False:          

                 files = request.FILES.getlist('file_field')
                 plink_format = []
                 for f in files:
                     base= str(f)
                     #print(base)
                     sub0 = base[-6:]
                     sub = base[-3:]
                     if sub0 == 'vcf.gz':
                         file_format = 'vcf'
                         with open(f'{path2}/upload.{sub0}', 'wb+') as destination:
                             for chunk in f.chunks():
                                  destination.write(chunk)
                     elif sub in ['bed','bim','fam']:
                         file_format = 'plink'
                         with open(f'{path2}/upload.{sub}', 'wb+') as destination:
                             for chunk in f.chunks():
                                 destination.write(chunk)
                         plink_format.append(sub)
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'split_chr.html', locals()) 
                 if file_format =='plink':
                     if sorted(plink_format)== sorted(['bed','bim','fam']):
                         print('OK')
                     else:
                         messages.add_message(request, messages.INFO, 'Plink format need .bed .bim .fam files')
                         return render(request, 'split_chr.html', locals())

             #save to session
             request.session['select_function'] = 'split_chr'
             request.session['project_name'] = project_name
             request.session['data_name'] = data_name
             request.session['file_format'] = file_format                   
              
             return HttpResponseRedirect('/submit_page/')
             

            
        else:
             message = "Please check the data"
    else:
        form = forms.Split()
    return render(request, 'split_chr.html', locals())    
    
#lift-------------------------------------------------------------------

def liftover(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')

    if request.POST:
        form = forms.Liftover(request.POST, request.FILES)
        if form.is_valid():
             project_name = form.cleaned_data['user_name']
             path2 = f"{storage_dir}/sample_dir/{username}/{project_name}"
             num = 2
             while os.path.isdir(path2):
                 path2 = f"{storage_dir}/sample_dir/{username}/{project_name}_{str(num)}"
                 num+=1
                 if num > 50 :
                     print('error')
                     break
             if not os.path.isdir(path2):
                 os.mkdir(path2)
             if num >2:
                 project_name = f"{project_name}_{str(num-1)}"
             data_name = form.cleaned_data['data_name']             
             use_url = form.cleaned_data['use_url']
             
             if use_url == True:
                 file_url_vcf = form.cleaned_data['file_url_vcf']
                 file_url_bed = form.cleaned_data['file_url_bed']
                 file_url_bim = form.cleaned_data['file_url_bim']
                 file_url_fam = form.cleaned_data['file_url_fam']
                 #print(file_url_vcf)
                 if file_url_vcf != None:
                     vcf_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_vcf} {path2} vcf.gz",shell=True)
                     vcf_download.communicate()
                     file_format = 'vcf'
                 else:
                     if file_url_bed != None and file_url_bim != None and file_url_fam != None:
                         bed_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bed} {path2} bed",shell=True)
                         bed_download.communicate()
                         bim_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_bim} {path2} bim",shell=True)
                         bim_download.communicate()
                         fam_download = subprocess.Popen(f"python {main_dir}/code/download_google.py {file_url_fam} {path2} fam",shell=True)
                         fam_download.communicate()
                         file_format = 'plink'
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'liftover.html', locals())   
             elif use_url == False:          
                 files = request.FILES.getlist('file_field')
                 plink_format = []
                 for f in files:
                     base= str(f)
                     #print(base)
                     sub0 = base[-6:]
                     sub = base[-3:]
                     if sub0 == 'vcf.gz':
                         file_format = 'vcf'
                         with open(f'{path2}/upload.{sub0}', 'wb+') as destination:
                             for chunk in f.chunks():
                                  destination.write(chunk)
                     elif sub in ['bed','bim','fam']:
                         file_format = 'plink'
                         with open(f'{path2}/upload.{sub}', 'wb+') as destination:
                             for chunk in f.chunks():
                                 destination.write(chunk)
                         plink_format.append(sub)
                     else:
                         messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                         return render(request, 'liftover.html', locals()) 
                 if file_format =='plink':
                     if sorted(plink_format)== sorted(['bed','bim','fam']):
                         print('OK')
                     else:
                         messages.add_message(request, messages.INFO, 'Plink format need .bed .bim .fam files')
                         return render(request, 'liftover.html', locals())

             
             convert_function = form.cleaned_data['convert_function']
             
             #save to session
             request.session['select_function'] = 'liftover'
             request.session['project_name'] = project_name
             request.session['data_name'] = data_name
             request.session['convert_function'] = convert_function
             request.session['file_format'] = file_format   
             
    #-------------------------------

             return HttpResponseRedirect('/submit_page/')
             

            
        else:
             message = "Please check the data"
    else:
        form = forms.Liftover()
    return render(request, 'liftover.html', locals())    

#NOT open

def qcoption_all(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')

    if request.method == 'POST':
        form = forms.Optiontest(request.POST, request.FILES)
        if form.is_valid():
             message = "已收到資料"
             user_name = form.cleaned_data['user_name']
             #handle_uploaded_bedfile(request.FILES['bedfile'])
             #handle_uploaded_bimfile(request.FILES['bimfile'])
             #handle_uploaded_famfile(request.FILES['famfile'])
             user_mafoption = form.cleaned_data['user_mafoption']
             user_genooption = form.cleaned_data['user_genooption']
             user_mindoption = form.cleaned_data['user_mindoption']
             user_relatedness = form.cleaned_data['user_relatedness']
             user_sexcheck = form.cleaned_data['user_sexcheck']
             user_group = form.cleaned_data['user_group']

             if user_relatedness == True:
                 R = ' --genome --min 0.2'
             else:
                 R = ''
             if user_sexcheck == True:
                 S = ' --check-sex'
             else:
                 S = ''
             if user_mafoption == '不使用':
                 user_mafoption = ''
             else:
                 user_mafoption = user_mafoption
             plink = "./software/plink_dir/plink --bfile ./sample_dir/test"+user_mafoption+user_genooption+user_mindoption+R+S+ " --make-bed --out ./result_data/all_qc"
             os.system(plink)
             word = "Quality control OK"
             shapeit_1 ="./software/shapeit_dir/bin/shapeit -check -B ./result_data/all_qc -M ./ref_dir/genetic_map_chr22_combined_b37.txt --input-ref ./ref_dir/1000GP_Phase3_chr22.hap.gz ./ref_dir/1000GP_Phase3_chr22.legend.gz ./ref_dir/1000GP_Phase3.sample --output-log ./result_data/chr22"
             os.system(shapeit_1)
             shapeit_2 ="./software/shapeit_dir/bin/shapeit -B ./result_data/all_qc -M ./ref_dir/genetic_map_chr22_combined_b37.txt --input-ref ref_dir/1000GP_Phase3_chr22.hap.gz ref_dir/1000GP_Phase3_chr22.legend.gz ref_dir/1000GP_Phase3.sample --exclude-snp ./result_data/chr22.snp.strand.exclude --include-grp group.list -O ./result_data/chr_phased"
             os.system("echo "+user_group+" > group.list")
             os.system(shapeit_2)
             word = word+" Pre-phasing OK "
             impute = "./software/impute2_dir/impute2 -use_prephased_g -known_haps_g ./result_data/chr_phased.haps -h ./ref_dir/1000GP_Phase3_chr22.hap.gz -l ./ref_dir/1000GP_Phase3_chr22.legend.gz -m ./ref_dir/genetic_map_chr22_combined_b37.txt -int 20.4e6 20.5e6 -Ne 20000 -o ./result_data/imputed_data"
             os.system(impute)
             gtool = "./software/gtool_dir/gtool -G --g ./result_data/imputed_data --s ./result_data/chr_phased.sample --ped ./result_data/out.ped --map ./result_data/out.map --phenotype phenotype_1 --threshold 0.9"
             os.system(gtool)
             print("OK")
             return HttpResponseRedirect('/success_page/')

        else:
             message = "請確認是否有輸入資料"
    else:
        form = forms.Optiontest()
    return render(request, 'qc_all.html', locals())
    

def result_page_v2(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    messages.get_messages(request)
    user_dir = f"{storage_dir}/result_data/{username}"
    user_dir2 = f"{storage_dir}/reference/{username}"
    user_dir3 = f"{storage_dir}/split_chr/{username}"
    user_dir4 = f"{storage_dir}/liftover/{username}"
    
    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)
    result = os.listdir(user_dir)
    
    if not os.path.isdir(user_dir2):
        os.mkdir(user_dir2)
    result2 = os.listdir(user_dir2)
    
    if not os.path.isdir(user_dir3):
        os.mkdir(user_dir3)
    result3 = os.listdir(user_dir3)
    
    if not os.path.isdir(user_dir4):
        os.mkdir(user_dir4)
    result4 = os.listdir(user_dir4)
    
    if request.method =='POST':
        if 'imputation' in request.POST:
            message = "Get data"
            user_select = request.POST['imp_selection']
            print(message)
            print(user_select)
            if user_select == "":
                messages.add_message(request, messages.WARNING,'Please check the selection')
                return HttpResponseRedirect('/result_page_v2')
            else:
                request.session['select_project'] = user_select
                request.session['function'] = 'imputation'
                return HttpResponseRedirect('/Download_page_v2')
            
        if 'reference' in request.POST:
            message = "Get data"
            user_select = request.POST['ref_selection']
            print(message)
            print(user_select)                          
            if user_select == "":
                messages.add_message(request, messages.WARNING,'Please check the selection')
                return HttpResponseRedirect('/result_page_v2')
            else:
                request.session['select_project'] = user_select
                request.session['function'] = 'reference'
                return HttpResponseRedirect('/Download_page_v2')
                
        if 'split_chr' in request.POST:
            message = "Get data"
            user_select = request.POST['split_selection']
            print(message)
            print(user_select)                          
            if user_select == "":
                messages.add_message(request, messages.WARNING,'Please check the selection')
                return HttpResponseRedirect('/result_page_v2')
            else:
                request.session['select_project'] = user_select
                request.session['function'] = 'split_chr'
                return HttpResponseRedirect('/Download_page_v2')
                
        if 'liftover' in request.POST:
            message = "Get data"
            user_select = request.POST['liftover_selection']
            print(message)
            print(user_select)                          
            if user_select == "":
                messages.add_message(request, messages.WARNING,'Please check the selection')
                return HttpResponseRedirect('/result_page_v2')
            else:
                request.session['select_project'] = user_select
                request.session['function'] = 'liftover'
                return HttpResponseRedirect('/Download_page_v2')
             
    else:
        print("no data")
        message = "Please check the selection"
    
    return render(request, 'result_page_v2.html', locals())
    
    
#--------------------------------------------------------------------------------
#    function == 'imputation_impute5':

def download_page(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    user_dir = f"{storage_dir}/result_data/{username}"
    
    if 'select_project' in request.session:
        if 'function' in request.session:
            function = request.session['function']
        select_project = request.session['select_project']
        if function == 'imputation':
            user_dir2 = f"{storage_dir}/result_data/{username}/{select_project}"
        else:
            user_dir2 = f"{storage_dir}/{function}/{username}/{select_project}"
        zip_dir = f"{user_dir2}/{select_project}.zip"
        zip_dir2 = f"{user_dir2}/{select_project}_vcf.zip"
        zip_log = f"{user_dir2}/log/sp2.log"
        process_file = f"{user_dir2}/process.txt"
        if os.path.isfile(process_file):
            with open(process_file, "r") as f:
                process = f.readline()
        info_plot = f"{main_dir}/mysite/static/user_plot/{username}/{select_project}/info.png"
        if os.path.isfile(info_plot):
            picture = f"user_plot/{username}/{select_project}/info.png"
        info_plot2 = f"{main_dir}/mysite/static/user_plot/{username}/{select_project}/info2.png"
        if os.path.isfile(info_plot2):
            picture2 = f"user_plot/{username}/{select_project}/info2.png"
        info_plot3 = f"{main_dir}/mysite/static/user_plot/{username}/{select_project}/info3.png"
        if os.path.isfile(info_plot3):
            picture3 = f"user_plot/{username}/{select_project}/info3.png"
        if os.path.isfile(zip_dir):
            zip_file = zip_dir
        if os.path.isfile(zip_dir2):
            zip_file2 = zip_dir2
        if os.path.isfile(zip_log):
            zip_file_log = zip_log
        download1 = 'download1'
    if 'function' in request.session:
        function = request.session['function']
        if function == 'imputation':
            if os.path.isfile(f'{user_dir2}/option.txt'):
                option_list = []
                with open(f'{user_dir2}/option.txt', 'r') as f:
                    for line in f:
                        #print(line)
                        x = line.replace('\n','')
                        if x == '' or x =='No use':
                            x = 'None'
                        option_list.append(x)
                title_list = ['Date','Project name','Chromosome number','Impute the full chromosome','Start position','End position', 'Minor allele frquency option','Single SNP missing rate option','Individual SNP missing rate option','Hardy-Weinberg Equilibrium option','Reference group select']
                d = {}
                for t,c in zip(title_list,option_list):
                    d[t] = c
                Date = d['Date']
                Project_name = d['Project name']
                Chr_num = d['Chromosome number']
                Entire_chr = d['Impute the full chromosome']
                Sta_posi = d['Start position']
                End_posi = d['End position']
                Maf = d['Minor allele frquency option']
                Sin_miss = d['Single SNP missing rate option']
                Indi_miss = d['Individual SNP missing rate option']
                Hardy = d['Hardy-Weinberg Equilibrium option']
                Ref = d['Reference group select']
            elif os.path.isfile(f'{user_dir2}/option_impute5.txt'):
                option_list_impute5 = []
                with open(f'{user_dir2}/option_impute5.txt', 'r') as f:
                    for line in f:
                        #print(line)
                        x = line.replace('\n','')
                        if x == '' or x =='No use':
                            x = 'None'
                        option_list_impute5.append(x)
                title_list = ['Date','Project name','Chromosome number', 'Minor allele frquency option','Single SNP missing rate option','Individual SNP missing rate option','Hardy-Weinberg Equilibrium option','Reference group select']
                d = {}
                for t,c in zip(title_list,option_list_impute5):
                    d[t] = c
                Date = d['Date']
                Project_name = d['Project name']
                Chr_num = d['Chromosome number']
                Maf = d['Minor allele frquency option']
                Sin_miss = d['Single SNP missing rate option']
                Indi_miss = d['Individual SNP missing rate option']
                Hardy = d['Hardy-Weinberg Equilibrium option']
                Ref = d['Reference group select']
                imp5_log = 'imp5_log'

            elif os.path.isfile(f'{user_dir2}/option_beagle5.txt'):
                option_list_beagle5 = []
                with open(f'{user_dir2}/option_beagle5.txt', 'r') as f:
                    for line in f:
                        #print(line)
                        x = line.replace('\n','')
                        if x == '' or x =='No use':
                            x = 'None'
                        option_list_beagle5.append(x)
                title_list = ['Date','Project name','Chromosome number', 'Minor allele frquency option','Single SNP missing rate option','Individual SNP missing rate option','Hardy-Weinberg Equilibrium option','Reference group select']
                d = {}
                for t,c in zip(title_list,option_list_beagle5):
                    d[t] = c
                Date = d['Date']
                Project_name = d['Project name']
                Chr_num = d['Chromosome number']
                Maf = d['Minor allele frquency option']
                Sin_miss = d['Single SNP missing rate option']
                Indi_miss = d['Individual SNP missing rate option']
                Hardy = d['Hardy-Weinberg Equilibrium option']
                Ref = d['Reference group select']
                beagle_log = 'beagle_log'                
        else:
            date_file = f"{user_dir2}/date.txt"
            if os.path.isfile(date_file):
                with open(date_file, "r") as f:
                    Date = f.readline()
            if function == 'reference':
                download2 = 'download2'

    return render(request, 'Download_page.html', locals())

#--------------------------------------------------------------------------------

def handle_uploaded_bedfile(f,username,project_name):
    path2 = "/work1782/evan/sample_dir/"+username+"/"+project_name
    if not os.path.isdir(path2):
        os.mkdir(path2)
    with open(path2+'/upload.bed', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
def handle_uploaded_bimfile(f,username,project_name):
    path2 = "/work1782/evan/sample_dir/"+username+"/"+project_name
    if not os.path.isdir(path2):
        os.mkdir(path2)
    with open(path2+'/upload.bim', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
def handle_uploaded_famfile(f,username,project_name):
    path2 = "/work1782/evan/sample_dir/"+username+"/"+project_name
    if not os.path.isdir(path2):
        os.mkdir(path2)
    with open(path2+'/upload.fam', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
            
def submit_page(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
    return render(request, 'success.html', locals())
    
            
def success_page(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
    #get function
    if 'select_function' in request.session:
        select_function = request.session['select_function']

    if select_function == 'imputation':
    
    #get session    
        if 'project_name' in request.session:
            project_name = request.session['project_name']
        if 'file_format' in request.session:
            file_format = request.session['file_format']
        if 'user_chromosome' in request.session:
            user_chromosome = request.session['user_chromosome']
        if 'user_entirechr' in request.session:
            user_entirechr = request.session['user_entirechr']
        if 'user_position1' in request.session:
            user_position1 = request.session['user_position1']
        if 'user_position2' in request.session:
            user_position2 = request.session['user_position2']
        if 'user_mafoption' in request.session:
            user_mafoption = request.session['user_mafoption']
        if 'user_genooption' in request.session:
            user_genooption = request.session['user_genooption']
        if 'user_mindoption' in request.session:
            user_mindoption = request.session['user_mindoption']
        if 'user_hwe' in request.session:
            user_hwe = request.session['user_hwe']
        if 'user_group' in request.session:
            user_group = request.session['user_group']
        if 'user_group2' in request.session:
            user_group2 = request.session['user_group2']
        if 'user_group3' in request.session:
            user_group3 = request.session['user_group3']
        try:
            print(f"{project_name}--1")
            async_task('mysite.views.submit_impute',username=username,project_name=project_name,file_format=file_format,user_chromosome=user_chromosome,user_entirechr=user_entirechr,user_position1=user_position1,user_position2=user_position2,user_mafoption=user_mafoption,user_genooption=user_genooption,user_mindoption=user_mindoption,user_hwe=user_hwe,user_group=user_group,user_group2=user_group2,user_group3=user_group3)
            time.sleep(5)
            return HttpResponseRedirect('/')
        except FileExistsError:
            return HttpResponseRedirect('/')
    
    elif select_function == 'imputation_impute5':
    
    #get session data    
        if 'project_name' in request.session:
            project_name = request.session['project_name']
        if 'file_format' in request.session:
            file_format = request.session['file_format']
        if 'user_chromosome' in request.session:
            user_chromosome = request.session['user_chromosome']
        if 'user_mafoption' in request.session:
            user_mafoption = request.session['user_mafoption']
        if 'user_genooption' in request.session:
            user_genooption = request.session['user_genooption']
        if 'user_mindoption' in request.session:
            user_mindoption = request.session['user_mindoption']
        if 'user_hwe' in request.session:
            user_hwe = request.session['user_hwe']
        if 'user_group' in request.session:
            user_group = request.session['user_group']
        try:
            async_task('mysite.views.submit_impute5',username=username,project_name=project_name,file_format=file_format,user_chromosome=user_chromosome,user_mafoption=user_mafoption,user_genooption=user_genooption,user_mindoption=user_mindoption,user_hwe=user_hwe,user_group=user_group)
            time.sleep(5)
            return HttpResponseRedirect('/')
        except FileExistsError:
            return HttpResponseRedirect('/')
    elif select_function == 'imputation_beagle5':
    
    #get session data    
        if 'project_name' in request.session:
            project_name = request.session['project_name']
        if 'file_format' in request.session:
            file_format = request.session['file_format']
        if 'user_chromosome' in request.session:
            user_chromosome = request.session['user_chromosome']
        if 'user_mafoption' in request.session:
            user_mafoption = request.session['user_mafoption']
        if 'user_genooption' in request.session:
            user_genooption = request.session['user_genooption']
        if 'user_mindoption' in request.session:
            user_mindoption = request.session['user_mindoption']
        if 'user_hwe' in request.session:
            user_hwe = request.session['user_hwe']
        if 'user_group' in request.session:
            user_group = request.session['user_group']
        try:
            async_task('mysite.views.submit_beagle5',username=username,project_name=project_name,file_format=file_format,user_chromosome=user_chromosome,user_mafoption=user_mafoption,user_genooption=user_genooption,user_mindoption=user_mindoption,user_hwe=user_hwe,user_group=user_group)
            time.sleep(5)
            return HttpResponseRedirect('/')
        except FileExistsError:
            return HttpResponseRedirect('/')
            
    elif select_function == 'reference':
        if 'project_name' in request.session:
            project_name = request.session['project_name']
        if 'file_format' in request.session:
            file_format = request.session['file_format']
        if 'user_chromosome' in request.session:
            user_chromosome = request.session['user_chromosome']
        try:
            submit_reference(username,project_name,file_format,user_chromosome)
        except FileExistsError:
            return HttpResponseRedirect('/')
            
    elif select_function == 'split_chr':
        if 'project_name' in request.session:
            project_name = request.session['project_name']
        if 'data_name' in request.session:
            data_name = request.session['data_name']
        if 'file_format' in request.session:
            file_format = request.session['file_format']
        try:
            submit_split_chr(username,project_name,data_name,file_format)
        except FileExistsError:
            return HttpResponseRedirect('/')
    
    elif select_function == 'liftover':
        if 'project_name' in request.session:
            project_name = request.session['project_name']
        if 'data_name' in request.session:
            data_name = request.session['data_name']
        if 'convert_function' in request.session:
            convert_function = request.session['convert_function']
        if 'file_format' in request.session:
            file_format = request.session['file_format']    
        try:
            submit_liftover(username,project_name,data_name,convert_function,file_format)
        except FileExistsError:
            return HttpResponseRedirect('/') 
            
    
    return HttpResponseRedirect('/')

    return render(request, 'index.html', locals())
#------------------------------------------------------------------------------檔案下載

def file_download(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    if 'select_project' in request.session:
        select_project = request.session['select_project']
    if 'function' in request.session:
        function = request.session['function']
    
    if function == 'imputation':
        download_dir = f"{storage_dir}/result_data"   
    elif function == 'reference':
        download_dir = f"{storage_dir}/reference"
    elif function == 'split_chr':
        download_dir = f"{storage_dir}/split_chr"
    elif function == 'liftover':
        download_dir = f"{storage_dir}/liftover"
    print(select_project)
    #filename= download_dir+str(username)+"/"+str(select_project)+"/"+str(select_project)+".zip"
    filename= f"{download_dir}/{str(username)}/{str(select_project)}/{str(select_project)}.zip"
    file = open((filename),'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']="attachment;filename="+select_project+".zip"
    return response

def file_download_log(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    if 'select_project' in request.session:
        select_project = request.session['select_project']
    if 'function' in request.session:
        function = request.session['function']
    
    if function == 'imputation':
        download_dir = f"{storage_dir}/result_data"
    print(select_project)
    #filename= download_dir+str(username)+"/"+str(select_project)+"/"+str(select_project)+"_impute_log.zip"
    filename= f"{download_dir}/{str(username)}/{str(select_project)}/{str(select_project)}_impute_log.zip"
    file = open((filename),'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']="attachment;filename=impute_log.zip"
    return response
    
def file_download_info(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    if 'select_project' in request.session:
        select_project = request.session['select_project']
    if 'function' in request.session:
        function = request.session['function']
    
    if function == 'imputation':
        download_dir = f"{storage_dir}/result_data"
    print(select_project)
    filename= f"{download_dir}/{str(username)}/{str(select_project)}/imputed_result.info"
    file = open((filename),'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']="attachment;filename=imputed_result.info"
    return response   

def file_download_qc_log(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    if 'select_project' in request.session:
        select_project = request.session['select_project']
    if 'function' in request.session:
        function = request.session['function']    
    if function == 'imputation':
        download_dir = f"{storage_dir}/result_data"
    print(select_project)
    #filename= download_dir+str(username)+"/"+str(select_project)+"/log/all_qc.log"
    filename= f"{download_dir}/{str(username)}/{str(select_project)}/log/all_qc.log"
    file = open((filename),'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']="attachment;filename=qc.log"
    return response   


def file_download_sp1_log(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    if 'select_project' in request.session:
        select_project = request.session['select_project']
    if 'function' in request.session:
        function = request.session['function']    
    if function == 'imputation':
        download_dir = f"{storage_dir}/result_data"
    print(select_project)
    #filename= download_dir+str(username)+"/"+str(select_project)+"/log/sp1.log"
    filename= f"{download_dir}/{str(username)}/{str(select_project)}/log/sp1.log"
    file = open((filename),'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']="attachment;filename=phasing_1.log"
    return response   

def file_download_sp2_log(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    if 'select_project' in request.session:
        select_project = request.session['select_project']
    if 'function' in request.session:
        function = request.session['function']    
    if function == 'imputation':
        download_dir = f"{storage_dir}/result_data"
    print(select_project)
    #filename= download_dir+str(username)+"/"+str(select_project)+"/log/sp2.log"
    filename= f"{download_dir}/{str(username)}/{str(select_project)}/log/sp2.log"
    file = open((filename),'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']="attachment;filename=phasing_2.log"
    return response   

def file_download_sp3_log(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    if 'select_project' in request.session:
        select_project = request.session['select_project']
    if 'function' in request.session:
        function = request.session['function']    
    if function == 'imputation':
        download_dir = f"{storage_dir}/result_data"
    print(select_project)
    #filename= download_dir+str(username)+"/"+str(select_project)+"/log/sp3.log"
    filename= f"{download_dir}/{str(username)}/{str(select_project)}/log/sp3.log"
    file = open((filename),'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']="attachment;filename=phasing_3.log"
    return response   

def file_download_vcf(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    if 'select_project' in request.session:
        select_project = request.session['select_project']
    if 'function' in request.session:
        function = request.session['function']
    
    if function == 'imputation':
        download_dir = f"{storage_dir}/result_data"
    elif function == 'reference':
        download_dir = f"{storage_dir}/reference"
    elif function == 'split_chr':
        download_dir = f"{storage_dir}/split_chr"
    elif function == 'liftover':
        download_dir = f"{storage_dir}/liftover"
    print(select_project)
    #filename= download_dir+str(username)+"/"+str(select_project)+"/"+str(select_project)+"_vcf.zip"
    filename= f"{download_dir}/{str(username)}/{str(select_project)}/{str(select_project)}_vcf.zip"
    file = open((filename),'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']="attachment;filename="+select_project+"_vcf.zip"
    return response     

def impute2(data_path,user_chromosome,ref_hap,ref_legend,ref_map,startpo,endpo,chunk,semlock):
    impute = subprocess.Popen("./software/impute2_dir/impute2 -use_prephased_g -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -strand_g "+data_path+"/log/chr"+user_chromosome+"_s1.snp.strand -h "+ref_hap+" -l "+ref_legend+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+"",shell=True)
    impute.communicate()  
    semlock.release()
    
def impute2_chrx(data_path,user_chromosome,ref_hap,ref_legend,ref_map,startpo,endpo,chunk,semlock):
    impute = subprocess.Popen("./software/impute2_dir/impute2 -use_prephased_g -chrX -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -strand_g "+data_path+"/log/chr"+user_chromosome+"_s1.snp.strand -sample_g "+data_path+"/chr"+user_chromosome+"_phased_sex.sample -h "+ref_hap+" -l "+ref_legend+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+" -phase",shell=True)
    impute.communicate()  
    semlock.release()    

def impute2_merge(data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock):
    impute = subprocess.Popen("./software/impute2_dir/impute2 -merge_ref_panels -use_prephased_g -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -strand_g "+data_path+"/log/chr"+user_chromosome+"_s1.snp.strand -h "+ref_hap+" "+ref_hap2+" -l "+ref_legend+" "+ref_legend2+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+"",shell=True)
    impute.communicate()  
    semlock.release()
    
def impute2_merge_chrx(data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock):
    impute = subprocess.Popen("./software/impute2_dir/impute2 -merge_ref_panels -use_prephased_g -chrX -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -strand_g "+data_path+"/log/chr"+user_chromosome+"_s1.snp.strand -sample_g "+data_path+"/chr"+user_chromosome+"_phased_sex.sample -h "+ref_hap+" "+ref_hap2+" -l "+ref_legend+" "+ref_legend2+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+" -phase",shell=True)
    impute.communicate()  
    semlock.release()    
    
def impute2_two_phased(data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock):
    impute = subprocess.Popen("./software/impute2_dir/impute2 -use_prephased_g -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -strand_g "+data_path+"/log/chr"+user_chromosome+"_s1.snp.strand -h "+ref_hap+" "+ref_hap2+" -l "+ref_legend+" "+ref_legend2+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+"",shell=True)
    impute.communicate()  
    semlock.release()
    
def impute2_two_phased_chrx(data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock):
    impute = subprocess.Popen("./software/impute2_dir/impute2 -use_prephased_g -chrX -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -strand_g "+data_path+"/log/chr"+user_chromosome+"_s1.snp.strand -sample_g "+data_path+"/chr"+user_chromosome+"_phased_sex.sample -h "+ref_hap+" "+ref_hap2+" -l "+ref_legend+" "+ref_legend2+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+" -phase",shell=True)
    impute.communicate()  
    semlock.release()

def impute5(data_path,user_chromosome,ref_vcf,ref_map,chunk,semlock):
    impute5 = subprocess.Popen(f"{main_dir}/software/impute5_v1.1.5/impute5_1.1.5_static --h {ref_vcf} --m {ref_map} --g {data_path}/chr{user_chromosome}_phased.vcf.gz --r {chunk[3]} --buffer-region {chunk[2]} --o {data_path}/vcf_dir/imputed_chr{user_chromosome}_chunk{int(chunk[0])}.vcf.gz --l {data_path}/log/imputed_chr{user_chromosome}_chunk{int(chunk[0])}.log --threads {IMPUTE5_core}",shell=True)
    impute5.communicate()
    semlock.release()
    
def beagle5(data_path,user_chromosome,ref_vcf,ref_map,startpo,endpo,chunk,threads,semlock):
    impute = subprocess.Popen(f"beagle gt={data_path}/chr{user_chromosome}_phased.vcf.gz ref={ref_vcf} map={ref_map} out={data_path}/vcf_dir/imputed_chr{user_chromosome}.chunk{str(chunk)} nthreads={threads} ne=20000 impute=true chrom={user_chromosome}:{startpo}-{endpo}",shell=True)
    impute.communicate()  
    semlock.release()
    
def gen2vcf(data_path,user_chromosome,chunk,semlock2):
    chunk_dir =  data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)
    if os.path.isfile(chunk_dir):
        if user_chromosome[0] == 'X':
            gen2vcf = subprocess.Popen(f"{main_dir}/software/GEN2VCF/src/gen2vcf --gen-file {data_path}/imputed_chr{user_chromosome}.chunk{str(chunk)} --sample-file {data_path}/chr{user_chromosome}_phased.sample --chr {user_chromosome[0]} --out {data_path}/vcf_dir/chr{user_chromosome}_chunk{str(chunk)}.vcf.gz",shell=True)
            gen2vcf.communicate()

        else:
            gen2vcf = subprocess.Popen(f"{main_dir}/software/GEN2VCF/src/gen2vcf --gen-file {data_path}/imputed_chr{user_chromosome}.chunk{str(chunk)} --sample-file {data_path}/chr{user_chromosome}_phased.sample --chr {user_chromosome} --out {data_path}/vcf_dir/chr{user_chromosome}_chunk{str(chunk)}.vcf.gz",shell=True)
            gen2vcf.communicate()
    semlock2.release()
    
    
#no use
def file_download_ref(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    filename= "./sample_dir/"+str(username)+"/"+str(project_name)+"/"+str(project_name)+"_plink.zip"
    file = open((filename),'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']="attachment;filename="+project_name+"_plink.zip"
    return response    

def example_file_download(request):
    try:
        if 'username' in request.session:
            username = request.session['username']
        print(username)
        print(SHAPEIT_core)
    except:
        print('no')
    filename= f"{main_dir}/code/example/example_chr22.zip"
    file = open((filename),'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']="attachment;filename=example_chr22.zip"
    return response    


def del_dir(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')
        
    if 'select_project' in request.session:
        select_project = request.session['select_project']
    if 'function' in request.session:
        function = request.session['function']
    if function == 'imputation':
        download_dir = f"{storage_dir}/result_data"
    elif function == 'reference':
        download_dir = f"{storage_dir}/reference"
    elif function == 'split_chr':
        download_dir = f"{storage_dir}/split_chr"
    elif function == 'liftover':
        download_dir = f"{storage_dir}/liftover"       
    del_dir= f"{download_dir}/{username}/{select_project}"
    del_static = f"{main_dir}/mysite/static/user_plot/{username}/{select_project}"
    try:
        shutil.rmtree(del_dir)
        shutil.rmtree(del_static)
    except OSError as e:
        print(f"Error:{ e.strerror}")
    messages.add_message(request, messages.INFO, f"Delete {select_project} successful")
    return HttpResponseRedirect('/result_page_v2')   

def handle_uploaded_bedfile(f,username,project_name):
    path2 = f"{storage_dir}/sample_dir/{username}/{project_name}"
    if not os.path.isdir(path2):
        os.mkdir(path2)
    with open(path2+'/upload.bed', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

#upload no use
def upload_mult_test(request):
    if 'username' in request.session:
        username = request.session['username']
    else:
        return HttpResponseRedirect('/get_email/')

    if request.POST:
        form = forms.upload_mult_data(request.POST, request.FILES)
        
        files = request.FILES.getlist('file_field')
        if form.is_valid():
             message = "已收到資料"
             plink_format = []
             for f in files:
                 base= str(f)
                 #print(base)
                 sub0 = base[-6:]
                 sub = base[-3:]
                 
                 if sub0 == 'vcf.gz':
                     with open(f'/home/evan/upload_test/upload.{sub}', 'wb+') as destination:
                         for chunk in f.chunks():
                              destination.write(chunk)
                 elif sub in ['bed','bim','fam']:
                         with open(f'/home/evan/upload_test/upload.{sub}', 'wb+') as destination:
                             for chunk in f.chunks():
                                 destination.write(chunk)
                         plink_format.append(sub)
                 else:
                     messages.add_message(request, messages.INFO, 'Please check the format of upload file (vcf.gz or .bed .bim .fam)')
                     return render(request, 'upload.html', locals())
             print(plink_format)
             if sorted(plink_format)== sorted(['bed','bim','fam']):
                 print('OK')
             else:
                 messages.add_message(request, messages.INFO, 'Plink format need .bed .bim .fam files')
                 return render(request, 'upload.html', locals())


             
             return HttpResponseRedirect('/')
             

            
        else:
             message = "請確認是否有輸入資料"
    else:
        form = forms.upload_mult_data()
    return render(request, 'upload.html', locals())
    
def submit_impute(username,project_name,file_format,user_chromosome,user_entirechr,user_position1,user_position2,user_mafoption,user_genooption,user_mindoption,user_hwe,user_group,user_group2,user_group3):
#------------------------------------------------------------------------        
    #create folder
    print(f"{project_name}--2")
    path = f"{storage_dir}/result_data/{username}"
    if not os.path.isdir(path):
        os.mkdir(path)
    data_path = f"{storage_dir}/result_data/{username}/{project_name}"
    os.mkdir(data_path)
    os.mkdir(data_path+"/log")
    os.mkdir(data_path+"/log/impute_log")
    os.mkdir(data_path+"/vcf_dir")
    #vcf_result為merge後的結果
    os.mkdir(data_path+"/vcf_result")
    #zip_file已轉換plink format
    os.mkdir(data_path+"/zip_file")
    #get time
    date1 = datetime.datetime.now()
    date1 = date1.strftime("%Y-%m-%d %H:%M")
    plot_dir = f"{main_dir}/mysite/static/user_plot/{username}"
    if not os.path.isdir(plot_dir):
        os.mkdir(plot_dir)    
    plot_dir2 = plot_dir+"/"+project_name
    if not os.path.isdir(plot_dir2):
        os.mkdir(plot_dir2)
    #store option
    if user_group2 != 'None':
        group_select = f"{user_group} + {user_group2}(merge)"
    elif user_group3 != 'None':
        group_select = f"{user_group} + {user_group3}(imporved)"
    else:
        group_select = user_group
    option_list = [date1,project_name,user_chromosome,user_entirechr,user_position1,user_position2,user_mafoption,user_genooption,user_mindoption,user_hwe,group_select]
    filename = data_path+"/option.txt"
    with open(filename,'w') as f:
        for i in option_list:
            f.write(str(i)+'\n')
    #save_option = open(data_path+"/option.txt",'w')
    #print(option_list,file = save_option)
    #save_option.close()  
    
    #if user_relatedness == True:
    #    R = ' --genome --min 0.2'
    #else:
    #    R = ''
    #if user_sexcheck == True:
    #    S = ' --check-sex'
    #else:
    #    S = ''
    if user_mafoption == 'No use':
        user_mafoption = ''
    else:
        user_mafoption = user_mafoption
    if user_genooption == 'No use':
        user_genooption = ''
    else:
        user_genooption = user_genooption
    if user_mindoption == 'No use':
        user_mindoption = ''
    else:
        user_mindoption = user_mindoption
        
    if user_hwe == '':
        user_hwe = ''
    else:
        user_hwe = float(user_hwe)
        user_hwe = f' --hwe {user_hwe}'
    total_group = ['EUR','SAS','EAS','AMR','AFR','1000G_phase3_total']
    if user_group2 == 'None' and user_group3 == 'None':
        if user_chromosome[0] == 'X':
            if user_group in total_group:
                if user_group == '1000G_phase3_total':
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = ""
                else:
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = "--include-grp "+data_path+"/group.list "
            elif user_group == 'HapMap3':
                ref_map = f"{storage_dir}/ref_dir/hapmap3/genetic_map_chr{user_chromosome[0]}_combined_b36.txt"
                ref_hap = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome[0]}.haps.gz"
                ref_legend = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome[0]}.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_all.sample"
                include = ""
            elif user_group == 'TWB':
                ref_map = f"{storage_dir}/ref_dir/TWB_data/genetic_map_chr{user_chromosome}_combined_b37.txt"
                ref_hap = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_new.hap.gz"
                ref_legend = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_new.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/TWB_data/TWB_ngs.sample"
                include = ""
            elif user_group == 'Custom':
                ref_map = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.txt"
                ref_hap = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.hap.gz"
                ref_legend = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.legend.gz"
                ref_sample = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.sample"
                include = ""         
        else:
            if user_group in total_group:
                if user_group == '1000G_phase3_total':
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = ""
                else:
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = "--include-grp "+data_path+"/group.list "
            elif user_group == 'HapMap3':
                ref_map = f"{storage_dir}/ref_dir/hapmap3/genetic_map_chr{user_chromosome}_combined_b36.txt"
                ref_hap = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome}.haps.gz"
                ref_legend = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome}.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_all.sample"
                include = ""
            elif user_group == 'TWB':
                ref_map = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_map.txt"
                ref_hap = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_new.hap.gz"
                ref_legend = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_new.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/TWB_data/TWB_ngs.sample"
                include = ""
            elif user_group == 'Custom':
                ref_map = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.txt"
                ref_hap = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.hap.gz"
                ref_legend = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.legend.gz"
                ref_sample = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.sample"
                include = "" 
    elif user_group2 != 'None':
        if user_chromosome[0] == 'X':
            if user_group in total_group:
                if user_group == '1000G_phase3_total':
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = ""
                else:
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = "--include-grp "+data_path+"/group.list "
            elif user_group == 'HapMap3':
                ref_map = f"{storage_dir}/ref_dir/hapmap3/genetic_map_chr{user_chromosome[0]}_combined_b36.txt"
                ref_hap = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome[0]}.haps.gz"
                ref_legend = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome[0]}.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_all.sample"
                include = ""
            elif user_group == 'TWB':
                ref_map = f"{storage_dir}/ref_dir/TWB_data/genetic_map_chr{user_chromosome}_combined_b37.txt"
                ref_hap = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_new.hap.gz"
                ref_legend = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_new.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/TWB_data/TWB_ngs.sample"
                include = ""
            elif user_group == 'Custom':
                ref_map = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.txt"
                ref_hap = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.hap.gz"
                ref_legend = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.legend.gz"
                ref_sample = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.sample"
                include = "" 
            if user_group2 == '1000G':
                ref_map2 = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/1000GP_legend/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
            elif user_group2 == 'HapMap3':
                ref_map2 = f"{storage_dir}/ref_dir/hapmap3/genetic_map_chr{user_chromosome[0]}_combined_b36.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome[0]}.haps.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome[0]}.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_all.sample"
            elif user_group2 == 'TWB':
                ref_map2 = f"{storage_dir}/ref_dir/TWB_data/genetic_map_chr{user_chromosome}_combined_b37.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_new.hap.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_new.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/TWB_data/TWB_ngs.sample"
            elif user_group2 == 'Custom':
                ref_map2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.txt"
                ref_hap2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.hap.gz"
                ref_legend2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.legend.gz"
                ref_sample2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.sample"
        else:
        
            if user_group in total_group:
                if user_group == '1000G_phase3_total':
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = ""
                else:
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = "--include-grp "+data_path+"/group.list "
            elif user_group == 'HapMap3':
                ref_map = f"{storage_dir}/ref_dir/hapmap3/genetic_map_chr{user_chromosome}_combined_b36.txt"
                ref_hap = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome}.haps.gz"
                ref_legend = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome}.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_all.sample"
                include = ""
            elif user_group == 'TWB':
                ref_map = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_map.txt"
                ref_hap = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_new.hap.gz"
                ref_legend = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_new.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/TWB_data/TWB_ngs.sample"
                include = ""
            elif user_group == 'Custom':
                ref_map = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.txt"
                ref_hap = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.hap.gz"
                ref_legend = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.legend.gz"
                ref_sample = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.sample"
                include = "" 
            if user_group2 == '1000G':
                ref_map2 = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/1000GP_legend/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
            elif user_group2 == 'HapMap3':
                ref_map2 = f"{storage_dir}/ref_dir/hapmap3/genetic_map_chr{user_chromosome}_combined_b36.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome}.haps.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome}.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_all.sample"
            elif user_group2 == 'TWB':
                ref_map2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_map.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_new.hap.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_new.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/TWB_data/TWB_ngs.sample"
            elif user_group2 == 'Custom':
                ref_map2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.txt"
                ref_hap2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.hap.gz"
                ref_legend2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.legend.gz"
                ref_sample2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.sample"
    elif user_group3 != 'None':
        if user_chromosome[0] == 'X':
            if user_group in total_group:
                if user_group == '1000G_phase3_total':
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"/{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = ""
                else:
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"/{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = "--include-grp "+data_path+"/group.list "
            elif user_group == 'HapMap3':
                ref_map = f"{storage_dir}/ref_dir/hapmap3/genetic_map_chr{user_chromosome[0]}_combined_b36.txt"
                ref_hap = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome[0]}.haps.gz"
                ref_legend = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome[0]}.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_all.sample"
                include = ""
            elif user_group == 'TWB':
                ref_map = f"{storage_dir}/ref_dir/TWB_data/genetic_map_chr{user_chromosome}_combined_b37.txt"
                ref_hap = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_new.hap.gz"
                ref_legend = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_new.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/TWB_data/TWB_ngs.sample"
                include = ""
            elif user_group == 'Custom':
                ref_map = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.txt"
                ref_hap = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.hap.gz"
                ref_legend = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.legend.gz"
                ref_sample = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.sample"
                include = ""         
            if user_group3 == '1000G':
                ref_map2 = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/1000GP_legend/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
            elif user_group3 == 'HapMap3':
                ref_map2 = f"{storage_dir}/ref_dir/hapmap3/genetic_map_chr{user_chromosome[0]}_combined_b36.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome[0]}.haps.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome[0]}.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_all.sample"
            elif user_group3 == 'TWB':
                ref_map2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_map.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_new.hap.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome[0]}_new.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/TWB_data/TWB_ngs.sample"
            elif user_group3 == 'Custom':
                ref_map2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.txt"
                ref_hap2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.hap.gz"
                ref_legend2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.legend.gz"
                ref_sample2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.sample"
        else:        
            if user_group in total_group:
                if user_group =='1000G_phase3_total':
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = ""
                else:
                    ref_map = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                    ref_hap = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                    ref_legend = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                    ref_sample = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
                    include = "--include-grp "+data_path+"/group.list "
            elif user_group == 'HapMap3':
                ref_map = f"{storage_dir}/ref_dir/hapmap3/genetic_map_chr{user_chromosome}_combined_b36.txt"
                ref_hap = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome}.haps.gz"
                ref_legend = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome}.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_all.sample"
                include = ""
            elif user_group == 'TWB':
                ref_map = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_map.txt"
                ref_hap = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_new.hap.gz"
                ref_legend = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_new.legend.gz"
                ref_sample = f"{storage_dir}/ref_dir/TWB_data/TWB_ngs.sample"
                include = ""
            elif user_group == 'Custom':
                ref_map = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.txt"
                ref_hap = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.hap.gz"
                ref_legend = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.legend.gz"
                ref_sample = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.sample"
                include = "" 
            if user_group3 == '1000G':
                ref_map2 = f"{storage_dir}/ref_dir/genetic_map_chr{user_chromosome}_combined_b37.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/1000GP_Phase3_chr{user_chromosome}.hap.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/1000GP_legend/1000GP_Phase3_chr{user_chromosome}.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/1000GP_Phase3.sample"
            elif user_group3 == 'HapMap3':
                ref_map2 = f"{storage_dir}/ref_dir/hapmap3/genetic_map_chr{user_chromosome}_combined_b36.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome}.haps.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_chr{user_chromosome}.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/hapmap3/hapmap3_r2_b36_all.sample"
            elif user_group3 == 'TWB':
                ref_map2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_map.txt"
                ref_hap2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_new.hap.gz"
                ref_legend2 = f"{storage_dir}/ref_dir/TWB_data/chr{user_chromosome}_new.legend.gz"
                ref_sample2 = f"{storage_dir}/ref_dir/TWB_data/TWB_ngs.sample"
            elif user_group3 == 'Custom':
                ref_map2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.txt"
                ref_hap2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.hap.gz"
                ref_legend2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.legend.gz"
                ref_sample2 = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.sample"
                    
#壓縮區----------------------------------------------------------------------------------
    compress1 = f"{main_dir}/software/zip_dir/bin/zip -jr {data_path}/{project_name}_vcf.zip {data_path}/vcf_result/*"
    compress2 = f"{main_dir}/software/zip_dir/bin/zip -jr {data_path}/{project_name}.zip {data_path}/zip_file/*"
    compress3 = f"{main_dir}/software/zip_dir/bin/zip -jr {data_path}/{project_name}_impute_log.zip {data_path}/log/impute_log/*"
#PLINK-----------------------------------------------------------------------------------
    try:
        process = "Quality Control"
            
        with open(data_path+"/process.txt", "w") as f:
            f.write(process)
        if file_format == 'plink':
            plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --make-bed --out {data_path}/all_qc", shell=True)
            plink.communicate()
        elif file_format == 'vcf':
            plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload.vcf.gz{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --make-bed --out {data_path}/all_qc", shell=True)
            plink.communicate()
            fname =f'{data_path}/all_qc.log'

            with open(fname, 'r') as f:  #打開文件
                lines = f.readlines() #讀取所有行
                last_line = lines[-6]
                s1_mess = last_line
                print(s1_mess)
                if "Multiple instances of '_' " in s1_mess:
                    print('retry')
                    plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload.vcf.gz{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --double-id --make-bed --out {data_path}/all_qc", shell=True)
                    plink.communicate()
        word = "Quality control OK"
    except:
        print("plink error")
#SHAPEIT1--------------------------------------------------------------------------------
    try:
        #shapeit core numbers
        #core_num = 20
        process = "Pre-phasing(1/3)"
            
        with open(data_path+"/process.txt", "w") as f:
            f.write(process)
        if user_group == 'ALL':
            include = ""
        group = open(data_path+"/group.list",'w')
        print(user_group,file = group)
        group.close()
        if user_chromosome[0] == 'X':
            shapeit1 = subprocess.Popen(f"{main_dir}/software/shapeit_dir/bin/shapeit -check -B {data_path}/all_qc -M {ref_map} --input-ref {ref_hap} {ref_legend} {ref_sample} {include}-T {SHAPEIT_core} --chrX --output-log {data_path}/log/chr{user_chromosome}_s1",shell=True)
            shapeit1.communicate()
        else:
            shapeit1 = subprocess.Popen(f"{main_dir}/software/shapeit_dir/bin/shapeit -check -B {data_path}/all_qc -M {ref_map} --input-ref {ref_hap} {ref_legend} {ref_sample} {include}-T {SHAPEIT_core} --output-log {data_path}/log/chr{user_chromosome}_s1",shell=True)
            shapeit1.communicate()
        fname = data_path+"/log/chr"+user_chromosome+"_s1.log"
        with open(fname, 'r') as f:  #打開文件
            lines = f.readlines() #讀取所有行
            last_line = lines[-1][0:21] #取最後一行     
            s1_mess = last_line
            print(s1_mess)
            if s1_mess == "ERROR: Duplicate site":
                move_dup = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload --list-duplicate-vars ids-only suppress-first --out {data_path}/dupvar_exclude", shell=True)
                move_dup.communicate()
                move_dup_2 = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload --exclude {data_path}/dupvar_exclude.dupvar --make-bed --snps-only just-acgt --out {storage_dir}/sample_dir/{username}/{project_name}/upload_rmdup", shell=True)
                move_dup_2.communicate()
                plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload_rmdup{user_mafoption}{user_genooption}{user_mindoption} --make-bed --out {data_path}/all_qc", shell=True)
                plink.communicate()
                if user_chromosome[0] == 'X':
                    shapeit1 = subprocess.Popen(f"{main_dir}/software/shapeit_dir/bin/shapeit -check -B {data_path}/all_qc -M {ref_map} --input-ref {ref_hap} {ref_legend} {ref_sample} {include}-T {SHAPEIT_core} --chrX --output-log {data_path}/log/chr{user_chromosome}_s1",shell=True)
                    shapeit1.communicate()
                else:
                    shapeit1 = subprocess.Popen(f"{main_dir}/software/shapeit_dir/bin/shapeit -check -B {data_path}/all_qc -M {ref_map} --input-ref {ref_hap} {ref_legend} {ref_sample} {include}-T {SHAPEIT_core} --output-log {data_path}/log/chr{user_chromosome}_s1",shell=True)
                    shapeit1.communicate()                
    except:
        print("alignment error")
        try:
            fname = data_path+"/log/chr"+user_chromosome+"_s1.log"
            with open(fname, 'r') as f:  #打開文件
                lines = f.readlines() #讀取所有行
                last_line = lines[-1][0:21] #取最後一行     
                s1_mess = last_line
                print(s1_mess,"2")
                if s1_mess == "ERROR: Duplicate site":
                    move_dup = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload --list-duplicate-vars ids-only suppress-first --out {data_path}/dupvar_exclude", shell=True)
                    move_dup.communicate()
                    move_dup_2 = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload --exclude {data_path}/dupvar_exclude.dupvar --snps-only just-acgt --out {storage_dir}/sample_dir/{username}/{project_name}/upload_rmdup", shell=True)
                    move_dup_2.communicate()
                    plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload_rmdup{user_mafoption}{user_genooption}{user_mindoption} --make-bed --out {data_path}/all_qc", shell=True)
                    plink.communicate()
                    if user_chromosome[0] == 'X':
                        shapeit1 = subprocess.Popen(f"{main_dir}/software/shapeit_dir/bin/shapeit -check -B {data_path}/all_qc -M {ref_map} --input-ref {ref_hap} {ref_legend} {ref_sample} {include}-T {SHAPEIT_core} --chrX --output-log {data_path}/log/chr{user_chromosome}_s1",shell=True)
                        shapeit1.communicate()
                    else:
                        shapeit1 = subprocess.Popen(f"{main_dir}/software/shapeit_dir/bin/shapeit -check -B {data_path}/all_qc -M {ref_map} --input-ref {ref_hap} {ref_legend} {ref_sample} {include}-T {SHAPEIT_core} --output-log {data_path}/log/chr{user_chromosome}_s1",shell=True)
                        shapeit1.communicate()   
        except:
            fname = data_path+"/log/chr"+user_chromosome+"_s1.log"
            with open(fname, 'r') as f:  #打開文件
                lines = f.readlines() #讀取所有行
                error_message = []
                for line in lines:
                    if 'ERROR' in line:
                        error_message.append(line)
            print("Shapeit other error")
#SHAPEIT2---------------------------------------------------------------------------------
    try:
        process = "Pre-phasing(2/3)"
            
        with open(data_path+"/process.txt", "w") as f:
            f.write(process)
        if user_chromosome[0] == 'X':
            shapeit2 = subprocess.Popen(f"{main_dir}/software/shapeit_dir/bin/shapeit -check -B {data_path}/all_qc -M {ref_map} --input-ref {ref_hap} {ref_legend} {ref_sample} --exclude-snp {data_path}/log/chr{user_chromosome}_s1.snp.strand.exclude {include}-T {SHAPEIT_core} --chrX --output-log {data_path}/log/chr{user_chromosome}_s2",shell=True)
            shapeit2.communicate()

        else:
            shapeit2 = subprocess.Popen(f"{main_dir}/software/shapeit_dir/bin/shapeit -check -B {data_path}/all_qc -M {ref_map} --input-ref {ref_hap} {ref_legend} {ref_sample} --exclude-snp {data_path}/log/chr{user_chromosome}_s1.snp.strand.exclude {include}-T {SHAPEIT_core} --output-log {data_path}/log/chr{user_chromosome}_s2",shell=True)
            shapeit2.communicate()
        
    except:
        print("strand check error")
#SHAPEIT3--------------------------------------------------------------------------------
    try:
        process = "Pre-phasing(3/3)"
            
        with open(data_path+"/process.txt", "w") as f:
            f.write(process)
        if user_chromosome[0] == 'X':
            shapeit3 = subprocess.Popen(f"{main_dir}/software/shapeit_dir/bin/shapeit -B {data_path}/all_qc -M {ref_map} --input-ref {ref_hap} {ref_legend} {ref_sample} {include}-T {SHAPEIT_core} --chrX --exclude-snp {data_path}/log/chr{user_chromosome}_s1.snp.strand.exclude --output-log {data_path}/log/chr{user_chromosome}_s3 -O {data_path}/chr{user_chromosome}_phased",shell=True)
            shapeit3.communicate()
            create_sample = subprocess.Popen(f"python {main_dir}/code/deal_sample.py {data_path}/chr{user_chromosome}_phased.sample {data_path}/chr{user_chromosome}_phased_sex.sample",shell=True)
            create_sample.communicate()

        else:
            shapeit3 = subprocess.Popen(f"{main_dir}/software/shapeit_dir/bin/shapeit -B {data_path}/all_qc -M {ref_map} --input-ref {ref_hap} {ref_legend} {ref_sample} {include}-T {SHAPEIT_core} --exclude-snp {data_path}/log/chr{user_chromosome}_s1.snp.strand.exclude --output-log {data_path}/log/chr{user_chromosome}_s3 -O {data_path}/chr{user_chromosome}_phased",shell=True)
            shapeit3.communicate()
        word = word+" Pre-phasing OK "
    except:
        print("pre-phasing error")
#IMPUTE2---------------------------------------------------------------------------------
    process = "Imputation"
            
    with open(data_path+"/process.txt", "w") as f:
        f.write(process)
    if user_entirechr == True:
        if user_chromosome[0] == 'X':
            if user_chromosome == 'X_PAR1':
                start = 0
                maxPos = int(2699520)
                numchunk2 = 1
            elif user_chromosome == 'X_nonPAR':
                start = 2699520
                maxPos = int(154931043)
                numchunk2 = 31
            elif user_chromosome == 'X_PAR2':
                start = 154931044
                maxPos = int(155260560)
                numchunk2 = 1
        else:
            with open (ref_map, 'r') as fp:
                lines = fp.readlines()
                last_line = lines[-1]
                maxPos = int(last_line.split()[0])
                numchunk = int(maxPos/5000000)
                numchunk2 = numchunk+1
                fp.close
                start = 0
        #IMPUTE2 core number (depend on RAM usage)

        #maxcpu = 8
        semlock = threading.BoundedSemaphore(IMPUTE2_core)
        threads = []
        
        #normal imputation
        if user_group2 == 'None' and user_group3 == 'None': 
            if user_chromosome[0] == 'X':
                if user_chromosome == 'X_PAR1':
                    for chunk in range(1,numchunk2+1):
                        endpo = maxPos
                        startpo = start + 1
                        semlock.acquire()
                        threads.append(threading.Thread(target = impute2_chrx, args = (data_path,user_chromosome,ref_hap,ref_legend,ref_map,startpo,endpo,chunk,semlock,)))
                        threads[chunk-1].start()
                        start = endpo
                        process = f"Imputation({chunk}/{numchunk2})"
                            
                        with open(data_path+"/process.txt", "w") as f:
                            f.write(process)
                    for chunk in range(1,numchunk2+1):
                        threads[chunk-1].join()
                    print("impute2 done")  
                elif user_chromosome == 'X_nonPAR':
                    for chunk in range(1,numchunk2+1):
                        endpo = start + 5000000
                        startpo = start + 1
                        semlock.acquire()
                        if chunk == numchunk2:
                            endpo = maxPos
                        threads.append(threading.Thread(target = impute2_chrx, args = (data_path,user_chromosome,ref_hap,ref_legend,ref_map,startpo,endpo,chunk,semlock,)))
                        threads[chunk-1].start()
                        start = endpo
                        process = f"Imputation({chunk}/{numchunk2})"
                            
                        with open(data_path+"/process.txt", "w") as f:
                            f.write(process)
                    for chunk in range(1,numchunk2+1):
                        threads[chunk-1].join()
                    print("impute2 done")                      
                elif user_chromosome == 'X_PAR2':
                    for chunk in range(1,numchunk2+1):
                        endpo = maxPos
                        startpo = start + 1
                        semlock.acquire()
                        threads.append(threading.Thread(target = impute2_chrx, args = (data_path,user_chromosome,ref_hap,ref_legend,ref_map,startpo,endpo,chunk,semlock,)))
                        threads[chunk-1].start()
                        start = endpo
                        process = f"Imputation({chunk}/{numchunk2})"
                            
                        with open(data_path+"/process.txt", "w") as f:
                            f.write(process)
                    for chunk in range(1,numchunk2+1):
                        threads[chunk-1].join()
                    print("impute2 done")  
            else:
                for chunk in range(1,numchunk2+1):
                    endpo = start + 5000000
                    startpo = start + 1
                    semlock.acquire()
                    threads.append(threading.Thread(target = impute2, args = (data_path,user_chromosome,ref_hap,ref_legend,ref_map,startpo,endpo,chunk,semlock,)))
                    threads[chunk-1].start()
                    start = endpo
                    process = f"Imputation({chunk}/{numchunk2})"
                        
                    with open(data_path+"/process.txt", "w") as f:
                        f.write(process)
                for chunk in range(1,numchunk2+1):
                    threads[chunk-1].join()
                print("impute2 done")
                
        #merge_imputation
        elif user_group2 != 'None':
            if user_chromosome[0] == 'X':
                if user_chromosome == 'X_PAR1':
                    for chunk in range(1,numchunk2+1):
                        endpo = maxPos
                        startpo = start + 1
                        semlock.acquire()
                        threads.append(threading.Thread(target = impute2_merge_chrx, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                        threads[chunk-1].start()
                        start = endpo
                        process = f"Imputation({chunk}/{numchunk2})"
                            
                        with open(data_path+"/process.txt", "w") as f:
                            f.write(process)
                    for chunk in range(1,numchunk2+1):
                        threads[chunk-1].join()
                    print("impute2 done")
                elif user_chromosome == 'X_nonPAR':
                    for chunk in range(1,numchunk2+1):
                        endpo = start + 5000000
                        startpo = start + 1
                        semlock.acquire()
                        if chunk == numchunk2:
                            endpo = maxPos
                        threads.append(threading.Thread(target = impute2_merge_chrx, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                        threads[chunk-1].start()
                        start = endpo
                        process = f"Imputation({chunk}/{numchunk2})"
                            
                        with open(data_path+"/process.txt", "w") as f:
                            f.write(process)
                    for chunk in range(1,numchunk2+1):
                        threads[chunk-1].join()
                    print("impute2 done")                      
                elif user_chromosome == 'X_PAR2':
                    for chunk in range(1,numchunk2+1):
                        endpo = maxPos
                        startpo = start + 1
                        semlock.acquire()
                        threads.append(threading.Thread(target = impute2_merge_chrx, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                        threads[chunk-1].start()
                        start = endpo
                        process = f"Imputation({chunk}/{numchunk2})"
                            
                        with open(data_path+"/process.txt", "w") as f:
                            f.write(process)
                    for chunk in range(1,numchunk2+1):
                        threads[chunk-1].join()
                    print("impute2 done")  
            else:
                for chunk in range(1,numchunk2+1):
                    endpo = start + 5000000
                    startpo = start + 1
                    semlock.acquire()
                    threads.append(threading.Thread(target = impute2_merge, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                    threads[chunk-1].start()
                    start = endpo
                    process = f"Imputation({chunk}/{numchunk2})"
                        
                    with open(data_path+"/process.txt", "w") as f:
                        f.write(process)
                for chunk in range(1,numchunk2+1):
                    threads[chunk-1].join()
                print("impute2 done")
                
        #improved_imputation -twophased
        elif user_group3 != 'None':
            if user_chromosome[0] == 'X':
                if user_chromosome == 'X_PAR1':
                    for chunk in range(1,numchunk2+1):
                        endpo = maxPos
                        startpo = start + 1
                        semlock.acquire()
                        threads.append(threading.Thread(target = impute2_two_phased_chrx, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                        threads[chunk-1].start()
                        start = endpo
                        process = f"Imputation({chunk}/{numchunk2})"
                            
                        with open(data_path+"/process.txt", "w") as f:
                            f.write(process)
                    for chunk in range(1,numchunk2+1):
                        threads[chunk-1].join()
                    print("impute2 done")
                elif user_chromosome == 'X_nonPAR':
                    for chunk in range(1,numchunk2+1):
                        endpo = start + 5000000
                        startpo = start + 1
                        semlock.acquire()
                        if chunk == numchunk2:
                            endpo = maxPos
                        threads.append(threading.Thread(target = impute2_two_phased_chrx, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                        threads[chunk-1].start()
                        start = endpo
                        process = f"Imputation({chunk}/{numchunk2})"
                            
                        with open(data_path+"/process.txt", "w") as f:
                            f.write(process)
                    for chunk in range(1,numchunk2+1):
                        threads[chunk-1].join()
                    print("impute2 done")                      
                elif user_chromosome == 'X_PAR2':
                    for chunk in range(1,numchunk2+1):
                        endpo = maxPos
                        startpo = start + 1
                        semlock.acquire()
                        threads.append(threading.Thread(target = impute2_two_phased_chrx, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                        threads[chunk-1].start()
                        start = endpo
                        process = f"Imputation({chunk}/{numchunk2})"
                            
                        with open(data_path+"/process.txt", "w") as f:
                            f.write(process)
                    for chunk in range(1,numchunk2+1):
                        threads[chunk-1].join()
                    print("impute2 done")  
            else:
                for chunk in range(1,numchunk2+1):
                    endpo = start + 5000000
                    startpo = start + 1
                    semlock.acquire()
                    threads.append(threading.Thread(target = impute2_two_phased, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                    threads[chunk-1].start()
                    start = endpo
                    process = f"Imputation({chunk}/{numchunk2})"
                        
                    with open(data_path+"/process.txt", "w") as f:
                        f.write(process)
                for chunk in range(1,numchunk2+1):
                    threads[chunk-1].join()
                print("impute2 done")
    #give position
    else:
        maxPos = int(user_position2) - int(user_position1)
        numchunk = int(maxPos/5000000)
        numchunk2 = numchunk+1
        if user_position1 == 0:
            start = int(user_position1)
        else:
            start = int(user_position1) - 1
        #normal imputation
        if user_group2 == 'None':
            if user_chromosome[0] == 'X':
                for chunk in range(1,numchunk2+1):
                    endpo = start + 5000000
                    if endpo > int(user_position2):
                        endpo = int(user_position2)
                    startpo = start + 1
                    semlock.acquire()
                    threads.append(threading.Thread(target = impute2_chrx, args = (data_path,user_chromosome,ref_hap,ref_legend,ref_map,startpo,endpo,chunk,semlock,)))
                    threads[chunk-1].start()
                    #impute = subprocess.Popen("./software/impute2_dir/impute2 -use_prephased_g -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -h "+ref_hap+" -l "+ref_legend+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+"",shell=True)
                    #impute.communicate()
                    start = endpo
                    process = f"Imputation({chunk}/{numchunk2})"
                        
                    with open(data_path+"/process.txt", "w") as f:
                        f.write(process)
                for chunk in range(1,numchunk2+1):
                    threads[chunk-1].join()
                print("impute2 done")

            else:
                for chunk in range(1,numchunk2+1):
                    endpo = start + 5000000
                    if endpo > int(user_position2):
                        endpo = int(user_position2)
                    startpo = start + 1
                    semlock.acquire()
                    threads.append(threading.Thread(target = impute2, args = (data_path,user_chromosome,ref_hap,ref_legend,ref_map,startpo,endpo,chunk,semlock,)))
                    threads[chunk-1].start()
                    #impute = subprocess.Popen("./software/impute2_dir/impute2 -use_prephased_g -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -h "+ref_hap+" -l "+ref_legend+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+"",shell=True)
                    #impute.communicate()
                    start = endpo
                    process = f"Imputation({chunk}/{numchunk2})"
                        
                    with open(data_path+"/process.txt", "w") as f:
                        f.write(process)
                for chunk in range(1,numchunk2+1):
                    threads[chunk-1].join()
                print("impute2 done")
        elif user_group2 != 'None':
            if user_chromosome[0] == 'X':
                for chunk in range(1,numchunk2+1):
                    endpo = start + 5000000
                    if endpo > int(user_position2):
                        endpo = int(user_position2)
                    startpo = start + 1
                    semlock.acquire()
                    threads.append(threading.Thread(target = impute2_merge_chrx, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                    threads[chunk-1].start()
                    #impute = subprocess.Popen("./software/impute2_dir/impute2 -use_prephased_g -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -h "+ref_hap+" -l "+ref_legend+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+"",shell=True)
                    #impute.communicate()
                    start = endpo
                    process = f"Imputation({chunk}/{numchunk2})"
                        
                    with open(data_path+"/process.txt", "w") as f:
                        f.write(process)
                for chunk in range(1,numchunk2+1):
                    threads[chunk-1].join()
                print("impute2 done")
            else:
                for chunk in range(1,numchunk2+1):
                    endpo = start + 5000000
                    if endpo > int(user_position2):
                        endpo = int(user_position2)
                    startpo = start + 1
                    semlock.acquire()
                    threads.append(threading.Thread(target = impute2_merge, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                    threads[chunk-1].start()
                    #impute = subprocess.Popen("./software/impute2_dir/impute2 -use_prephased_g -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -h "+ref_hap+" -l "+ref_legend+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+"",shell=True)
                    #impute.communicate()
                    start = endpo
                    process = f"Imputation({chunk}/{numchunk2})"
                        
                    with open(data_path+"/process.txt", "w") as f:
                        f.write(process)
                for chunk in range(1,numchunk2+1):
                    threads[chunk-1].join()
                print("impute2 done")
        elif user_group3 != 'None':
            if user_chromosome[0] == 'X':
                for chunk in range(1,numchunk2+1):
                    endpo = start + 5000000
                    if endpo > int(user_position2):
                        endpo = int(user_position2)
                    startpo = start + 1
                    semlock.acquire()
                    threads.append(threading.Thread(target = impute2_two_phased_chrx, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                    threads[chunk-1].start()
                    #impute = subprocess.Popen("./software/impute2_dir/impute2 -use_prephased_g -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -h "+ref_hap+" -l "+ref_legend+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+"",shell=True)
                    #impute.communicate()
                    start = endpo
                    process = f"Imputation({chunk}/{numchunk2})"
                        
                    with open(data_path+"/process.txt", "w") as f:
                        f.write(process)
                for chunk in range(1,numchunk2+1):
                    threads[chunk-1].join()
                print("impute2 done")             

            else:
                for chunk in range(1,numchunk2+1):
                    endpo = start + 5000000
                    if endpo > int(user_position2):
                        endpo = int(user_position2)
                    startpo = start + 1
                    semlock.acquire()
                    threads.append(threading.Thread(target = impute2_two_phased, args = (data_path,user_chromosome,ref_hap,ref_hap2,ref_legend,ref_legend2,ref_map,startpo,endpo,chunk,semlock,)))
                    threads[chunk-1].start()
                    #impute = subprocess.Popen("./software/impute2_dir/impute2 -use_prephased_g -known_haps_g "+data_path+"/chr"+user_chromosome+"_phased.haps -h "+ref_hap+" -l "+ref_legend+" -m "+ref_map+" -int "+str(startpo)+" "+str(endpo)+" -Ne 20000 -o "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+"",shell=True)
                    #impute.communicate()
                    start = endpo
                    process = f"Imputation({chunk}/{numchunk2})"
                        
                    with open(data_path+"/process.txt", "w") as f:
                        f.write(process)
                for chunk in range(1,numchunk2+1):
                    threads[chunk-1].join()
                print("impute2 done")             
#Convert to vcf +MERGE-----------------------------------------------------------------------------
    exidir = ""
    process = "Converting format"
            
    with open(data_path+"/process.txt", "w") as f:
        f.write(process)
    maxcpu2 = 20
    semlock2 = threading.BoundedSemaphore(maxcpu2)
    threads2 = []
    
    for chunk in range(1,numchunk2+1):
        chunk_dir =  data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)
        #if os.path.isfile(chunk_dir):
        semlock2.acquire()
        if user_chromosome[0] == 'X':
            threads2.append(threading.Thread(target = gen2vcf, args = (data_path,user_chromosome,chunk,semlock2,)))
            threads2[chunk-1].start()
        else:
            threads2.append(threading.Thread(target = gen2vcf, args = (data_path,user_chromosome,chunk,semlock2,)))
            threads2[chunk-1].start()
            #gen2vcf = subprocess.Popen("./software/GEN2VCF/src/gen2vcf --gen-file "+data_path+"/imputed_chr"+user_chromosome+".chunk"+str(chunk)+" --sample-file "+data_path+"/chr"+user_chromosome+"_phased.sample --chr "+user_chromosome+" --out "+data_path+"/vcf_dir/chr"+user_chromosome+"_chunk"+str(chunk)+".vcf.gz",shell=True)
            #gen2vcf.communicate()
    for chunk in range(1,numchunk2+1):
        threads2[chunk-1].join()
            
    merge = subprocess.Popen(f"{main_dir}/software/bcftools-1.13/bcftools concat {data_path}/vcf_dir/*vcf.gz -Oz -o {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz ",shell=True)
    merge.communicate()
    
    #vcf
    os.system(compress1)
    #vcftoplink

    try:
        vcf2plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz --make-bed --out {data_path}/zip_file/imputed_chr{user_chromosome}", shell=True)
        vcf2plink.communicate()

        fname =f'{data_path}/zip_file/imputed_chr{user_chromosome}.log'
        fname2 =f'{storage_dir}/sample_dir/{username}/{project_name}/upload.fam'

        with open(fname, 'r') as f:  #打開文件
            lines = f.readlines() #讀取所有行
            last_line = lines[-6]
            s1_mess = last_line
            print(s1_mess)
        if file_format == 'plink':        
            with open(fname2, 'r') as f:  #打開文件
                lines = f.readlines() #讀取所有行
            total = []
            for line in lines:
                #print(line)
                split_line= line.split('\t')
                total.append(split_line)
            fam_id = total[0][0].split()[0]
                
        if "Multiple instances of '_' " in s1_mess:
            print('retry')
            vcf2plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz --make-bed --double-id --out {data_path}/zip_file/imputed_chr{user_chromosome}", shell=True)
            vcf2plink.communicate()
        elif '_' in fam_id:
            print('retry')
            vcf2plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz --make-bed --double-id --out {data_path}/zip_file/imputed_chr{user_chromosome}", shell=True)
            vcf2plink.communicate()                

    except:
        print('vcf error')


    #plink
    os.system(compress2)


    #os.system(compress)
    #print("OK")
    date2 = datetime.datetime.now()
    print(date1)
    print(date2)
    process = "Done"
            
    with open(data_path+"/process.txt", "w") as f:
        f.write(process)

    os.system(f"python {main_dir}/code/info_plot.py {data_path} {plot_dir2} {user_chromosome}")
    #os.system(f"cp {data_path}/info.png {plot_dir2}")    
    print("PLOT DONE")
    #刪除殘餘檔案
    try:
        os.system(f"cp {data_path}/*_summary {data_path}/log/impute_log")
        os.system(f"cp {data_path}/*_warnings {data_path}/log/impute_log")
        os.system(f"cp {data_path}/all_qc.log {data_path}/log")
        os.system(f"mv {data_path}/log/chr{user_chromosome}_s1.log {data_path}/log/sp1.log")
        os.system(f"mv {data_path}/log/chr{user_chromosome}_s2.log {data_path}/log/sp2.log")
        os.system(f"mv {data_path}/log/chr{user_chromosome}_s3.log {data_path}/log/sp3.log")
        compress_final = subprocess.Popen(compress3,shell=True)
        compress_final.communicate()
        os.system(f"rm {data_path}/imputed_chr{user_chromosome}.chunk*")
        os.system(f"rm {data_path}/chr{user_chromosome}_phased*")
        os.system(f"rm {data_path}/all_qc*")
        shutil.rmtree(f"{data_path}/vcf_dir")
        os.system(f"rm {storage_dir}/sample_dir/{username}/{project_name}/*")
        print(f"{project_name}--3")
        #shutil.rmtree(f"/work1782/evan/sample_dir/{username}/{project_name}")
    except:
        print('del error')


def submit_reference(username,project_name,file_format,user_chromosome):
    upload_dir = f"{storage_dir}/sample_dir/{username}/{project_name}/reference"
    user_dir = f"{storage_dir}/reference/{username}"
    user_dir2 = f"{user_dir}/{project_name}"
             
    if not os.path.isdir(upload_dir):
        os.mkdir(upload_dir)
    if not os.path.isdir(user_dir2):
        os.mkdir(user_dir2)             #os.mkdir(data_path+"/log")
    date1 = datetime.datetime.now()
    date1 = date1.strftime("%Y-%m-%d %H:%M")
    with open(user_dir2+"/date.txt", "w") as f:
        f.write(date1)                 
               
    process = "converting"

    with open(user_dir2+"/process.txt", "w") as f:
        f.write(process)

    if file_format == 'plink':
        try:
            creat_vcf = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --allow-extra-chr --allow-no-sex --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload --recode vcf --keep-allele-order --out {storage_dir}/sample_dir/{username}/{project_name}/upload", shell=True)
            creat_vcf.communicate()

            fname = f"{storage_dir}/sample_dir/{username}/{project_name}/upload.log"

            with open(fname, 'r') as f:  #打開文件
                lines = f.readlines() #讀取所有行
                last_line = lines[-6]
                s1_mess = last_line
                print(s1_mess)
                if "Multiple instances of '_' " in s1_mess:
                    print('retry')
                    creat_vcf = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --allow-extra-chr --allow-no-sex --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload --recode vcf --keep-allele-order --double-id --out {storage_dir}/sample_dir/{username}/{project_name}/upload", shell=True)
                    creat_vcf.communicate()
        except:
            print('vcf error')
        
    if file_format =='vcf':
        os.system(f"gunzip {storage_dir}/sample_dir/{username}/{project_name}/upload.vcf.gz")
             
    #vcf_reformat = subprocess.Popen(f'python ./code/vcf_format.py /work1782/evan/sample_dir/{username}/{project_name}/upload.vcf /work1782/evan/sample_dir/{username}/{project_name}/upload.vcf')
    #vcf_reformat.communicate()
    os.system(f"python {main_dir}/code/vcf_format.py {storage_dir}/sample_dir/{username}/{project_name}/upload.vcf {storage_dir}/sample_dir/{username}/{project_name}/upload2.vcf")
    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)
    creat_reference = subprocess.Popen(f"perl {main_dir}/code/vcf2impute_legend_haps -vcf {storage_dir}/sample_dir/{username}/{project_name}/upload2.vcf -leghap {upload_dir}/user_ref -chr {user_chromosome} -snps-only",shell=True)
    creat_reference.communicate()
             
    compress = f"{main_dir}/software/zip_dir/bin/zip -jr {user_dir2}/{project_name}.zip {upload_dir}/*"
    os.system(compress)
    #os.system("./software/zip_dir/bin/zip -r ./sample_dir/"+username+"/"+project_name+"/user_ref.zip ./sample_dir/"+username+"/"+project_name+"/user_ref.legend")
    process = "Done"
    with open(user_dir2+"/process.txt", "w") as f:
        f.write(process)
    #刪除殘餘檔案
    try:
        os.system(f"rm {storage_dir}/sample_dir/{username}/{project_name}/*")
        #shutil.rmtree(f"/work1782/evan/sample_dir/{username}/{project_name}")
    except:
        print('del error')
        
def submit_split_chr(username,project_name,data_name,file_format):
    user_dir = f"{storage_dir}/split_chr/{username}"             
    user_dir2 = f"{storage_dir}/split_chr/{username}/{project_name}"        

    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)         
    if not os.path.isdir(user_dir2):
        os.mkdir(user_dir2)
             
    date1 = datetime.datetime.now()
    date1 = date1.strftime("%Y-%m-%d %H:%M")
    with open(user_dir2+"/date.txt", "w") as f:
        f.write(date1)
             
    process = "spliting"

    with open(user_dir2+"/process.txt", "w") as f:
        f.write(process)

    if file_format == 'vcf':
        for chr in range(1,23):
            split_chr = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --allow-extra-chr --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload --chr {str(chr)} --make-bed --out {user_dir2}/{data_name}_chr{str(chr)}",shell=True)
            split_chr.communicate()
        try:
            split_chrx = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --allow-extra-chr --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload --chr x --set-hh-missing --make-bed --out {user_dir2}/{data_name}_chrx",shell=True)
            split_chrx.communicate()
        except:
            print('No chrx')
    elif file_format == 'plink':            
        for chr in range(1,23):
            split_chr = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --allow-extra-chr --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload --chr {str(chr)} --make-bed --out {user_dir2}/{data_name}_chr{str(chr)}",shell=True)
            split_chr.communicate()
        try:
            split_chr = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --allow-extra-chr --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload --chr x --set-hh-missing --make-bed --out {user_dir2}/{data_name}_chrx",shell=True)
            split_chr.communicate()
        except:
            print('No chrx')
    os.system(f"{main_dir}/software/zip_dir/bin/zip -jr {user_dir2}/{project_name}.zip {user_dir2}/*")
             
    user_dir3 = f"{user_dir2}/vcf_result"
             
    if not os.path.isdir(user_dir3):
        os.mkdir(user_dir3)             

    if file_format == 'vcf':
        for chr in range(1,23):
            split_chr = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --allow-extra-chr --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload --chr {str(chr)} --recode vcf bgz --out {user_dir3}/{data_name}_chr{str(chr)}",shell=True)
            split_chr.communicate()
    elif file_format == 'plink':            
        for chr in range(1,23):
            split_chr = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --allow-extra-chr --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload --chr {str(chr)} --recode vcf bgz --out {user_dir3}/{data_name}_chr{str(chr)}",shell=True)
            split_chr.communicate()             
    os.system(f"{main_dir}/software/zip_dir/bin/zip -jr {user_dir2}/{project_name}_vcf.zip {user_dir3}/*")
    process = "Done"
             
    with open(user_dir2+"/process.txt", "w") as f:
        f.write(process)
    #刪除殘餘檔案
    try:
        #shutil.rmtree(f"/work1782/evan/sample_dir/{username}/{project_name}")
        os.system(f"rm {storage_dir}/sample_dir/{username}/{project_name}/*")
        os.system(f"rm {user_dir2}/{data_name}*")
        shutil.rmtree(f"{user_dir3}")
    except:
        print('del error')
        
def submit_liftover(username,project_name,data_name,convert_function,file_format):
    user_dir = f"{storage_dir}/liftover/{username}"             
    user_dir2 = f"{storage_dir}/liftover/{username}/{project_name}"

    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)
               
    if not os.path.isdir(user_dir2):
        os.mkdir(user_dir2)          

    date1 = datetime.datetime.now()
    date1 = date1.strftime("%Y-%m-%d %H:%M")
    with open(user_dir2+"/date.txt", "w") as f:
        f.write(date1)

    process = "Converting"
    with open(user_dir2+"/process.txt", "w") as f:
        f.write(process) 
             
    if file_format == 'vcf':
        convert_to_ped = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload --allow-extra-chr --recode --tab --out {storage_dir}/sample_dir/{username}/{project_name}/upload_2",shell=True)
        convert_to_ped.communicate()        
    elif file_format == 'plink':
        convert_to_ped = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload --allow-extra-chr --recode --tab --out {storage_dir}/sample_dir/{username}/{project_name}/upload_2",shell=True)
        convert_to_ped.communicate()  
    with open(user_dir2+"/process.txt", "w") as f:
        f.write(process)
    #notice that the liftoverplink script use python2
    if convert_function == "To 19":
        liftover = subprocess.Popen(f"{main_dir}/software/liftover_dir/liftOverPlink.py -m {storage_dir}/sample_dir/{username}/{project_name}/upload_2.map -p {storage_dir}/sample_dir/{username}/{project_name}/upload_2.ped -c {main_dir}/software/liftover_dir/hg38ToHg19.over.chain.gz -e {main_dir}/software/liftover_dir/liftOver -o {user_dir2}/{data_name}",shell=True)
        liftover.communicate()
    elif convert_function == "To 38":
        liftover = subprocess.Popen(f"{main_dir}/software/liftover_dir/liftOverPlink.py -m {storage_dir}/sample_dir/{username}/{project_name}/upload_2.map -p {storage_dir}/sample_dir/{username}/{project_name}/upload_2.ped -c {main_dir}/software/liftover_dir/hg19ToHg38.over.chain.gz -e {main_dir}/software/liftover_dir/liftOver -o {user_dir2}/{data_name}",shell=True)
        liftover.communicate()
    elif convert_function == "To 18":
        liftover = subprocess.Popen(f"{main_dir}/software/liftover_dir/liftOverPlink.py -m {storage_dir}/sample_dir/{username}/{project_name}/upload_2.map -p {storage_dir}/sample_dir/{username}/{project_name}/upload_2.ped -c {main_dir}/software/liftover_dir/hg19ToHg18.over.chain.gz -e {main_dir}/software/liftover_dir/liftOver -o {user_dir2}/{data_name}",shell=True)
        liftover.communicate()
    elif convert_function == "18 To 19":
        liftover = subprocess.Popen(f"{main_dir}/software/liftover_dir/liftOverPlink.py -m {storage_dir}/sample_dir/{username}/{project_name}/upload_2.map -p {storage_dir}/sample_dir/{username}/{project_name}/upload_2.ped -c {main_dir}/software/liftover_dir/hg18ToHg19.over.chain.gz -e {main_dir}/software/liftover_dir/liftOver -o {user_dir2}/{data_name}",shell=True)
        liftover.communicate()
    
    user_dir3 = f"{user_dir2}/plink_result"

    if not os.path.isdir(user_dir3):
        os.mkdir(user_dir3)

    ped_2plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --map {user_dir2}/{data_name}.map --ped {user_dir2}/{data_name}.ped --allow-extra-chr --make-bed --out {user_dir3}/{data_name}",shell=True)
    ped_2plink.communicate()

    os.system(f"{main_dir}/software/zip_dir/bin/zip -jr {user_dir2}/{project_name}.zip {user_dir3}/*")

    user_dir4 = f"{user_dir2}/vcf_result"
             
    if not os.path.isdir(user_dir4):
        os.mkdir(user_dir4)
    plink_2vcf = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {user_dir3}/{data_name} --allow-extra-chr --recode vcf bgz --out {user_dir4}/{data_name}",shell=True)
    plink_2vcf.communicate()
             
    os.system(f"{main_dir}/software/zip_dir/bin/zip -jr {user_dir2}/{project_name}_vcf.zip {user_dir4}/*")
    process = "Done"
             
    with open(user_dir2+"/process.txt", "w") as f:
        f.write(process)
    #刪除殘餘檔案
    try:
        #shutil.rmtree(f"/work1782/evan/sample_dir/{username}/{project_name}")
        os.system(f"rm {storage_dir}/sample_dir/{username}/{project_name}/*")
        os.system(f"rm {user_dir2}/{data_name}*")
        shutil.rmtree(f"{user_dir3}")
        shutil.rmtree(f"{user_dir4}")
    except:
        print('del error')
        
def submit_impute5(username,project_name,file_format,user_chromosome,user_mafoption,user_genooption,user_mindoption,user_hwe,user_group):
#------------------------------------------------------------------------        
    #創建資料夾及pathway
    print(f"{project_name}--2")
    path = f"{storage_dir}/result_data/{username}"
    if not os.path.isdir(path):
        os.mkdir(path)
    data_path = f"{storage_dir}/result_data/{username}/{project_name}"
    os.mkdir(data_path)
    os.mkdir(data_path+"/log")
    os.mkdir(data_path+"/log/impute_log")
    os.mkdir(data_path+"/vcf_dir")
    #vcf_result為merge後的結果
    os.mkdir(data_path+"/vcf_result")
    #zip_file已轉換plink format
    os.mkdir(data_path+"/zip_file")
    #獲取時間
    date1 = datetime.datetime.now()
    date1 = date1.strftime("%Y-%m-%d %H:%M")
    plot_dir = f"{main_dir}/mysite/static/user_plot/{username}"
    if not os.path.isdir(plot_dir):
        os.mkdir(plot_dir)    
    plot_dir2 = plot_dir+"/"+project_name
    if not os.path.isdir(plot_dir2):
        os.mkdir(plot_dir2)
    #儲存全部選項

    group_select = user_group
    option_list = [date1,project_name,user_chromosome,user_mafoption,user_genooption,user_mindoption,user_hwe,group_select]
    filename = data_path+"/option_impute5.txt"
    with open(filename,'w') as f:
        for i in option_list:
            f.write(str(i)+'\n')
    #save_option = open(data_path+"/option.txt",'w')
    #print(option_list,file = save_option)
    #save_option.close()  
    
    #if user_relatedness == True:
    #    R = ' --genome --min 0.2'
    #else:
    #    R = ''
    #if user_sexcheck == True:
    #    S = ' --check-sex'
    #else:
    #    S = ''
    if user_mafoption == 'No use':
        user_mafoption = ''
    else:
        user_mafoption = user_mafoption
    if user_genooption == 'No use':
        user_genooption = ''
    else:
        user_genooption = user_genooption
    if user_mindoption == 'No use':
        user_mindoption = ''
    else:
        user_mindoption = user_mindoption
        
    if user_hwe == '':
        user_hwe = ''
    else:
        user_hwe = float(user_hwe)
        user_hwe = f' --hwe {user_hwe}'
    total_group = ['EUR','SAS','EAS','AMR','AFR','1000G_phase3_total']
    if user_group in total_group:
        if user_group == '1000G_phase3_total':
            ref_map = f"{storage_dir}/ref_dir/vcf/gmap/chr{user_chromosome}.b37.gmap.gz"
            ref_vcf = f"{storage_dir}/ref_dir/vcf/ALL.chr{user_chromosome}.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"
        else:
            ref_map = f"{storage_dir}/ref_dir/vcf/gmap/chr{user_chromosome}.b37.gmap.gz"
            ref_vcf = f"{storage_dir}/ref_dir/vcf/{user_group}/chr{user_chromosome}_1kg_{user_group}.vcf.gz"
    elif user_group == 'TWB':
        ref_map = f"{storage_dir}/ref_dir/vcf/gmap/chr{user_chromosome}.b37.gmap.gz"
        ref_vcf = f"{storage_dir}/ref_dir/TWB_data/vcf/chr{user_chromosome}_final.vcf.gz"
    elif user_group == 'Custom':
        ref_map = f"{storage_dir}/ref_dir/vcf/gmap/chr{user_chromosome}.b37.gmap.gz"
        ref_vcf = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.vcf.gz"
                    
#壓縮區----------------------------------------------------------------------------------
    compress1 = f"{main_dir}/software/zip_dir/bin/zip -jr {data_path}/{project_name}_vcf.zip {data_path}/vcf_result/*"
    compress2 = f"{main_dir}/software/zip_dir/bin/zip -jr {data_path}/{project_name}.zip {data_path}/zip_file/*"
    compress3 = f"{main_dir}/software/zip_dir/bin/zip -jr {data_path}/{project_name}_impute_log.zip {data_path}/log/impute_log/*"
    #compress3 = "./software/zip_dir/bin/zip -jr "+data_path+"/"+project_name+"_impute_log.zip "+data_path+"/log/impute_log/*"
#PLINK-----------------------------------------------------------------------------------
    try:
        process = "Quality Control"
            
        with open(data_path+"/process.txt", "w") as f:
            f.write(process)
        if file_format == 'plink':
            plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --recode vcf bgz --out {data_path}/all_qc", shell=True)
            plink.communicate()
        elif file_format == 'vcf':
            plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload.vcf.gz{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --recode vcf bgz --out {data_path}/all_qc", shell=True)
            plink.communicate()
        fname =f'{data_path}/all_qc.log'

        with open(fname, 'r') as f:  #打開文件
            lines = f.readlines() #讀取所有行
        if file_format == 'plink':
            if "Error: Multiple instances of '_' in sample ID.\n" in lines:
                print('retry')
                plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --double-id --recode vcf bgz --out {data_path}/all_qc", shell=True)
                plink.communicate()
            elif 'Warning: Underscore(s) present in sample IDs.\n' in lines:
                print('retry')
                plink = subprocess.Popen(f"{main_dir}/software/plink2_dir/plink2 --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --export vcf bgz id-delim=' ' --out {data_path}/all_qc", shell=True)
                plink.communicate()
        elif file_format == 'vcf':
            if "Error: Multiple instances of '_' in sample ID.\n" in lines:
                print('retry')
                plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload.vcf.gz{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --double-id --recode vcf bgz --out {data_path}/all_qc", shell=True)
                plink.communicate()
            elif 'Warning: Underscore(s) present in sample IDs.\n' in lines:
                print('retry')
                plink = subprocess.Popen(f"{main_dir}/software/plink2_dir/plink2 --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload.vcf.gz{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --export vcf bgz id-delim=' ' --out {data_path}/all_qc", shell=True)
                plink.communicate()        
        word = "Quality control OK"
    except:
        print("plink error")
#SHAPEIT4--------------------------------------------------------------------------------
    try:
        #shapeit core numbers
        #core_num = 20
        process = "Pre-phasing"
            
        with open(data_path+"/process.txt", "w") as f:
            f.write(process)
        qc_index= subprocess.Popen(f"{main_dir}/software/bcftools-1.13/bcftools index {data_path}/all_qc.vcf.gz",shell=True)
        qc_index.communicate()
        shapeit4 = subprocess.Popen(f"shapeit4 --input {data_path}/all_qc.vcf.gz --map {ref_map} --region {user_chromosome} --reference {ref_vcf} --thread {SHAPEIT_core} --log {data_path}/log/chr{user_chromosome}_phased.log --output {data_path}/chr{user_chromosome}_phased.vcf.gz",shell=True)
        shapeit4.communicate()
            
    except:
        print("phasing error")

#IMPUTE5---------------------------------------------------------------------------------
    process = "Chunking"
    
    phase_index= subprocess.Popen(f"{main_dir}/software/bcftools-1.13/bcftools index {data_path}/chr{user_chromosome}_phased.vcf.gz",shell=True)
    phase_index.communicate()
            
    with open(data_path+"/process.txt", "w") as f:
        f.write(process)

        #IMPUTE2 core number (depend on RAM usage)
        #maxcpu = 10
        chunking = subprocess.Popen(f"{main_dir}/software/impute5_v1.1.5/imp5Chunker_1.1.5_static --h {ref_vcf} --g {data_path}/chr{user_chromosome}_phased.vcf.gz --r {user_chromosome} --o {data_path}/coordinates.txt",shell=True)
        chunking.communicate()

    process = "Imputation"
            
    with open(data_path+"/process.txt", "w") as f:
        f.write(process)      

    filename = f'{data_path}/coordinates.txt'
    filelist = f'{data_path}/filelist.txt'
    with open(filename, 'r') as f:  #打開文件
        lines = f.readlines() #讀取所有行
    total = []
    for line in lines:
        #print(line)
        split_line= line.split('\t')
        total.append(split_line)
    semlock = threading.BoundedSemaphore(IMPUTE5_core_write)
    threads = []
    
    for chunk in total:
        print(int(chunk[0]))
        print(f'buffer region {chunk[2]}')
        print(f'impute region {chunk[3]}')
        semlock.acquire()
        threads.append(threading.Thread(target = impute5, args = (data_path,user_chromosome,ref_vcf,ref_map,chunk,semlock)))
        threads[int(chunk[0])].start()
        process = f"Imputation({int(chunk[0])}/{int(total[-1][0])})"                     
        with open(data_path+"/process.txt", "w") as f:
            f.write(process)
        with open(filelist, 'a') as f:  #打開文件
            f.write(f'{data_path}/vcf_dir/imputed_chr{user_chromosome}_chunk{int(chunk[0])}.vcf.gz\n')
    for chunk in total:
        threads[int(chunk[0])].join()
        

        
#MERGE-----------------------------------------------------------------------------
    process = "Converting format"            
    with open(data_path+"/process.txt", "w") as f:
        f.write(process)
    merge = subprocess.Popen(f"{main_dir}/software/bcftools-1.13/bcftools concat -f {filelist} -Oz -o {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz ",shell=True)
    merge.communicate()
    
    #vcf
    os.system(compress1)
    #vcftoplink

    try:
        vcf2plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz --make-bed --out {data_path}/zip_file/imputed_chr{user_chromosome}", shell=True)
        vcf2plink.communicate()

        fname =f'{data_path}/zip_file/imputed_chr{user_chromosome}.log'

        with open(fname, 'r') as f:  #打開文件
            lines = f.readlines() #讀取所有行
            if "Error: Multiple instances of '_' in sample ID.\n" in lines:
                print('retry')
                vcf2plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz --make-bed --double-id --out {data_path}/zip_file/imputed_chr{user_chromosome}", shell=True)
                vcf2plink.communicate()
            if 'Error: VCF/BCF2 sample ID contains space(s).  Use --vcf-idspace-to to convert\n' in lines:
                print('retry')
                vcf2plink = subprocess.Popen(f"{main_dir}/software/plink2_dir/plink2 --vcf {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz --make-bed --id-delim ' ' --out {data_path}/zip_file/imputed_chr{user_chromosome}", shell=True)
                vcf2plink.communicate()
    except:
        print('vcf error')


    #plink
    os.system(compress2)


    #os.system(compress)
    #print("OK")
    date2 = datetime.datetime.now()
    print(date1)
    print(date2)
    process = "Done"
    os.system(f"cp {storage_dir}/result_data/{username}/{project_name}/log/imputed_* {storage_dir}/result_data/{username}/{project_name}/log/impute_log")
    with open(data_path+"/process.txt", "w") as f:
        f.write(process)
    os.system(compress3)
    os.system(f"mv {storage_dir}/result_data/{username}/{project_name}/log/chr{user_chromosome}_phased.log {storage_dir}/result_data/{username}/{project_name}/log/sp1.log")
    #os.system(f"cp {data_path}/info.png {plot_dir2}")    
    #print("PLOT DONE")
    #刪除殘餘檔案
    try:
        os.system(f"rm {storage_dir}/sample_dir/{username}/{project_name}/*")
        print(f"{project_name}--3")
        #shutil.rmtree(f"/work1782/evan/sample_dir/{username}/{project_name}")
    except:
        print('del error')
        
def submit_beagle5(username,project_name,file_format,user_chromosome,user_mafoption,user_genooption,user_mindoption,user_hwe,user_group):
#------------------------------------------------------------------------        
    #創建資料夾及pathway
    print(f"{project_name}--2")
    path = f"{storage_dir}/result_data/{username}"
    if not os.path.isdir(path):
        os.mkdir(path)
    data_path = f"{storage_dir}/result_data/{username}/{project_name}"
    os.mkdir(data_path)
    os.mkdir(data_path+"/log")
    os.mkdir(data_path+"/log/impute_log")
    os.mkdir(data_path+"/vcf_dir")
    #vcf_result為merge後的結果
    os.mkdir(data_path+"/vcf_result")
    #zip_file已轉換plink format
    os.mkdir(data_path+"/zip_file")
    #獲取時間
    date1 = datetime.datetime.now()
    date1 = date1.strftime("%Y-%m-%d %H:%M")
    plot_dir = f"{main_dir}/mysite/static/user_plot/{username}"
    if not os.path.isdir(plot_dir):
        os.mkdir(plot_dir)    
    plot_dir2 = plot_dir+"/"+project_name
    if not os.path.isdir(plot_dir2):
        os.mkdir(plot_dir2)
    #儲存全部選項

    group_select = user_group
    option_list = [date1,project_name,user_chromosome,user_mafoption,user_genooption,user_mindoption,user_hwe,group_select]
    filename = data_path+"/option_beagle5.txt"
    with open(filename,'w') as f:
        for i in option_list:
            f.write(str(i)+'\n')
    #save_option = open(data_path+"/option.txt",'w')
    #print(option_list,file = save_option)
    #save_option.close()  
    
    #if user_relatedness == True:
    #    R = ' --genome --min 0.2'
    #else:
    #    R = ''
    #if user_sexcheck == True:
    #    S = ' --check-sex'
    #else:
    #    S = ''
    if user_mafoption == 'No use':
        user_mafoption = ''
    else:
        user_mafoption = user_mafoption
    if user_genooption == 'No use':
        user_genooption = ''
    else:
        user_genooption = user_genooption
    if user_mindoption == 'No use':
        user_mindoption = ''
    else:
        user_mindoption = user_mindoption
        
    if user_hwe == '':
        user_hwe = ''
    else:
        user_hwe = float(user_hwe)
        user_hwe = f' --hwe {user_hwe}'
    total_group = ['EUR','SAS','EAS','AMR','AFR','1000G_phase3_total']
    if user_group in total_group:
        if user_group == '1000G_phase3_total':
            ref_map_shapeit4 = f"{storage_dir}/ref_dir/vcf/gmap/chr{user_chromosome}.b37.gmap.gz"
            ref_map = f"{storage_dir}/ref_dir/vcf/b_map/plink.chr{user_chromosome}.GRCh37.map"
            ref_vcf = f"{storage_dir}/ref_dir/vcf/ALL.chr{user_chromosome}.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"
        else:
            ref_map_shapeit4 = f"{storage_dir}/ref_dir/vcf/gmap/chr{user_chromosome}.b37.gmap.gz"
            ref_map = f"{storage_dir}/ref_dir/vcf/b_map/plink.chr{user_chromosome}.GRCh37.map"
            ref_vcf = f"{storage_dir}/ref_dir/vcf/{user_group}/chr{user_chromosome}_1kg_{user_group}.vcf.gz"
    elif user_group == 'Custom':
        ref_map_shapeit4 = f"{storage_dir}/ref_dir/vcf/gmap/chr{user_chromosome}.b37.gmap.gz"
        ref_map = f"{storage_dir}/ref_dir/vcf/b_map/plink.chr{user_chromosome}.GRCh37.map"
        ref_vcf = f"{storage_dir}/sample_dir/{username}/{project_name}/cusref_dir/uploadref.vcf.gz"
                    
#壓縮區----------------------------------------------------------------------------------
    compress1 = f"{main_dir}/software/zip_dir/bin/zip -jr {data_path}/{project_name}_vcf.zip {data_path}/vcf_result/*"
    compress2 = f"{main_dir}/software/zip_dir/bin/zip -jr {data_path}/{project_name}.zip {data_path}/zip_file/*"
    compress3 = f"{main_dir}/software/zip_dir/bin/zip -jr {data_path}/{project_name}_impute_log.zip {data_path}/log/impute_log/*"
    #compress3 = "./software/zip_dir/bin/zip -jr "+data_path+"/"+project_name+"_impute_log.zip "+data_path+"/log/impute_log/*"
#PLINK-----------------------------------------------------------------------------------
    try:
        process = "Quality Control"
            
        with open(data_path+"/process.txt", "w") as f:
            f.write(process)
        if file_format == 'plink':
            plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --recode vcf bgz --out {data_path}/all_qc", shell=True)
            plink.communicate()
        elif file_format == 'vcf':
            plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload.vcf.gz{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --recode vcf bgz --out {data_path}/all_qc", shell=True)
            plink.communicate()
        fname =f'{data_path}/all_qc.log'

        with open(fname, 'r') as f:  #打開文件
            lines = f.readlines() #讀取所有行
        if file_format == 'plink':
            if "Error: Multiple instances of '_' in sample ID.\n" in lines:
                print('retry')
                plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --double-id --recode vcf bgz --out {data_path}/all_qc", shell=True)
                plink.communicate()
            elif 'Warning: Underscore(s) present in sample IDs.\n' in lines:
                print('retry')
                plink = subprocess.Popen(f"{main_dir}/software/plink2_dir/plink2 --bfile {storage_dir}/sample_dir/{username}/{project_name}/upload{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --export vcf bgz id-delim=' ' --out {data_path}/all_qc", shell=True)
                plink.communicate()
        elif file_format == 'vcf':
            if "Error: Multiple instances of '_' in sample ID.\n" in lines:
                print('retry')
                plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload.vcf.gz{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --double-id --recode vcf bgz --out {data_path}/all_qc", shell=True)
                plink.communicate()
            elif 'Warning: Underscore(s) present in sample IDs.\n' in lines:
                print('retry')
                plink = subprocess.Popen(f"{main_dir}/software/plink2_dir/plink2 --vcf {storage_dir}/sample_dir/{username}/{project_name}/upload.vcf.gz{user_mafoption}{user_genooption}{user_mindoption}{user_hwe} --export vcf bgz id-delim=' ' --out {data_path}/all_qc", shell=True)
                plink.communicate()        
        word = "Quality control OK"
    except:
        print("plink error")
#SHAPEIT4--------------------------------------------------------------------------------
    try:
        #shapeit core numbers
        #core_num = 20
        process = "Pre-phasing"
            
        with open(data_path+"/process.txt", "w") as f:
            f.write(process)
        qc_index= subprocess.Popen(f"{main_dir}/software/bcftools-1.13/bcftools index {data_path}/all_qc.vcf.gz",shell=True)
        qc_index.communicate()
        shapeit4 = subprocess.Popen(f"shapeit4 --input {data_path}/all_qc.vcf.gz --map {ref_map_shapeit4} --region {user_chromosome} --reference {ref_vcf} --thread {SHAPEIT_core} --log {data_path}/log/chr{user_chromosome}_phased.log --output {data_path}/chr{user_chromosome}_phased.vcf.gz",shell=True)
        shapeit4.communicate()
            
    except:
        print("phasing error")

#beagle5---------------------------------------------------------------------------------
#    process = "Chunking"
#    
#    phase_index= subprocess.Popen(f"{main_dir}/software/bcftools-1.13/bcftools index {data_path}/chr{user_chromosome}_phased.vcf.gz",shell=True)
#    phase_index.communicate()
#            
#    with open(data_path+"/process.txt", "w") as f:
#        f.write(process)

    process = "Imputation"          
    with open(data_path+"/process.txt", "w") as f:
        f.write(process)      
    with open (ref_map, 'r') as fp:
        lines = fp.readlines()
        last_line = lines[-1]
        maxPos = int(last_line.split('\t')[-1][:-1])
        numchunk = int(maxPos/5000000)
        numchunk2 = numchunk+1
        fp.close
        start = 0

    semlock = threading.BoundedSemaphore(Beagle5_core_write)
    threads = []

    for chunk in range(1,numchunk2+1):
        endpo = start + 5000000
        startpo = start + 1
        semlock.acquire()
        threads.append(threading.Thread(target = beagle5, args = (data_path,user_chromosome,ref_vcf,ref_map,startpo,endpo,chunk,Beagle5_core,semlock)))
        threads[chunk-1].start()
        start = endpo
        process = f"Imputation({chunk}/{numchunk2})"                     
        with open(data_path+"/process.txt", "w") as f:
            f.write(process)
    for chunk in range(1,numchunk2+1):
        threads[chunk-1].join()
    filelist = f'{data_path}/filelist.txt'
    print(filelist)
    for chunk in range(1,numchunk2+1):
        result_beagle = f"{data_path}/vcf_dir/imputed_chr{user_chromosome}.chunk{str(chunk)}.vcf.gz"
        print(result_beagle)
        if os.path.isfile(result_beagle):
            index = subprocess.Popen(f"{main_dir}/software/bcftools-1.13/bcftools index {result_beagle}",shell=True)
            index.communicate()
            with open(filelist, 'a') as f:  #打開文件
                f.write(f"{data_path}/vcf_dir/imputed_chr{user_chromosome}.chunk{str(chunk)}.vcf.gz\n")   
                print(f"chunk{chunk} add")
    
    print("beagle5 done")      
#MERGE-----------------------------------------------------------------------------
    process = "Converting format"            
    with open(data_path+"/process.txt", "w") as f:
        f.write(process)
    merge = subprocess.Popen(f"{main_dir}/software/bcftools-1.13/bcftools concat -f {filelist} -Oz -o {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz ",shell=True)
    merge.communicate()
    
    #vcf
    os.system(compress1)
    #vcftoplink

    try:
        vcf2plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz --make-bed --out {data_path}/zip_file/imputed_chr{user_chromosome}", shell=True)
        vcf2plink.communicate()

        fname =f'{data_path}/zip_file/imputed_chr{user_chromosome}.log'

        with open(fname, 'r') as f:  #打開文件
            lines = f.readlines() #讀取所有行
            if "Error: Multiple instances of '_' in sample ID.\n" in lines:
                print('retry')
                vcf2plink = subprocess.Popen(f"{main_dir}/software/plink_dir/plink --vcf {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz --make-bed --double-id --out {data_path}/zip_file/imputed_chr{user_chromosome}", shell=True)
                vcf2plink.communicate()
            if 'Error: VCF/BCF2 sample ID contains space(s).  Use --vcf-idspace-to to convert\n' in lines:
                print('retry')
                vcf2plink = subprocess.Popen(f"{main_dir}/software/plink2_dir/plink2 --vcf {data_path}/vcf_result/imputed_chr{user_chromosome}.vcf.gz --make-bed --max-alleles 2 --id-delim ' ' --out {data_path}/zip_file/imputed_chr{user_chromosome}", shell=True)
                vcf2plink.communicate()
    except:
        print('vcf error')


    #plink
    os.system(compress2)


    #os.system(compress)
    #print("OK")
    date2 = datetime.datetime.now()
    print(date1)
    print(date2)
    process = "Done"
    os.system(f"cp {storage_dir}/result_data/{username}/{project_name}/vcf_dir/*.log {storage_dir}/result_data/{username}/{project_name}/log/impute_log")
    with open(data_path+"/process.txt", "w") as f:
        f.write(process)
    os.system(f"mv {storage_dir}/result_data/{username}/{project_name}/log/chr{user_chromosome}_phased.log {storage_dir}/result_data/{username}/{project_name}/log/sp1.log")
    #os.system(f"cp {data_path}/info.png {plot_dir2}")    
    #print("PLOT DONE")
    #刪除殘餘檔案
    try:
        os.system(f"rm {storage_dir}/sample_dir/{username}/{project_name}/*")
        print(f"{project_name}--3")
        #shutil.rmtree(f"/work1782/evan/sample_dir/{username}/{project_name}")
    except:
        print('del error')