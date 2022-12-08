from django.http import HttpResponseRedirect
def jump_page():
    print('OK')
    return HttpResponseRedirect('/success_page/')
