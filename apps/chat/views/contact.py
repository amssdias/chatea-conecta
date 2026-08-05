import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import BadHeaderError, EmailMessage
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from apps.chat.forms import ContactForm

logger = logging.getLogger(__name__)


class ContactView(FormView):
    """Emails a support message. Stores nothing.

    The privacy policy says we keep no personal data, so the address and the
    message go straight out over SMTP and are never written to the database.
    """

    template_name = "pages/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("chat:contact")

    def form_valid(self, form):
        if form.is_spam():
            # Honeypot tripped. Show the same success message rather than
            # telling the bot what gave it away.
            messages.success(self.request, self.success_message())
            return super().form_valid(form)

        support = getattr(
            settings, "SUPPORT_EMAIL", "support@chatea-conecta.com"
        )
        sender = form.cleaned_data["email"]

        email = EmailMessage(
            subject=f"[Contact] {form.reason_label()}",
            body=f"From: {sender}\nReason: {form.reason_label()}\n\n{form.cleaned_data['message']}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[support],
            reply_to=[sender],
        )

        try:
            email.send(fail_silently=False)
        except BadHeaderError:
            logger.warning("Contact form rejected: bad header from %s", sender)
            form.add_error(None, _("That message could not be sent. Please try again."))
            return self.form_invalid(form)
        except Exception:
            logger.exception("Contact form delivery failed")
            form.add_error(
                None,
                _(
                    "We could not send that just now. Please email "
                    "support@chatea-conecta.com directly."
                ),
            )
            return self.form_invalid(form)

        messages.success(self.request, self.success_message())
        return super().form_valid(form)

    @staticmethod
    def success_message():
        return _("Thanks, your message is on its way. We usually reply within two working days.")
