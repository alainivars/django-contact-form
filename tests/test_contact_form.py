from __future__ import unicode_literals

"""
Contact Form tests
"""
from django import test
from django.core import mail
from django.core.urlresolvers import reverse
from django.forms import CharField, EmailField
from django.template import loader, TemplateDoesNotExist

# from contact_form_bootstrap import forms, views
from contact_form_bootstrap.forms import forms, BaseEmailFormMixin, ContactForm

from mock import Mock


def test_BaseEmailFormMixin_get_email_headers():
    form = BaseEmailFormMixin()
    assert not form.get_email_headers()

class BaseEmailFormMixinTests(test.TestCase):

    def test_goods_values_in_contact_page(self):
        resp = self.client.get(reverse("contact"))
        print(resp.content)
        assert b'center: new google.maps.LatLng(48.8148446' in resp.content
        assert b'map: map, position: new google.maps.LatLng(48.8148446' in resp.content
        assert b'<h3 class="fn org">my company</h3>' in resp.content
        assert b'<span class="locality">Maybe-there</span>' in resp.content
        assert b'<abbr title="Phone">P</abbr>: +336 1234 5678</p>' in resp.content
        assert b'<a class="email" href="mailto:contact@mycompany.com">contact@mycompany.com</a>' in resp.content
        assert b'<abbr title="Hours">H</abbr>: Monday - Friday: 9:00 to 18:00' in resp.content
        assert b'facebook-link"><a href="http://fr-fr.facebook.com/people/Maybe-there"' in resp.content
        assert b'linkedin-link"><a href="http://www.linkedin.com/in/Maybe-there"' in resp.content
        assert b'twitter-link"><a href="http://twitter.com/Maybe-there"' in resp.content
        assert b'google-plus-link"><a href="https://plus.google.com/+Maybe-there/posts"' in resp.content

    # @mock.patch('django.template.loader.render_to_string')
    # def test_get_message_returns_rendered_message_template(self, render_to_string):
    #     context = {'message': b'an example message.'}
    #
    #     class TestForm(forms.BaseEmailFormMixin):
    #         message_template_name = "my_template.html"
    #
    #         def get_context(self):
    #             return context
    #
    #     form = TestForm()
    #
    #     message = form.get_message()
    #     self.assertEqual(render_to_string.return_value, message)
    #     render_to_string.assert_called_once_with(form.message_template_name, context)

    # @mock.patch('django.template.loader.render_to_string')
    # def test_get_subject_returns_single_line_rendered_subject_template(self, render_to_string):
    #     render_to_string.return_value = b'This is \na \ntemplate.'
    #     context = {'message': b'an example message.'}
    #
    #     class TestForm(forms.BaseEmailFormMixin):
    #         subject_template_name = "my_template.html"
    #
    #         def get_context(self):
    #             return context
    #
    #     form = TestForm()
    #
    #     subject = form.get_subject()
    #     self.assertEqual('This is a template.', subject)
    #     render_to_string.assert_called_once_with(form.subject_template_name, context)

    def test_get_context_returns_cleaned_data_with_request_when_form_is_valid(self):
        request = test.RequestFactory().post(reverse("contact"))

        class TestForm(BaseEmailFormMixin, forms.Form):
            name = CharField()

        form = TestForm(data={'name': b'test'})
        form.request = request
        self.assertEqual(dict(name='test', request=request), form.get_context())

    def test_get_context_returns_value_error_when_form_is_invalid(self):
        class TestForm(BaseEmailFormMixin, forms.Form):
            name = CharField()

        form = TestForm(data={})
        with self.assertRaises(ValueError) as ctx:
            form.get_context()
        assert "Cannot generate Context when form is invalid." == str(ctx.exception)

def test_sends_mail_with_message_dict(monkeypatch):
    request = test.RequestFactory().get(reverse("contact"))
    get_message_dict = Mock()
    get_message_dict.return_value = {"to": ["user@example.com"]}
    monkeypatch.setattr(
        "contact_form_bootstrap.forms.BaseEmailFormMixin.get_message_dict",
        get_message_dict)
    send = Mock()
    send.return_value = 1
    monkeypatch.setattr("django.core.mail.message.EmailMessage.send", send)

    form = BaseEmailFormMixin()
    assert form.send_email(request) == 1

def test_send_mail_sets_request_on_instance(monkeypatch):
    request = test.RequestFactory().get(reverse("contact"))
    get_message_dict = Mock()
    get_message_dict.return_value = {"to": ["user@example.com"]}
    monkeypatch.setattr(
        "contact_form_bootstrap.forms.BaseEmailFormMixin.get_message_dict",
        get_message_dict)
    send = Mock()
    send.return_value = 1
    monkeypatch.setattr("django.core.mail.message.EmailMessage.send", send)

    form = BaseEmailFormMixin()
    form.send_email(request)
    assert request == form.request

# def test_gets_message_dict(monkeypatch):
#     form = forms.BaseEmailFormMixin()
#     message_dict = form.get_message_dict()
#
#     assert message_dict == {
#         "from_email": form.from_email,
#         "to": form.recipient_list,
#         "body": b'get_message.return_value',
#         "subject": b'get_subject.return_value',
#     }

    # @mock.patch("contact_form_bootstrap.forms.BaseEmailFormMixin.get_subject")
    # @mock.patch("contact_form_bootstrap.forms.BaseEmailFormMixin.get_message")
    # def test_get_message_dict_adds_headers_when_present(self, get_message, get_subject):
    #     email_headers = {"Reply-To": "user@example.com"}
    #
    #     class HeadersForm(forms.BaseEmailFormMixin):
    #
    #         def get_email_headers(self):
    #             return email_headers
    #
    #     form = HeadersForm()
    #     message_dict = form.get_message_dict()
    #
    #     self.assertEqual({
    #         "from_email": form.from_email,
    #         "to": form.recipient_list,
    #         "body": get_message.return_value,
    #         "subject": get_subject.return_value,
    #         "headers": email_headers,
    #     }, message_dict)


class ContactFormTests(test.TestCase):

    def test_is_subclass_of_form_and_base_email_form_mixin(self):
        self.assertTrue(issubclass(ContactForm, BaseEmailFormMixin))
        # self.assertTrue(issubclass(ContactForm, Form))

    def test_sends_mail_with_headers(self):
        class ReplyToForm(ContactForm):
            email = EmailField()

            def get_email_headers(self):
                return {'Reply-To': self.cleaned_data['email']}

        request = test.RequestFactory().get(reverse("contact"))
        reply_to_email = u'user@example.com' # the user's email
        data = {
            'name': b'Test',
            'body': b'Test message',
            'phone': b'0123456789',
            'email': reply_to_email,
        }
        form = ReplyToForm(data=data)
        print(form)
        assert form.send_email(request)
        assert len(mail.outbox) == 1
        reply_to_header_email = mail.outbox[0].extra_headers['Reply-To']
        self.assertEqual(reply_to_email, reply_to_header_email)
