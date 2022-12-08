"""ch08www URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from mysite import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('login/', views.login),
    path('get_email/', views.email),
    path('tutorial/', views.tutorial),
    path('logout/', views.logout),
    path('imputation/',views.imputation_page,name='imputation_page'),
    path('imputation_impute5/',views.imputation_impute5,name='imputation_impute5'),
    path('imputation_beagle5/',views.imputation_beagle5,name='imputation_beagle5'),
    path('qctest_all/', views.qcoption_all),
    path('result_page_v2/', views.result_page_v2,name='result_page_v2'),
    path('Download_page_v2/', views.download_page),
    path('reference/', views.reference_page),
    path('upload_mult_test/', views.upload_mult_test),
    path('success_page/', views.success_page),
    path('filedel/', views.del_dir),
    path('filedownload/', views.file_download),
    path('filedownload_vcf/', views.file_download_vcf),
    path('filedownload_log/', views.file_download_log),
    path('filedownload_info/', views.file_download_info),
    path('filedownload_qc_log/', views.file_download_qc_log),
    path('filedownload_sp1_log/', views.file_download_sp1_log),
    path('filedownload_sp2_log/', views.file_download_sp2_log),
    path('filedownload_sp3_log/', views.file_download_sp3_log),
    path('example_download/', views.example_file_download),
    path('register/', views.register),
    path('split_chr/', views.split_chr),
    path('liftover/', views.liftover),
    path('submit_page/',views.submit_page)
]
