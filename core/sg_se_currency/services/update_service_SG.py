# -*- coding: utf-8 -*-
# © 2009 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
from .currency_getter_interface import CurrencyGetterInterface


class SGGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for Yahoo finance service
    """
    code = 'SG'
    name = 'Monetary Authority of Singapore'

    supported_currency_array = [
        "EUR", "GBP", "USD", "AUD", "CAD", "CNY", "HKD",
        "INR", "IDR", "JPY", "KRW", "MYR",
        "TWD", "NZD", "PHP", "QAR", "SAR", "CHF",
        "THB", "AED", "VND", "SGD"]

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of curreny_getter_interface"""
        self.validate_cur(main_currency)
        url = ('https://eservices.mas.gov.sg/api/action/datastore/search.json?resource_id=95932927-c8bc-4e7a-b484-68a66a24edfe&limit=1&sort=end_of_day desc')
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        rawfile = self.get_url(url)
        jsondata = json.loads(rawfile)
        for curr in currency_array:
            self.validate_cur(curr)
            res = jsondata['result']['records'][0]
            if curr.lower() in rawfile:
                ext = 'cny,hkd,inr,idr,jpy,krw,myr,twd,php,qar,sar,thb,aed,vnd'
                if curr.lower() in ext:
                    val = curr.lower() + '_sgd_100'
                    val = str(val)
                    data = res[val]
                    print data
                else:
                    val = curr.lower() + '_sgd'
                    val = str(val)
                    data = res[val]
                    print data

                if val:
                    self.updated_currency[curr] = data
                else:
                    raise Exception('Could not update the %s' % (curr))

        return self.updated_currency, self.log_info