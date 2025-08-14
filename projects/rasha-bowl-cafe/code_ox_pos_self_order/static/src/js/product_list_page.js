/** @odoo-module **/
import { ProductListPage } from "@pos_self_order/app/pages/product_list_page/product_list_page"
import { patch } from "@web/core/utils/patch";
import { useState, onMounted } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

patch(ProductListPage.prototype, {
    setup() {
        super.setup(...arguments);
        this.selfOrder.showProductCategories = true;
        this.selfOrder.showProducts = false;
        this.state = useState({
            showProducts: false,
            showProductCategories: true,
            company: {'name': '', 'logo': '', 'id': ''},
        });
        this.toggleVisibility = this.toggleVisibility.bind(this);

        onMounted(async () => {
            await this.getCompnayData()
        })
    },

    toggleVisibility(currentCategoryId){
        this.selfOrder.showProductCategories = false;
        this.selfOrder.showProducts = true;
        this.state.currentProductCategory = this.selfOrder.productCategories.filter(category => 
            category.id === currentCategoryId
        );
    },

    showProductCategories(){
        this.selfOrder.showProductCategories = true;
        this.selfOrder.showProducts = false;
        
    },

    async getCompnayData(){
        const result = await rpc("/public/company_data");
        if (result.length > 0) {
            this.state.company.name = result[0].name;
            this.state.company.id = result[0].id;
        }
    }   

});
