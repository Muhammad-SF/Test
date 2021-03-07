# -*- coding: utf-8 -*-


import base64
import logging
from openerp import api, models
from openerp import report as odoo_report
from openerp import tools

_logger = logging.getLogger(__name__)


class MailTemplate(models.Model):
    _inherit = "mail.template"
    _name = "mail.template"

    @api.multi
    def generate_email(self, res_ids, fields=None):
        """Generates an email from the template for given the given model based on
        records given by res_ids.

        :param template_id: id of the template to render.
        :param res_id: id of the record to use for rendering the template (model
                       is taken from template definition)
        :returns: a dict containing all relevant fields for creating a new
                  mail.mail entry, with one extra key ``attachments``, in the
                  format [(report_name, data)] where data is base64 encoded.
        """

        self.ensure_one()
        multi_mode = True
        if isinstance(res_ids, (int, long)):
            res_ids = [res_ids]
            multi_mode = False
        if fields is None:
            fields = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to']

        res_ids_to_templates = self.get_email_template(res_ids)

        # templates: res_id -> template; template -> res_ids
        templates_to_res_ids = {}
        for res_id, template in res_ids_to_templates.iteritems():
            templates_to_res_ids.setdefault(template, []).append(res_id)

        results = dict()
        for template, template_res_ids in templates_to_res_ids.iteritems():
            Template = self.env['mail.template']

            # generate fields value for all res_ids linked to the current template
            if template.lang:
                Template = Template.with_context(lang=template._context.get('lang'))
            for field in fields:
                Template = Template.with_context(safe=field in {'subject'})
                generated_field_values = Template.render_template(
                    getattr(template, field), template.model, template_res_ids,
                    post_process=(field == 'body_html'))
                for res_id, field_value in generated_field_values.iteritems():
                    if template._context.get('is_subscription_mail'):
                        if field == 'email_to':
                            # _logger.info("*** si email_to"+str(results))
                            results.setdefault(res_id, dict())[field] = template._context.get('email_to')
                        elif field == 'email_cc':
                            # _logger.info("*** si email_cc"+str(results))
                            results.setdefault(res_id, dict())[field] = template._context.get('email_cc')
                        else:
                            # _logger.info("*** si else "+str(field)+" :: "+str(results))
                            results.setdefault(res_id, dict())[field] = field_value
                    else:
                        results.setdefault(res_id, dict())[field] = field_value
                        # _logger.info("*** si else "+str(field)+" :: "+str(results))
            # compute recipients
            if any(field in fields for field in ['email_to', 'partner_to', 'email_cc']):
                results = template.generate_recipients(results, template_res_ids)
            # update values for all res_ids
            for res_id in template_res_ids:
                values = results[res_id]
                # body: add user signature, sanitize
                if 'body_html' in fields and template.user_signature:
                    signature = self.env.user.signature
                    if signature:
                        values['body_html'] = tools.append_content_to_html(values['body_html'], signature, plaintext=False)
                if values.get('body_html'):
                    values['body'] = tools.html_sanitize(values['body_html'])
                # technical settings
                values.update(
                    mail_server_id=template.mail_server_id.id or False,
                    auto_delete=template.auto_delete,
                    model=template.model,
                    res_id=res_id or False,
                    attachment_ids=[attach.id for attach in template.attachment_ids],
                )

            # Add report in attachments: generate once for all template_res_ids
            if template._context.get('is_subscription_mail'):
                try:
                    template.report_template = template._context.get('attachment_ids')[0]
                except(TypeError, KeyError) as e:
                    print e
                    _logger.info("mail.py :: report template empty")

            if template.report_template and 'report_template_in_attachment' not in self.env.context:
                for res_id in template_res_ids:

                    attachments = []
                    report_name = self.render_template(template.report_name, template.model, res_id)
                    if template._context.get('is_subscription_mail'):
                        if Template._context.get('report_template_model'):
                            so_obj = self.pool.get('ir.actions.report.xml')
                            so_obj = so_obj.browse(self._cr, self._uid, Template._context.get('report_template_model')[0], Template._context)
                            report = so_obj
                        else:
                            report = template.report_template
                    else:
                        report = template.report_template
                    report_service = report.report_name

                    if report.report_type in ['qweb-html', 'qweb-pdf']:
                        result, format = self.pool['report'].get_pdf(self._cr, self._uid, [res_id], report_service, context=Template._context), 'pdf'
                    else:
                        result, format = odoo_report.render_report(self._cr, self._uid, [res_id], report_service, {'model': template.model}, Template._context)

                    # TODO in trunk, change return format to binary to match message_post expected format
                    result = base64.b64encode(result)
                    if not report_name:
                        report_name = 'report.' + report_service
                    ext = "." + format
                    if not report_name.endswith(ext):
                        report_name += ext
                    attachments.append((report_name, result))
                    results[res_id]['attachments'] = attachments

        return multi_mode and results or results[res_ids[0]]
