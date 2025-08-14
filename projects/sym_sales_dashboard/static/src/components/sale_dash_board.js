/** @odoo-module */

import { registry } from "@web/core/registry"
import { KpiCard } from "./kpi_card/kpi_card"
import { ChartRenderer } from "./chart_renderer/char_renderer"
import { loadJS } from "@web/core/assets"
import { useService } from "@web/core/utils/hooks"
// import Chart from 'chart.js/auto'
const { Component, onWillStart, useRef, onMounted, useState } = owl

export class SaleDashBoard extends Component {
    setup() {
        this.orm = useService("orm")
        this.state = useState({
            quotations: {
                value: 10,
                percentage: 20,
            },
            period: 90
        })
        onWillStart(async () => {
            this.get_quotations();
        })


    }
    async get_quotations() {
        const quotations = await this.orm.searchCount("sale.order", [['state', 'in', ['draft', 'sent']]])
        this.state.quotations.value = quotations;

    }

    OnchangePeriod(){
        // Logic to handle period change
        console.log(this.state.period);
    }

}

SaleDashBoard.template = "sym_sales_dashboard.OwlDash"
SaleDashBoard.components = {
    KpiCard, ChartRenderer
}
registry.category("actions").add("owl.action_ad_dashboard", SaleDashBoard)