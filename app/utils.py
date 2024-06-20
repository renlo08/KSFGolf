def arrange_urlpatterns(urlpatterns_list):
    general_urlpatterns = []
    specific_urlpatterns = []

    for pattern in urlpatterns_list:
        if '<' in pattern.pattern.regex.pattern:  # This means it's a general pattern
            general_urlpatterns.append(pattern)
        else:
            specific_urlpatterns.append(pattern)

    return specific_urlpatterns + general_urlpatterns
