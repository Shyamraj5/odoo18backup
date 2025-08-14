/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";

patch(PartnerList.prototype, {
    async getNewPartners() {
        let domain = [];
        const limit = 30;

        if (this.state.query) {
            const search_fields = [
                "name",
                "parent_name",
                ...this.getPhoneSearchTerms(),
                "email",
                "barcode",
                "street",
                "zip",
                "city",
                "state_id",
                "country_id",
                "vat",
            ];

            const baseDomain = [
                ...Array(search_fields.length - 1).fill("|"),
                ...search_fields.map((field) => [field, "ilike", this.state.query + "%"]),
            ];

            // Final domain: only active customers, allow user's own partner
            domain = [
                "&",
                ["customer_rank", ">", 0],
                ["active", "=", true],
                ...baseDomain,
            ];
        }

        const result = await this.pos.data.searchRead("res.partner", domain, [], {
            limit: limit,
            offset: this.state.currentOffset,
        });

        return result;
    },
});