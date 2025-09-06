# pool/admin.py

from django.contrib import admin, messages
from .models import Team, Game, Pick, Score, PoolSettings, Email, WeeklyNote
from django import forms
from django.urls import path
from django.http import JsonResponse
from django.core.management import call_command
from io import StringIO
from markdownx.admin import MarkdownxModelAdmin
import markdown
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import re


User = get_user_model()

def parse_markdown_email(md_text: str):
    """
    Parse a markdown email string into subject, plain text body, and HTML body.

    Assumes the first line is "Subject: ..." or just the subject line.
    """
    lines = md_text.splitlines()

    # Find first non-empty line for subject
    subject = ""
    body_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            # This line is the subject
            subject = stripped
            # If it starts with 'Subject:', remove that
            if subject.lower().startswith("subject:"):
                subject = subject[len("subject:"):].strip()
            # Everything after this line is the body
            body_lines = lines[i+1:]
            break

    body_md = "\n".join(body_lines).strip()

    # Plain text version: remove Markdown formatting
    body_text = re.sub(r'(\*\*|__|\*|~~|`|#)', '', body_md).strip()

    # HTML version
    body_html = markdown.markdown(body_md)

    return subject, body_text, body_html


class PoolAdmin(admin.AdminSite):
    site_header = 'NFL Pool Administration'
    site_title = 'NFL Pool Administration'
    site_index_title = 'NFL Pool Administration'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "update_points/",
                self.admin_view(self.update_points_view),
                name="update_points",
            ),
            path("create_email/",
                 self.admin_view(self.create_email_view),
                 name="create_email",),
            path("send_email/",
                 self.admin_view(self.send_email_view),
                 name="send_email",),
        ]
        return custom_urls + urls

    def update_points_view(self, request):
        """AJAX view to run the command and return JSON output."""
        output = StringIO()
        try:
            call_command("update_points_earned", stdout=output)
            status = "success"
        except Exception as e:
            output.write(str(e))
            status = "error"

        return JsonResponse({
            "status": status,
            "output": output.getvalue(),
        })

    def create_email_view(self, request):
        """AJAX view to run the command and return JSON output."""
        output = StringIO()
        try:
            call_command("create_email", stdout=output)
            status = "success"

        except Exception as e:
            output.write(str(e))
            status = "error"

        raw_output = output.getvalue()
        rendered_output = markdown.markdown(raw_output)

        return JsonResponse({
            "status": status,
            "output": rendered_output,
        })

    # def send_email_view(self, request):
    #     email_id = request.GET.get("id")
    #     if not email_id:
    #         messages.error(request, "No email ID provided.")
    #         return redirect(request.META.get('HTTP_REFERER', '/admin/'))
    #
    #     try:
    #         email = Email.objects.get(pk=email_id)
    #         # TODO: your send logic here
    #         messages.success(request, f"Email {email.pk} sent successfully!")
    #         return redirect(f"/admin/pool/email/{email.pk}/change/")
    #     except Email.DoesNotExist:
    #         messages.error(request, "Email not found.")
    #         return redirect(request.META.get('HTTP_REFERER', '/admin/'))
    def send_email_view(self, request):
        email_id = request.GET.get("id")
        if not email_id:
            return JsonResponse(
                {"status": "error", "message": "No email ID provided."})

        try:
            email = Email.objects.get(pk=email_id)
            subject, plain_text, html_text = parse_markdown_email(email.text)


            # Send to all users
            recipients = User.objects.filter(is_active=True).values_list(
                "email", flat=True)
            for recipient in recipients:
                send_mail(
                    subject=subject,
                    message=plain_text,
                    html_message=html_text,  # HTML version
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False,
                )

            return JsonResponse({"status": "success",
                                    "message": f"Email {email.pk} sent to all users."})

        except Email.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Email not found."})


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)
    ordering = ("name",)
    search_fields = ("name",)

class GameAdminForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Limit the winner choices to just home_team and away_team
            self.fields['winner'].queryset = self.fields['winner'].queryset.filter(
                pk__in=[self.instance.home_team_id, self.instance.away_team_id]
            )


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    form = GameAdminForm
    list_display = ("home_team", "away_team", "week")
    list_filter = ("week",)  # adds a sidebar filter for weeks




@admin.register(Pick)
class PickAdmin(admin.ModelAdmin):
    list_display = ("game", "picked_team", "user")


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("week", "points")

# @admin.register(PoolSettings)
# class PoolSettingsAdmin(admin.ModelAdmin):
#     def has_add_permission(self, request):
#         # only allow adding if no instance exists
#         return not PoolSettings.objects.exists()

@admin.register(PoolSettings)
class PoolSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'enforce_pick_window', 'site_maintenance')
    list_editable = ('enforce_pick_window', 'site_maintenance')
    list_display_links = ('id',)

    def has_add_permission(self, request):
        """Allow only one PoolSettings instance."""
        return not PoolSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of PoolSettings."""
        return False

@admin.register(Email)
class EmailAdmin(MarkdownxModelAdmin):
    list_display = ("date",)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Pass flag to template to show Save and Send button."""
        extra_context = extra_context or {}
        extra_context["show_save_and_send"] = True
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)

    def response_change(self, request, obj):
        """Called after editing an existing email."""
        if "_saveandsend" in request.POST:
            obj.save()  # ensure any changes are saved
            return redirect(f"{reverse('pooladmin:send_email')}?id={obj.id}")
        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        """Called after adding a new email."""
        if "_saveandsend" in request.POST:
            obj.save()  # ensure object is saved and has a PK
            return redirect(f"{reverse('pooladmin:send_email')}?id={obj.id}")
        return super().response_add(request, obj, post_url_continue)




# Register models with custom admin site
pool_admin_site = PoolAdmin(name="pooladmin")
pool_admin_site.register(Pick)
pool_admin_site.register(Game)
