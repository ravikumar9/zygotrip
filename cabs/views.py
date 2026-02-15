from django.shortcuts import render

def coming_soon(request):
    context = {'module_name': 'Cabs'}
    return render(request, 'coming_soon.html', context)
