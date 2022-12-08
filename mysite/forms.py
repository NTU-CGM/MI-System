#-*- encoding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import datetime
import os

class user_email(forms.Form):
    email = forms.EmailField(required=True)

class impute2_form(forms.Form):
    MAF = [
        ['', '---------------'],
        [' --maf 0.05', '0.05'],
        [' --maf 0.01', '0.01'],
        [' --maf 0.001', '0.001'],
        ['No use' ,'None'],
	]
    GENO = [
        ['', '---------------'],
        [' --geno 0.05', '0.05'],
        [' --geno 0.01', '0.01'],
        ['No use', 'None'],
        ]
    MIND = [
        ['', '---------------'],
        [' --mind 0.05', '0.05'],
        [' --mind 0.01', '0.01'],
        ['No use', 'None'],
        ]
    
    HWE = [
        ['', '---------------'],
        [' --hwe 0.001' , '0.001'],
        [' --hwe 0.0001' , '0.0001'],
        [' --hwe 0.00001' , '0.00001'],
        [' --hwe 0.000001', '0.000001'],
        ['No use', 'None'],
    ]
    
    REF = [
        ['', '---------------'],
        ['1000G','1000G_phase3'],
        ['TWB','Taiwan biobank'],
        ['HapMap3','HapMap 3'],
    ]
    GROUP = (
        ('', '---------------'),
        ('1000G_phase3', (
        ('EUR','European(EUR)'),
        ('SAS','South Asian(SAS)'),
        ('EAS','East Asian(EAS)'),
        ('AMR','Ad Mixed American(AMR)'),
        ('AFR','African(AFR)'),
        ('1000G_phase3_total','1000G_phase3 total'),
        )
        ),
        ('HapMap 3', (
        ('HapMap3','HapMap 3 -- hg18'),
        )
        ),
        ('Taiwan biobank', (
        ('TWB','Taiwan biobank'),
        )
        ),
        ('Custom refernece', (
        ('Custom','Custom'),
        )
        ),
        )
    GROUP2 = (
        ('None', 'None'),
        ('1000G_phase3', (
        ('1000G','1000G_phase3'),
#        ('EUR','European(EUR)'),
#        ('SAS','South Asian(SAS)'),
#        ('EAS','East Asian(EAS)'),
#        ('AMR','Ad Mixed American(AMR)'),
#        ('AFR','African(AFR)'),
        )
        ),
        ('Taiwan biobank', (
        ('TWB','Taiwan biobank'),
        )
        ),
        ('Custom refernece', (
        ('Custom','Custom'),
        )
        ),
        )
    GROUP3 = (
        ('None', 'None'),
        ('1000G_phase3', (
        ('1000G','1000G_phase3'),
#        ('EUR','European(EUR)'),
#        ('SAS','South Asian(SAS)'),
#        ('EAS','East Asian(EAS)'),
#        ('AMR','Ad Mixed American(AMR)'),
#        ('AFR','African(AFR)'),
        )
        ),
        ('Taiwan biobank', (
        ('TWB','Taiwan biobank'),
        )
        ),
        ('Custom refernece', (
        ('Custom','Custom'),
        )
        ),
        )
    CHR = [
       ['', '---------------'],
       ['1','1'],
       ['2','2'],
       ['3','3'],
       ['4','4'],
       ['5','5'],
       ['6','6'],
       ['7','7'],
       ['8','8'],
       ['9','9'],
       ['10','10'],
       ['11','11'],
       ['12','12'],
       ['13','13'],
       ['14','14'],
       ['15','15'],
       ['16','16'],
       ['17','17'],
       ['18','18'],
       ['19','19'],
       ['20','20'],
       ['21','21'],
       ['22','22'],
       ['X_PAR1','X_PAR1'],
       ['X_nonPAR','X_nonPAR'],
       ['X_PAR2','X_PAR2'],
       ]
    
    date = datetime.datetime.now()
    today = 'Project_'+str(date.year)+'_'+str(date.month)+'_'+str(date.day)
    user_name = forms.CharField(label='Project name',widget=forms.TextInput, max_length=50, initial= today)
    file_field = forms.FileField(label='File upload (vcf.gz/bed bim fam)',widget=forms.ClearableFileInput(attrs={'multiple': True}))
    user_chromosome = forms.ChoiceField(label='Chromosone number',widget=forms.Select(attrs={'id': 'chr',}), choices=CHR)
    user_entirechr = forms.BooleanField(label='Impute the full chromosome',widget=forms.CheckboxInput, required=False)
    user_position1 = forms.CharField(label='Start position',widget=forms.NumberInput, required=False)
    user_position2 = forms.CharField(label='End position',widget=forms.NumberInput,required=False)
    user_mafoption = forms.ChoiceField(label='Minor allele frquency option',widget=forms.Select, choices=MAF)
    user_genooption = forms.ChoiceField(label='Single SNP missing rate option',widget=forms.Select, choices=GENO)
    user_mindoption = forms.ChoiceField(label='Individual SNP missing rate option',widget=forms.Select, choices=MIND)
    user_hwe = forms.FloatField(label='Hardy-Weinberg Equilibrium option',widget=forms.NumberInput, required=False)
    user_group = forms.ChoiceField(label='Reference group select',widget=forms.Select, choices=GROUP)
    file_field2 = forms.FileField(label='File upload (.sample, .legend.gz, .hap.gz, genetic_map.txt )',widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    user_group2 = forms.ChoiceField(label='Merge reference panels',widget=forms.Select, choices=GROUP2,initial= 'None')
    user_group3 = forms.ChoiceField(label='Improved reference panels',widget=forms.Select, choices=GROUP3,initial= 'None')
    use_url = forms.BooleanField(label='Use URL to upload',widget=forms.CheckboxInput, required=False)
    file_url_vcf = forms.URLField(label='File upload url (vcf.gz)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bed = forms.URLField(label='File upload url (bed)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bim = forms.URLField(label='File upload url (bim)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_fam = forms.URLField(label='File upload url (fam)',widget=forms.URLInput,empty_value=None,required=False)
class Uploadfile(forms.Form):
    file = forms.FileField()

class Makeref(forms.Form):
    CHR = [
       ['', '---------------'],
       ['1','1'],
       ['2','2'],
       ['3','3'],
       ['4','4'],
       ['5','5'],
       ['6','6'],
       ['7','7'],
       ['8','8'],
       ['9','9'],
       ['10','10'],
       ['11','11'],
       ['12','12'],
       ['13','13'],
       ['14','14'],
       ['15','15'],
       ['16','16'],
       ['17','17'],
       ['18','18'],
       ['19','19'],
       ['20','20'],
       ['21','21'],
       ['22','22'],
       ]
    date = datetime.datetime.now()
    today = 'Project_'+str(date.year)+'_'+str(date.month)+'_'+str(date.day)   
    user_name = forms.CharField(label='Project name',widget=forms.TextInput, max_length=50, initial= today)
    #bedfile = forms.FileField(label='BED file upload',widget=forms.FileInput)
    #bimfile = forms.FileField(label='BIM file upload',widget=forms.FileInput)
    #famfile = forms.FileField(label='FAM file upload',widget=forms.FileInput)
    file_field = forms.FileField(label='File upload (vcf.gz/bed bim fam)',widget=forms.ClearableFileInput(attrs={'multiple': True}))
    user_chromosome = forms.ChoiceField(label='Chromosone number',widget=forms.Select(attrs={'id': 'chr',}), choices=CHR)
    use_url = forms.BooleanField(label='Use URL to upload',widget=forms.CheckboxInput, required=False)
    file_url_vcf = forms.URLField(label='File upload url (vcf.gz)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bed = forms.URLField(label='File upload url (bed)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bim = forms.URLField(label='File upload url (bim)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_fam = forms.URLField(label='File upload url (fam)',widget=forms.URLInput,empty_value=None,required=False)

class Split(forms.Form):
    date = datetime.datetime.now()
    today = 'Project_'+str(date.year)+'_'+str(date.month)+'_'+str(date.day)   
    user_name = forms.CharField(label='Project name',widget=forms.TextInput, max_length=50, initial= today)
    data_name = forms.CharField(label='Data name',widget=forms.TextInput, max_length=50)
    #bedfile = forms.FileField(label='BED file upload',widget=forms.FileInput)
    #bimfile = forms.FileField(label='BIM file upload',widget=forms.FileInput)
    #famfile = forms.FileField(label='FAM file upload',widget=forms.FileInput)
    file_field = forms.FileField(label='File upload (vcf.gz/bed bim fam)',widget=forms.ClearableFileInput(attrs={'multiple': True}))
    use_url = forms.BooleanField(label='Use URL to upload',widget=forms.CheckboxInput, required=False)
    file_url_vcf = forms.URLField(label='File upload url (vcf.gz)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bed = forms.URLField(label='File upload url (bed)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bim = forms.URLField(label='File upload url (bim)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_fam = forms.URLField(label='File upload url (fam)',widget=forms.URLInput,empty_value=None,required=False)
    
class Liftover(forms.Form):
    VER = [
    ['To 19', 'Hg38 to Hg19'],
    ['To 38', 'Hg19 to Hg38'],
    ['To 18', 'Hg19 to Hg18'],
    ['18 To 19', 'Hg18 to Hg19'],
    ]
    date = datetime.datetime.now()
    today = 'Project_'+str(date.year)+'_'+str(date.month)+'_'+str(date.day)   
    user_name = forms.CharField(label='Project name',widget=forms.TextInput, max_length=50, initial= today)
    data_name = forms.CharField(label='Data name',widget=forms.TextInput, max_length=50)
    convert_function = forms.ChoiceField(label='Convert function',widget=forms.Select, choices=VER)
    #bedfile = forms.FileField(label='BED file upload',widget=forms.FileInput)
    #bimfile = forms.FileField(label='BIM file upload',widget=forms.FileInput)
    #famfile = forms.FileField(label='FAM file upload',widget=forms.FileInput)
    file_field = forms.FileField(label='File upload (vcf.gz/bed bim fam)',widget=forms.ClearableFileInput(attrs={'multiple': True}),required=False)
    use_url = forms.BooleanField(label='Use URL to upload',widget=forms.CheckboxInput, required=False)
    file_url_vcf = forms.URLField(label='File upload url (vcf.gz)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bed = forms.URLField(label='File upload url (bed)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bim = forms.URLField(label='File upload url (bim)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_fam = forms.URLField(label='File upload url (fam)',widget=forms.URLInput,empty_value=None,required=False)

class Registerform(forms.ModelForm):
    username = forms.CharField(label='Username', max_length=25)
    password = forms.CharField(label='Password', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput())
    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password!=password2:
            raise forms.ValidationError('密碼不相符')
            return password2
    class Meta:
        model = User
        fields = ['username', 'password', 'password2']

class impute5_form(forms.Form):
    MAF = [
        ['', '---------------'],
        [' --maf 0.05', '0.05'],
        [' --maf 0.01', '0.01'],
        [' --maf 0.001', '0.001'],
        ['No use' ,'None'],
	]
    GENO = [
        ['', '---------------'],
        [' --geno 0.05', '0.05'],
        [' --geno 0.01', '0.01'],
        ['No use', 'None'],
        ]
    MIND = [
        ['', '---------------'],
        [' --mind 0.05', '0.05'],
        [' --mind 0.01', '0.01'],
        ['No use', 'None'],
        ]
    
    HWE = [
        ['', '---------------'],
        [' --hwe 0.001' , '0.001'],
        [' --hwe 0.0001' , '0.0001'],
        [' --hwe 0.00001' , '0.00001'],
        [' --hwe 0.000001', '0.000001'],
        ['No use', 'None'],
    ]
    
    GROUP = (
        ('', '---------------'),
        ('1000G_phase3', (
        ('EUR','European(EUR)'),
        ('SAS','South Asian(SAS)'),
        ('EAS','East Asian(EAS)'),
        ('AMR','Ad Mixed American(AMR)'),
        ('AFR','African(AFR)'),
        ('1000G_phase3_total','1000G_phase3 total'),
        )
        ),
        ('Taiwan biobank not open', (
#        ('TWB','Taiwan biobank'),
        )
        ),
        ('Custom refernece', (
        ('Custom','Custom'),
        )
        ),
        )

    CHR = [
       ['', '---------------'],
       ['1','1'],
       ['2','2'],
       ['3','3'],
       ['4','4'],
       ['5','5'],
       ['6','6'],
       ['7','7'],
       ['8','8'],
       ['9','9'],
       ['10','10'],
       ['11','11'],
       ['12','12'],
       ['13','13'],
       ['14','14'],
       ['15','15'],
       ['16','16'],
       ['17','17'],
       ['18','18'],
       ['19','19'],
       ['20','20'],
       ['21','21'],
       ['22','22'],
       ]
    
    date = datetime.datetime.now()
    today = 'Project_'+str(date.year)+'_'+str(date.month)+'_'+str(date.day)
    user_name = forms.CharField(label='Project name',widget=forms.TextInput, max_length=50, initial= today)
    file_field = forms.FileField(label='File upload (vcf.gz/bed bim fam)',widget=forms.ClearableFileInput(attrs={'multiple': True}))
    user_chromosome = forms.ChoiceField(label='Chromosone number',widget=forms.Select(attrs={'id': 'chr',}), choices=CHR)
    #user_entirechr = forms.BooleanField(label='Impute the full chromosome',widget=forms.CheckboxInput, required=False)
    #user_position1 = forms.CharField(label='Start position',widget=forms.NumberInput, required=False)
    #user_position2 = forms.CharField(label='End position',widget=forms.NumberInput,required=False)
    user_mafoption = forms.ChoiceField(label='Minor allele frquency option',widget=forms.Select, choices=MAF)
    user_genooption = forms.ChoiceField(label='Single SNP missing rate option',widget=forms.Select, choices=GENO)
    user_mindoption = forms.ChoiceField(label='Individual SNP missing rate option',widget=forms.Select, choices=MIND)
    user_hwe = forms.FloatField(label='Hardy-Weinberg Equilibrium option',widget=forms.NumberInput, required=False)
    user_group = forms.ChoiceField(label='Reference group select',widget=forms.Select, choices=GROUP)
    file_field2 = forms.FileField(label='File upload (.vcf.gz )',widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    #user_group2 = forms.ChoiceField(label='Merge reference panels',widget=forms.Select, choices=GROUP2,initial= 'None')
    #user_group3 = forms.ChoiceField(label='Improved reference panels',widget=forms.Select, choices=GROUP3,initial= 'None')
    use_url = forms.BooleanField(label='Use URL to upload',widget=forms.CheckboxInput, required=False)
    file_url_vcf = forms.URLField(label='File upload url (vcf.gz)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bed = forms.URLField(label='File upload url (bed)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bim = forms.URLField(label='File upload url (bim)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_fam = forms.URLField(label='File upload url (fam)',widget=forms.URLInput,empty_value=None,required=False)

class beagle5_form(forms.Form):
    MAF = [
        ['', '---------------'],
        [' --maf 0.05', '0.05'],
        [' --maf 0.01', '0.01'],
        [' --maf 0.001', '0.001'],
        ['No use' ,'None'],
	]
    GENO = [
        ['', '---------------'],
        [' --geno 0.05', '0.05'],
        [' --geno 0.01', '0.01'],
        ['No use', 'None'],
        ]
    MIND = [
        ['', '---------------'],
        [' --mind 0.05', '0.05'],
        [' --mind 0.01', '0.01'],
        ['No use', 'None'],
        ]
    
    HWE = [
        ['', '---------------'],
        [' --hwe 0.001' , '0.001'],
        [' --hwe 0.0001' , '0.0001'],
        [' --hwe 0.00001' , '0.00001'],
        [' --hwe 0.000001', '0.000001'],
        ['No use', 'None'],
    ]
    
    GROUP = (
        ('', '---------------'),
        ('1000G_phase3', (
        ('EUR','European(EUR)'),
        ('SAS','South Asian(SAS)'),
        ('EAS','East Asian(EAS)'),
        ('AMR','Ad Mixed American(AMR)'),
        ('AFR','African(AFR)'),
        ('1000G_phase3_total','1000G_phase3 total'),
        )
        ),
        ('Taiwan biobank not open', (
#        ('TWB','Taiwan biobank'),
        )
        ),
        ('Custom refernece', (
        ('Custom','Custom'),
        )
        ),
        )

    CHR = [
       ['', '---------------'],
       ['1','1'],
       ['2','2'],
       ['3','3'],
       ['4','4'],
       ['5','5'],
       ['6','6'],
       ['7','7'],
       ['8','8'],
       ['9','9'],
       ['10','10'],
       ['11','11'],
       ['12','12'],
       ['13','13'],
       ['14','14'],
       ['15','15'],
       ['16','16'],
       ['17','17'],
       ['18','18'],
       ['19','19'],
       ['20','20'],
       ['21','21'],
       ['22','22'],
       ]
    
    date = datetime.datetime.now()
    today = 'Project_'+str(date.year)+'_'+str(date.month)+'_'+str(date.day)
    user_name = forms.CharField(label='Project name',widget=forms.TextInput, max_length=50, initial= today)
    file_field = forms.FileField(label='File upload (vcf.gz/bed bim fam)',widget=forms.ClearableFileInput(attrs={'multiple': True}))
    user_chromosome = forms.ChoiceField(label='Chromosone number',widget=forms.Select(attrs={'id': 'chr',}), choices=CHR)
    #user_entirechr = forms.BooleanField(label='Impute the full chromosome',widget=forms.CheckboxInput, required=False)
    #user_position1 = forms.CharField(label='Start position',widget=forms.NumberInput, required=False)
    #user_position2 = forms.CharField(label='End position',widget=forms.NumberInput,required=False)
    user_mafoption = forms.ChoiceField(label='Minor allele frquency option',widget=forms.Select, choices=MAF)
    user_genooption = forms.ChoiceField(label='Single SNP missing rate option',widget=forms.Select, choices=GENO)
    user_mindoption = forms.ChoiceField(label='Individual SNP missing rate option',widget=forms.Select, choices=MIND)
    user_hwe = forms.FloatField(label='Hardy-Weinberg Equilibrium option',widget=forms.NumberInput, required=False)
    user_group = forms.ChoiceField(label='Reference group select',widget=forms.Select, choices=GROUP)
    file_field2 = forms.FileField(label='File upload (.vcf.gz )',widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    #user_group2 = forms.ChoiceField(label='Merge reference panels',widget=forms.Select, choices=GROUP2,initial= 'None')
    #user_group3 = forms.ChoiceField(label='Improved reference panels',widget=forms.Select, choices=GROUP3,initial= 'None')
    use_url = forms.BooleanField(label='Use URL to upload',widget=forms.CheckboxInput, required=False)
    file_url_vcf = forms.URLField(label='File upload url (vcf.gz)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bed = forms.URLField(label='File upload url (bed)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_bim = forms.URLField(label='File upload url (bim)',widget=forms.URLInput,empty_value=None,required=False)
    file_url_fam = forms.URLField(label='File upload url (fam)',widget=forms.URLInput,empty_value=None,required=False)

class Loginform(forms.Form):
    username = forms.CharField(label='Username', max_length=25)
    password = forms.CharField(label='Password', widget=forms.PasswordInput())


class upload_mult_data(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))