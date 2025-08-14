/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
const { DateTime } = luxon;
import { rpc } from "@web/core/network/rpc";


export class CustomJsVatReportView extends Component {
    setup() {
        this.ormService = useService("orm");
        this.action = useService("action");
        const savedDateFrom = localStorage.getItem("vat_report_temp_date_from");
        const savedDateTo = localStorage.getItem("vat_report_temp_date_to");
        this.state = useState({
            reportLines: [],
            date_from: savedDateFrom ? DateTime.fromISO(savedDateFrom) : DateTime.now().startOf("month"),
            date_to: savedDateTo ? DateTime.fromISO(savedDateTo) : DateTime.now().endOf("month"),
        });

        onMounted(() => {
            this.apply_filters();
        })

        this.apply_filters = async () => {
            const selectedStartDate = this.state.date_from ? this.state.date_from.toISODate() : null;
            const selectedEndDate = this.state.date_to ? this.state.date_to.toISODate() : null;
            localStorage.setItem("vat_report_temp_date_from", selectedStartDate);
            localStorage.setItem("vat_report_temp_date_to", selectedEndDate);
            try {
                let report_lines = await rpc('/codeox_vat_report/vat_report_data', {
                    start_date: selectedStartDate,
                    end_date: selectedEndDate
                });
                this.state.reportLines = report_lines.vat_line||[]
                this.state.domainFilters = report_lines.domain||{}
            } catch (error) {
                console.error("Error fetching report lines:", error)
            }
    
        }
        
    }

    fromPlaceholder = _t("Date from");
    toPlaceholder = _t("Date to");

    async onDateFromChanged(dateFrom) {
        this.state.date_from = dateFrom;
    }

    async onDateToChanged(dateTo) {
        this.state.date_to = dateTo;
    }

    saveDatesToLocalStorage() {
        localStorage.setItem("vat_report_temp_date_from", this.state.date_from.toISODate());
        localStorage.setItem("vat_report_temp_date_to", this.state.date_to.toISODate());
    }

    viewSalesBaseAction() {
        this.saveDatesToLocalStorage()
        return this.action.doAction({
            name: _t("Journal Items"),
            type: "ir.actions.act_window",
            res_model: "account.move.line",
            domain: this.state.domainFilters.sales_untaxed_domain,
            views: [[false, "list"],[false, "form"]],
            view_mode: "list,form",
            target: "current",
        })

    }

    viewSalesTaxAction() {
        this.saveDatesToLocalStorage()
        return this.action.doAction({
            name: _t("Journal Items"),
            type: "ir.actions.act_window",
            res_model: "account.move.line",
            domain: this.state.domainFilters.sales_taxed_domain,
            views: [[false, "list"],[false, "form"]],
            view_mode: "list,form",
            target: "current",
        })
    }

    viewExpensesBaseAction() {
        this.saveDatesToLocalStorage()
        return this.action.doAction({
            name: _t("Journal Items"),
            type: "ir.actions.act_window",
            res_model: "account.move.line",
            domain: this.state.domainFilters.purchases_base_domain,
            views: [[false, "list"],[false, "form"]],
            view_mode: "list,form",
            target: "current",
        })
    }

    viewExpensesTaxAction() {
        this.saveDatesToLocalStorage()
        return this.action.doAction({
            name: _t("Journal Items"),
            type: "ir.actions.act_window",
            res_model: "account.move.line",
            domain: this.state.domainFilters.purchases_tax_domain,
            views: [[false, "list"],[false, "form"]],
            view_mode: "list,form",
            target: "current",
        })
    }

}

CustomJsVatReportView.template = "codeox_vat_report.CustomJsVatReportView";
CustomJsVatReportView.components = { DateTimeInput };
registry.category("actions").add("codeox_vat_report.custom_js_vat_report_view", CustomJsVatReportView)
