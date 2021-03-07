odoo.define('pos_promotion', function (require) {

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var PopupWidget = require("point_of_sale.popups");
    var core = require('web.core');
    var _t = core._t;
    var gui = require('point_of_sale.gui');
    var utils = require('web.utils');
    var round_pr = utils.round_precision;


    // ------- *** models *** -----------------------------//
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            var self = this;
            var res = _super_order.initialize.apply(this, arguments);
            setInterval(function () {
                if (self.pos.auto_promotion && self.pos.auto_promotion == true) {
                    self.auto_build_promotion();
                    console.log('auto build promotion')
                }
            }, 1000);
            return res;
        },
        get_total_without_promotion_and_tax: function () {
            var rounding = this.pos.currency.rounding;
            var orderlines = this.orderlines.models
            var sum = 0
            var i = 0
            while (i < orderlines.length) {
                var line = orderlines[i];
                if (line.promotion && line.promotion == true) {
                    i++;
                    continue
                }
                sum += round_pr(line.get_unit_price() * line.get_quantity() * (1 - line.get_discount() / 100), rounding)
                i++
            }
            return sum;
        },
        auto_build_promotion: function () {
            if (!this.pos.building_promotion || this.pos.building_promotion == false) {
                if (this.pos.config.allow_promotion == true && this.pos.config.promotion_ids.length) {
                    this.pos.building_promotion = true;
                    var promotions = this.pos.promotions
                    if (promotions) {
                        for (var i = 0; i < promotions.length; i++) {
                            var type = promotions[i].type
                            var order = this;
                            if (order.orderlines.length) {
                                if (type == '1_discount_total_order') {
                                    order.compute_discount_total_order(promotions[i]);
                                }
                                if (type == '2_discount_category') {
                                    order.compute_discount_category(promotions[i]);
                                }
                                if (type == '3_discount_by_quantity_of_product') {
                                    order.compute_discount_by_quantity_of_products(promotions[i]);
                                }
                                if (type == '4_pack_discount') {
                                    order.compute_pack_discount(promotions[i]);
                                }
                                if (type == '5_pack_free_gift') {
                                    order.compute_pack_free_gift(promotions[i]);
                                }
                                if (type == '6_price_filter_quantity') {
                                    order.compute_price_filter_quantity(promotions[i]);
                                }
                            }
                        }
                    }
                    this.pos.building_promotion = false;
                }
            }
        },
        export_for_printing: function () {
            var res = _super_order.export_for_printing.call(this);
            if (this.promotion_amount) {
                res.promotion_amount = this.promotion_amount;
            }
            return res
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.call(this);
            if (this.promotion_amount) {
                json.promotion_amount = this.promotion_amount;
            }
            return json
        },
        remove_promotion_lines: function (lines) {
            for (i in lines) {
                this.remove_orderline(lines[i]);
            }
        },
        get_product_and_quantity_current_order: function () {
            var lines_list = {};
            var lines = this.orderlines.models;
            var i = 0;
            while (i < lines.length) {
                var line = lines[i];
                if (line.promotion) {
                    i++;
                    continue
                }
                if (!lines_list[line.product.id]) {
                    lines_list[line.product.id] = line.quantity;
                } else {
                    lines_list[line.product.id] += line.quantity;
                }
                i++;
            }
            return lines_list
        },
        checking_can_apply_promotion: function (promotion_condition_items) {
            var check = true;
            var quantity_item_by_product_id = {};
            for (i in promotion_condition_items) {
                var item = promotion_condition_items[i];
                if (!quantity_item_by_product_id[item.product_id[0]]) {
                    quantity_item_by_product_id[item.product_id[0]] = item.quantity_free
                } else {
                    quantity_item_by_product_id[item.product_id[0]] += item.quantity_free
                }
            }
            var quantity_line_by_product_id = this.get_product_and_quantity_current_order();
            if (!quantity_line_by_product_id || !promotion_condition_items) {
                return false
            }
            for (i in promotion_condition_items) {
                if (!quantity_line_by_product_id[promotion_condition_items[i].product_id[0]]) {
                    check = false;
                    continue
                }
                if (quantity_line_by_product_id[promotion_condition_items[i].product_id[0]] < quantity_item_by_product_id[promotion_condition_items[i].product_id[0]]) {
                    check = false;
                    continue
                }
            }
            return check
        },
        checking_apply_total_order: function (promotion) {
            var discount_lines = this.pos.promotion_discount_order_by_promotion_id[promotion.id];
            var total_order = this.get_total_without_promotion_and_tax();
            var lines = this.orderlines.models;
            if (lines.length) {
                for (var j = 0; j < lines.length; j++) {
                    if (lines[j].promotion_discount_total_order) {
                        this.remove_orderline(lines[j]);
                    }
                }
            }
            var discount_line_tmp = null;
            var discount_tmp = 0;
            if (discount_lines) {
                var i = 0;
                while (i < discount_lines.length) {
                    var discount_line = discount_lines[i];
                    if (total_order >= discount_line.minimum_amount && total_order >= discount_tmp) {
                        discount_line_tmp = discount_line;
                        discount_tmp = discount_line.minimum_amount
                    }
                    i++;
                }
            }
            return discount_line_tmp;
        },
        compute_discount_total_order: function (promotion) {
            var discount_line_tmp = this.checking_apply_total_order(promotion)
            var total_order = this.get_total_without_promotion_and_tax();
            if (discount_line_tmp) {
                var product = this.pos.db.get_product_by_id(promotion.product_id[0]);
                if (product) {
                    this.add_product(product, {
                        price: -total_order / 100 * discount_line_tmp.discount
                    })
                    var selected_line = this.get_selected_orderline();
                    selected_line.promotion_discount_total_order = true;
                    selected_line.promotion = true;
                    selected_line.promotion_reason = 'discount ' + discount_line_tmp.discount + ' % ' + ' when total order greater or equal ' + discount_line_tmp.minimum_amount;
                    selected_line.trigger('change', selected_line);
                }
            }
        },
        compute_discount_category: function (promotion) {
            var product = this.pos.db.get_product_by_id(promotion.product_id[0]);
            if (!product || !this.pos.promotion_by_category_id) {
                return;
            }
            var lines = this.orderlines.models;
            if (lines.length) {
                var x = 0;
                while (x < lines.length) {
                    if (lines[x].promotion_discount_category) {
                        this.remove_orderline(lines[x]);
                    }
                    x++;
                }
            }
            for (i in this.pos.promotion_by_category_id) {
                var promotion_line = this.pos.promotion_by_category_id[i];
                var amount_total_by_category = 0;
                var z = 0;
                while (z < lines.length) {
                    if (!lines[z].product.pos_categ_id) {
                        z++;
                        continue;
                    }
                    if (lines[z].product.pos_categ_id[0] == promotion_line.category_id[0]) {
                        amount_total_by_category += lines[z].get_price_without_tax();
                    }
                    z++;
                }
                if (amount_total_by_category > 0) {
                    this.add_product(product, {
                        price: -amount_total_by_category / 100 * promotion_line.discount
                    })
                    var selected_line = this.get_selected_orderline();
                    selected_line.promotion_discount_category = true;
                    selected_line.promotion = true;
                    selected_line.promotion_reason = ' discount ' + promotion_line.discount + ' % ' + promotion_line.category_id[1];
                    selected_line.trigger('change', selected_line);
                }
            }
        },
        compute_discount_by_quantity_of_products: function (promotion) {
            var quantity_by_product_id = {}
            var product = this.pos.db.get_product_by_id(promotion.product_id[0]);
            var i = 0;
            var lines = this.orderlines.models;
            var lines_remove = [];
            while (i < lines.length) {
                var line = lines[i];
                if (line.promotion_discount_by_quantity && line.promotion_discount_by_quantity == true) {
                    lines_remove.push(line)
                }
                if (line.promotion) {
                    i++;
                    continue
                }
                if (!quantity_by_product_id[line.product.id]) {
                    quantity_by_product_id[line.product.id] = line.quantity;
                } else {
                    quantity_by_product_id[line.product.id] += line.quantity;
                }
                i++;
            }
            this.remove_promotion_lines(lines_remove);
            for (i in quantity_by_product_id) {
                var product_id = i;
                var promotion_lines = this.pos.promotion_quantity_by_product_id[product_id];
                if (!promotion_lines) {
                    continue;
                }
                var quantity_tmp = 0;
                var promotion_line = null;
                var j = 0
                for (j in promotion_lines) {
                    if (quantity_tmp <= promotion_lines[j].quantity && quantity_by_product_id[i] >= promotion_lines[j].quantity) {
                        promotion_line = promotion_lines[j];
                        quantity_tmp = promotion_lines[j].quantity
                    }
                }
                var lines = this.orderlines.models;
                var amount_total_by_product = 0;
                if (lines.length) {
                    var x = 0;
                    while (x < lines.length) {
                        if (lines[x].promotion) {
                            x++;
                            continue
                        }
                        if (lines[x].promotion_discount_by_quantity) {
                            this.remove_orderline(lines[x]);
                        }
                        if (lines[x].product.id == product_id && lines[x].promotion != true) {
                            amount_total_by_product += lines[x].get_price_without_tax()
                        }
                        x++;
                    }
                }
                if (amount_total_by_product > 0 && promotion_line) {
                    this.add_product(product, {
                        price: -amount_total_by_product / 100 * promotion_line.discount
                    })
                    var selected_line = this.get_selected_orderline();
                    selected_line.promotion_discount_by_quantity = true;
                    selected_line.promotion = true;
                    selected_line.promotion_reason = ' discount ' + promotion_line.discount + ' % when ' + promotion_line.product_id[1] + ' have quantity greater or equal ' + promotion_line.quantity + ' ' + selected_line.product.uom_id[1] + ' ';
                    selected_line.trigger('change', selected_line);
                }
            }
        },
        compute_pack_discount: function (promotion) {
            var promotion_condition_items = this.pos.promotion_discount_condition_by_promotion_id[promotion.id];
            var product = this.pos.db.get_product_by_id(promotion.product_id[0]);
            var check = this.checking_can_apply_promotion(promotion_condition_items);
            var lines = this.orderlines.models;
            var lines_remove = [];
            var i = 0;
            while (i < lines.length) {
                var line = lines[i];
                if (line.promotion_discount && line.promotion_discount == true) {
                    lines_remove.push(line)
                }
                i++;
            }
            this.remove_promotion_lines(lines_remove);
            if (check == true) {
                var discount_items = this.pos.promotion_discount_apply_by_promotion_id[promotion.id]
                if (!discount_items) {
                    return;
                }
                var i = 0;
                while (i < discount_items.length) {
                    var discount_item = discount_items[i];
                    var discount = 0;
                    var lines = this.orderlines.models;
                    for (x = 0; x < lines.length; x++) {
                        if (lines[x].promotion) {
                            continue;
                        }
                        if (lines[x].product.id == discount_item.product_id[0]) {
                            discount += lines[x].get_price_without_tax()
                        }
                    }
                    if (product) {
                        this.add_product(product, {
                            price: -discount / 100 * discount_item.discount
                        })
                        var selected_line = this.get_selected_orderline();
                        selected_line.promotion_discount = true;
                        selected_line.promotion = true;
                        selected_line.promotion_reason = 'discount ' + discount_item.product_id[1] + ' ' + discount_item.discount + ' % of Pack name: ' + promotion.name;
                        selected_line.trigger('change', selected_line);
                    }
                    i++;
                }
            }
        },
        compute_pack_free_gift: function (promotion) {
            var promotion_condition_items = this.pos.promotion_gift_condition_by_promotion_id[promotion.id];
            var check = this.checking_can_apply_promotion(promotion_condition_items);
            var lines = this.orderlines.models;
            var lines_remove = [];
            var i = 0;
            while (i < lines.length) {
                var line = lines[i];
                if (line.promotion_gift && line.promotion_gift == true) {
                    lines_remove.push(line)
                }
                i++;
            }
            this.remove_promotion_lines(lines_remove);
            if (check == true) {
                var gifts = this.pos.promotion_gift_free_by_promotion_id[promotion.id]
                if (!gifts) {
                    return;
                }
                var i = 0;
                while (i < gifts.length) {
                    var product = this.pos.db.get_product_by_id(gifts[i].product_id[0]);
                    if (product) {
                        this.add_product(product, {
                            price: 0, quantity: gifts[i].quantity_free
                        })
                        var selected_line = this.get_selected_orderline();
                        selected_line.promotion_gift = true;
                        selected_line.promotion = true;
                        selected_line.promotion_reason = ' gift of Pack name: ' + promotion.name;
                        selected_line.trigger('change', selected_line);
                    }
                    i++;
                }
            }
        },
        compute_price_filter_quantity: function (promotion) {
            var promotion_prices = this.pos.promotion_price_by_promotion_id[promotion.id]
            var product = this.pos.db.get_product_by_id(promotion.product_id[0]);
            var i = 0;
            var lines = this.orderlines.models;
            var lines_remove = [];
            while (i < lines.length) {
                var line = lines[i];
                if (line.promotion_price_by_quantity && line.promotion_price_by_quantity == true) {
                    lines_remove.push(line)
                }
                i++;
            }
            this.remove_promotion_lines(lines_remove);
            if (promotion_prices) {
                var prices_item_by_product_id = {};
                for (var i = 0; i < promotion_prices.length; i++) {
                    var item = promotion_prices[i];
                    if (!prices_item_by_product_id[item.product_id[0]]) {
                        prices_item_by_product_id[item.product_id[0]] = [item]
                    } else {
                        prices_item_by_product_id[item.product_id[0]].push(item)
                    }
                }
                var quantity_by_product_id = this.get_product_and_quantity_current_order()
                var discount = 0;
                for (i in quantity_by_product_id) {
                    if (prices_item_by_product_id[i]) {
                        var quantity_tmp = 0
                        var price_item_tmp = null
                        // root: quantity line, we'll compare this with 2 variable quantity line greater minimum quantity of item and greater quantity temp
                        for (var j = 0; j < prices_item_by_product_id[i].length; j++) {
                            var price_item = prices_item_by_product_id[i][j];
                            if (quantity_by_product_id[i] >= price_item.minimum_quantity && quantity_by_product_id[i] >= quantity_tmp) {
                                quantity_tmp = price_item.minimum_quantity;
                                price_item_tmp = price_item;
                            }
                        }
                        if (price_item_tmp) {
                            var discount = 0;
                            var z = 0;
                            while (z < lines.length) {
                                var line = lines[z];
                                if (line.product.id == price_item_tmp.product_id[0]) {
                                    discount += line.get_price_without_tax() - (line.quantity * price_item_tmp.list_price)
                                }
                                z++;
                            }
                            if (discount > 0) {
                                this.add_product(product, {
                                    price: -discount
                                })
                                var selected_line = this.get_selected_orderline();
                                selected_line.promotion_price_by_quantity = true;
                                selected_line.promotion = true;
                                selected_line.promotion_reason = ' By greater or equal ' + price_item_tmp.minimum_quantity + ' ' + selected_line.product.uom_id[1] + ' ' + price_item_tmp.product_id[1] + ' applied price ' + price_item_tmp.list_price
                                selected_line.trigger('change', selected_line);
                            }
                        }
                    }
                }

            }
        },
    })
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        init_from_JSON: function (json) {
            if (json.promotion) {
                this.promotion = json.promotion;
            }
            if (json.promotion_reason) {
                this.promotion_reason = json.promotion_reason;
            }
            if (json.promotion_discount_total_order) {
                this.promotion_discount_total_order = json.promotion_discount_total_order;
            }
            if (json.promotion_discount_category) {
                this.promotion_discount_category = json.promotion_discount_category;
            }
            if (json.promotion_discount_by_quantity) {
                this.promotion_discount_by_quantity = json.promotion_discount_by_quantity;
            }
            if (json.promotion_gift) {
                this.promotion_gift = json.promotion_gift;
            }
            if (json.promotion_discount) {
                this.promotion_discount = json.promotion_discount;
            }
            if (json.promotion_price_by_quantity) {
                this.promotion_price_by_quantity = json.promotion_price_by_quantity;
            }
            return _super_orderline.init_from_JSON.apply(this, arguments);
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            if (this.promotion) {
                json.promotion = this.promotion;
            }
            if (this.promotion_reason) {
                json.promotion_reason = this.promotion_reason;
            }
            if (this.promotion_discount_total_order) {
                json.promotion_discount_total_order = this.promotion_discount_total_order;
            }
            if (this.promotion_discount_category) {
                json.promotion_discount_category = this.promotion_discount_category;
            }
            if (this.promotion_discount_by_quantity) {
                json.promotion_discount_by_quantity = this.promotion_discount_by_quantity;
            }
            if (this.promotion_gift) {
                json.promotion_gift = this.promotion_gift;
            }
            if (this.promotion_discount) {
                json.promotion_discount = this.promotion_discount;
            }
            if (this.promotion_price_by_quantity) {
                json.promotion_price_by_quantity = this.promotion_price_by_quantity;
            }
            return json;
        },
        export_for_printing: function () {
            var res = _super_orderline.export_for_printing.call(this);
            if (this.promotion) {
                res.promotion = this.promotion;
                res.promotion_reason = this.promotion_reason;
            }
            return res
        },
        can_be_merged_with: function (orderline) {
            _super_orderline.can_be_merged_with.apply(this, arguments);
            if (this.promotion) {
                return false;
            }
        },
    });

    //------- *** Screen of promotions *** ---------------//
    var promotion_popup = PopupWidget.extend({
        template: 'promotion_popup',
        init: function (parent, options) {
            this._super(parent, options);
            this.promotions = this.pos.promotions;
        },
        renderElement: function () {
            var promotions_cache = this.pos.promotions;
            var promotions_show = [];
            var i = 0
            var order = this.pos.get_order();
            if (promotions_cache.length && order) {
                while (i < promotions_cache.length) {
                    var promotion = promotions_cache[i];
                    var type = promotion.type
                    if (type == '1_discount_total_order') {
                        var check = order.checking_apply_total_order(promotion);
                        if (check) {
                            promotions_show.push(promotion);
                        }
                    }
                    if (type == '2_discount_category') {
                        if (this.pos.promotion_by_category_id) {
                            promotions_show.push(promotion);
                        }
                    }
                    if (type == '3_discount_by_quantity_of_product' || type == '6_price_filter_quantity') {
                        promotions_show.push(promotion);
                    }
                    if (type == '4_pack_discount') {
                        var promotion_condition_items = order.pos.promotion_discount_condition_by_promotion_id[promotion.id];
                        var check = order.checking_can_apply_promotion(promotion_condition_items);
                        if (check == true) {
                            promotions_show.push(promotion);
                        }
                    }
                    if (type == '5_pack_free_gift') {
                        var promotion_condition_items = order.pos.promotion_gift_condition_by_promotion_id[promotion.id];
                        var check = order.checking_can_apply_promotion(promotion_condition_items);
                        if (check == true) {
                            promotions_show.push(promotion);
                        }

                    }
                    i++
                }
            }

            this.promotions = promotions_show;
            this._super();
            var self = this;
            $('.promotion-line').click(function () {
                var promotion_id = parseInt($(this).data()['id']);
                var promotion = self.pos.promotion_by_id[promotion_id];
                var type = promotion.type;
                var order = self.pos.get('selectedOrder');
                if (order.orderlines.length) {
                    if (type == '1_discount_total_order') {
                        order.compute_discount_total_order(promotion);
                    }
                    if (type == '2_discount_category') {
                        order.compute_discount_category(promotion);
                    }
                    if (type == '3_discount_by_quantity_of_product') {
                        order.compute_discount_by_quantity_of_products(promotion);
                    }
                    if (type == '4_pack_discount') {
                        order.compute_pack_discount(promotion);
                    }
                    if (type == '5_pack_free_gift') {
                        order.compute_pack_free_gift(promotion);
                    }
                    if (type == '6_price_filter_quantity') {
                        order.compute_price_filter_quantity(promotion);
                    }
                }
            })
            $('.remove_promotion').click(function () {
                var order = self.pos.get('selectedOrder');
                var lines = order.orderlines.models;
                var lines_remove = [];
                var i = 0;
                while (i < lines.length) {
                    var line = lines[i];
                    if (line.promotion && line.promotion == true) {
                        lines_remove.push(line)
                    }
                    i++;
                }
                order.remove_promotion_lines(lines_remove)
                order.trigger('change', order);
            })
        }
    })
    gui.define_popup({
        name: 'promotion_popup',
        widget: promotion_popup
    });

    var promotion_button = screens.ActionButtonWidget.extend({
        template: 'promotion_button',
        button_click: function () {
            var order = this.pos.get('selectedOrder');
            if (order && order.orderlines.length) {
                this.gui.show_popup('promotion_popup', {});
                this.pos.auto_promotion = false;
                $('.auto-promotion').removeClass('highlight');
            }

        },
    });

    screens.define_action_button({
        'name': 'promotion_button',
        'widget': promotion_button,
        'condition': function () {
            return this.pos.config.promotion_ids.length && this.pos.config.allow_promotion == true;
        },
    });

    var auto_promotion_button = screens.ActionButtonWidget.extend({
        template: 'auto_promotion_button',
        button_click: function () {
            var auto = this.pos.auto_promotion;
            if (auto == false || !auto) {
                $('.auto-promotion').addClass('highlight');
                this.pos.auto_promotion = true;
            } else {
                $('.auto-promotion').removeClass('highlight');
                this.pos.auto_promotion = false;
            }

        },
    });

    screens.define_action_button({
        'name': 'auto_promotion_button',
        'widget': auto_promotion_button,
        'condition': function () {
            return this.pos.config.promotion_ids.length && this.pos.config.allow_promotion == true;
        },
    });

    screens.OrderWidget.include({
        update_summary: function () {
            this._super();
            var order = this.pos.get('selectedOrder');
            var lines = order.orderlines.models;
            var promotion_amount = 0;
            for (var i = 0; i < lines.length; i++) {
                var line = lines[i]
                if (line.promotion) {
                    promotion_amount += line.get_price_without_tax()
                }
            }
            if (order && this.el.querySelector('.promotion_amount')) {
                this.el.querySelector('.promotion_amount').textContent = round_pr(promotion_amount, this.pos.currency.rounding);
                order.promotion_amount = round_pr(promotion_amount, this.pos.currency.rounding);
            }
        },
        rerender_orderline: function (order_line) {
            try {
                this._super(order_line);
            } catch (e) {
                console.error(e);
            }
        }
    })

    screens.ActionpadWidget.include({
        renderElement: function () {
            var self = this;
            this._super();
            this.$('.pay').click(function () {
                self.pos.auto_promotion = false;
                $('.auto-promotion').removeClass('highlight');
            })
        }
    })

});
