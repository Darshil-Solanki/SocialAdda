import sys

from django.core.mail.backends.base import BaseEmailBackend


class ReadableConsoleEmailBackend(BaseEmailBackend):
    """Prints emails to the terminal as plain text, for development.

    Django's console backend prints the wire format. Lines over 76 characters are quoted-printable encoded there,
    so a link shows `=3D` instead of `=` and a `=` at the end of a line. Copying such a link gives a broken
    token, and the reset page reports it as expired. This backend prints the body exactly as written.
    """

    def __init__(self, *args, stream=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream = stream or sys.stdout

    def send_messages(self, email_messages):
        for message in email_messages:
            self.stream.write(
                f'\n--- email ---\nFrom: {message.from_email}\nTo: {", ".join(message.to)}\n'
                f'Subject: {message.subject}\n\n{message.body}\n-------------\n'
            )
        self.stream.flush()
        return len(email_messages)
