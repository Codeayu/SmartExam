from django.contrib import admin
from .models import Customuser, ExamHistory


admin.site.site_header = "Smart Exam Admin"
admin.site.site_title = "Smart Exam Admin Portal"
admin.site.index_title = "Welcome to Smart Exam Admin Portal"
admin.site.register(Customuser)  # Register the Customuser model in the admin panel
admin.site.register(ExamHistory)  # Register the ExamHistory model in the admin panel

# Register your models here.
