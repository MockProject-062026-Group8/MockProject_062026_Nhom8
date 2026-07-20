from django.shortcuts import render


# Hardcoded data — matches mockup exactly, no DB needed
_SEVERITY_LEVELS = [
    {
        'name':        'Minor',
        'color_tag':   'gray',
        'description': 'Low-risk event; no injury or intervention required.',
        'example':     'e.g. minor skin tear, no treatment needed',
    },
    {
        'name':        'Moderate',
        'color_tag':   'yellow',
        'description': 'Injury requiring minor treatment; no hospitalization.',
        'example':     'e.g. bruise requiring first aid, missed dose',
    },
    {
        'name':        'Major',
        'color_tag':   'orange',
        'description': 'Significant injury requiring treatment; possible hospitalization.',
        'example':     'e.g. fall with fracture, med error',
    },
    {
        'name':        'Critical',
        'color_tag':   'red',
        'description': 'Life-threatening event requiring emergency intervention.',
        'example':     'e.g. elopement, cardiac event',
    },
]


def severity_list(request):
    return render(request, 'incidents/severity_list.html', {
        'severity_levels': _SEVERITY_LEVELS,
        'active_menu':     'incident_severity',
    })
