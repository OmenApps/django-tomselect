"""Middleware that sends Django messages to the client via HX-Trigger header."""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django_htmx.http import trigger_client_event

logger = logging.getLogger(__name__)


class HtmxMessagesMiddleware(MiddlewareMixin):
    """Middleware that sends Django messages to the client via HX-Trigger header."""

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Process the response, sending Django messages to the client."""

        # Only handle messages if this is an htmx request
        if getattr(request, "htmx", False):
            storage = messages.get_messages(request)
            msg_list = []
            for msg in storage:
                msg_list.append(
                    {
                        "message": msg.message,
                        "level": msg.level_tag,
                    }
                )
            # Sets the HX-Trigger header in the response, triggering an event named 'django_messages'
            trigger_client_event(response, "django_messages", {"messages": msg_list})
        return response
