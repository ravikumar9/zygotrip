from django.shortcuts import render

def coming_soon(request):
    context = {'module_name': 'Trains'}
    return render(request, 'coming_soon.html', context)
