from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    """The /contact/ message form.

    Kept deliberately small: an email to reply to, a reason so support can
    triage, and the message itself. Nothing is persisted - the view emails it
    and forgets it, which matches what the privacy policy promises.
    """

    REASON_CHOICES = [
        ("question", _("A question")),
        ("report", _("Report a user")),
        ("billing", _("PRO and billing")),
        ("bug", _("Something is broken")),
    ]

    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        initial="question",
        widget=forms.RadioSelect,
        label=_("What is this about?"),
    )
    email = forms.EmailField(
        max_length=254,
        label=_("Your email"),
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}),
    )
    message = forms.CharField(
        max_length=5000,
        label=_("Message"),
        widget=forms.Textarea(attrs={"rows": 6}),
    )
    # Honeypot: hidden from people, irresistible to naive bots. A filled value
    # means we drop the submission silently rather than tell the bot it failed.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def is_spam(self):
        return bool(self.data.get("website"))

    def reason_label(self):
        value = self.cleaned_data["reason"]
        return dict(self.REASON_CHOICES).get(value, value)
